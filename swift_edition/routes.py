import tornado.web
from tornado_cors import CorsMixin
from tornado import gen, queues
from tornado.log import gen_log, access_log
import re
import json
import traceback
from lxml import etree
from swift_collate.collate import CollationJSONEncoder, DifferenceTextJSONEncoder
from swift_collate.text import Text, TextJSONEncoder
from swift_collate.tokenize import SwiftSentenceTokenizer
from swift_edition.tei import TeiParser
from swift_edition.async import collate_async
from utils import TokenizerFactory, TaggerFactory

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class PoemAutocompleteHandler(CorsMixin, tornado.web.RequestHandler):
    CORS_ORIGIN = '*'

    """The request handler for autocompletion

    """
    def initialize(self, nota_bene_encoder):
        self.nota_bene_encoder = nota_bene_encoder

    def get(self):
        query = self.get_argument("q", "")
        poems = self.nota_bene_encoder.poems()

        items = map(lambda poem: poem['id'], filter(lambda poem: re.search('^' + query, poem['id']), poems))

        self.write(tornado.escape.json_encode({'items': items }))

class TranscriptSearchHandler(tornado.web.RequestHandler):
    CORS_ORIGIN = '*'

    """The request handler for searching for transcripts

    """

    def get(self, poem_id):
        query = self.get_argument("q", "")
        poems = transcript_ids(poem_id)

        items = filter(lambda poem: re.search('^' + query, poem), poems)

        self.write(tornado.escape.json_encode({'items': items }))


class TeiHandler(CorsMixin, tornado.web.RequestHandler):
    CORS_ORIGIN = '*'

    def initialize(self, nota_bene_encoder):
        self.nota_bene_encoder = nota_bene_encoder

    def get(self, transcript_id):
        tei_xml = self.nota_bene_encoder.transcript(None, transcript_id)
        self.write(tei_xml)


class PoemsHandler(CorsMixin, tornado.web.RequestHandler):
    """The request handler for viewing poem variants

    """

    CORS_ORIGIN = '*'

    def initialize(self, nota_bene_encoder):
        self.nota_bene_encoder = nota_bene_encoder

    @gen.coroutine
    def get(self, poem_id):
        """The GET request handler for poems
        
        Args:
           poem_id (string):   The identifier for the poem set

        """

        poem_texts = []

        # Retrieve the stanzas
        ids, poem_docs = self.nota_bene_encoder.poem(poem_id)

        witnesses = []
        for node, witness_id in zip(poem_docs, ids):
            if node is not None:
                witness_values = { 'node': node, 'id': witness_id }
                witnesses.append( witness_values )

        # Construct the poem objects
        poem_texts.extend(map(lambda poem_text: Text(poem_text['node'], poem_text['id'], SwiftSentenceTokenizer), witnesses))

        #if self.request.headers.get('Accept') == 'application/json':
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(poem_texts, cls=TextJSONEncoder))

class BaseCollateHandler(object):

    def load(self):

        # Parse the documents
        self.variant_texts = []
        message = 'ok'

        base_transcript = nota_bene_encoder.transcript('001A', self.base_id)

        # Work-around for lxml2
        # <?xml version="1.0" encoding="utf-8"?>
        base_transcript = base_transcript.replace('<?xml version="1.0" encoding="utf-8"?>', '')

        base_docs = map(TeiParser.parse, [base_transcript])
        self.base_doc = base_docs.pop()

        if self.base_doc is None:
            raise Exception("Failed to retrieve the TEI-XML Document for " + self.base_id)

        # Structure the base and witness values
        base_values = { 'node': self.base_doc, 'id': self.base_id }

        docs = []
        for transcript_id in self.transcript_ids:

            transcript = nota_bene_encoder.transcript('001A', transcript_id)
            transcript = transcript.replace('<?xml version="1.0" encoding="utf-8"?>', '')

            docs.append(TeiParser.parse(transcript))

        for node, witness_id in zip(docs, self.transcript_ids):
            # Ensure that Nodes which could not be parsed are logged as server errors
            # Resolves SPP-529
            if node is not None:
                witness_values = { 'node': node, 'id': witness_id, 'message': message }
            else:
                witness_values = { 'node': node, 'id': witness_id, 'message': 'Failed to parse the XML for the transcript ' + witness_id }
                logging.warn("Failed to parse the XML for the transcript %s", witness_id)

            self.variant_texts.append( witness_values )

        try:
            pass
        except Exception as loadEx:
            pass

        # Update the response body

        # self.response_body = map(lambda item: { 'node': etree.tostring(item['node']), 'id': item['id'], 'message': item['message'] }, self.variant_texts)
        variants = []

        for item in self.variant_texts:
            if 'node' in item and item['node'] is not None:
                variants.append({ 'node': etree.tostring(item['node']), 'id': item['id'], 'message': item['message'] })

        # self.variants = variants
        self.response_body = variants

    def tokenize(self):

        # Retrieve the base Text
        self.base_text = Text(self.base_doc, self.base_id, self.tokenizer, self.tagger)
        self.base_text.tokenize()

        # Retrieve the variant Texts
        # self.witness_texts = map(lambda witness: Text(witness['node'], witness['id'], self.tokenizer, self.tagger), self.variants)

        # Filter for errors in the parsing of the XML Documents
        self.witness_texts = []
        for witness in self.variant_texts:
            if 'node' in witness and witness['node'] is not None:
                self.witness_texts.append( Text(witness['node'], witness['id'], self.tokenizer, self.tagger) )

        # Update the response body
        self.response_body = map(lambda witness_text: TextJSONEncoder().encode(witness_text), self.witness_texts)

    def collate(self):
        try:
            collation = collate_async(self.executor, self.base_text, self.witness_texts, self.poem_id, self.base_id, None, None, False)

            results = DifferenceTextJSONEncoder().encode(collation)

            self.response_body = results
        except Exception as collateEx:
            raise Exception("Could not collate: " + str(collateEx) + traceback.format_exc())

class CollateHandler(CorsMixin, tornado.web.RequestHandler, BaseCollateHandler):
    CORS_ORIGIN = '*'
    CORS_HEADERS = 'Content-Type'

    def post(self):

        if self.request.headers.get('Accept') == 'application/json':
            self.json_args = json.loads(self.request.body)

            self.poem_id = self.json_args.get('poemId', None)
            base_text = self.json_args.get('baseText', None)
            self.transcript_ids = self.json_args.get('variantTexts', [])
            mode = self.json_args.get('mode', 'notaBene')
            tokenizer_class_name = self.json_args.get('tokenizer', 'SwiftSentenceTokenizer')
            tagger_class_name = self.json_args.get('tagger', 'disabled')

            tokenizer_factory = TokenizerFactory(tokenizer_class_name)
            self.tokenizer = tokenizer_factory.klass

            # Retrieve the POS tagger
            tagger_factory = TaggerFactory(tagger_class_name)
            self.tagger = tagger_factory.tagger
            
            # Load the documents
            self.base_id = base_text

            self.load()
            self.tokenize()
            self.collate()

            self.set_header('Content-Type', 'application/json')
            self.write(self.response_body)
        else:
            self.write({'status': 'error'})

class CollateSocketHandler(tornado.websocket.WebSocketHandler, BaseCollateHandler):

    def initialize(self, clients, nota_bene_encoder):
        self.clients = clients
        self.nota_bene_encoder= nota_bene_encoder
        self.messages = []

    def log(self, message):
        self.messages.append(message)
        self.write_message(json.dumps({'status': "\n".join(self.messages)}))

    def load(self):
        # Parse the documents
        self.variant_texts = []
        message = 'ok'

        base_transcript = self.nota_bene_encoder.transcript(None, self.base_id)

        # Work-around for lxml2
        base_transcript = base_transcript.replace('<?xml version="1.0" encoding="utf-8"?>', '')

        base_docs = map(TeiParser.parse, [base_transcript])
        self.base_doc = base_docs.pop()

        if self.base_doc is None:
            self.log("Failed to retrieve the TEI-XML Document for the base text " + self.base_id)
        else:
            self.log("Retrieved the TEI-XML Document for the base text " + self.base_id)

        # Structure the base and witness values
        base_values = { 'node': self.base_doc, 'id': self.base_id }

        docs = []

        for transcript_id in self.transcript_ids:

            transcript = self.nota_bene_encoder.transcript(None, transcript_id)
            if transcript is not None:
                transcript = transcript.replace('<?xml version="1.0" encoding="utf-8"?>', '')
                try:
                    docs.append(TeiParser.parse(transcript))
                    self.log("Retrieved the TEI-XML Document for the variant text " + transcript_id)
                except:
                    self.log("Failed to retrieve the TEI-XML Document for the variant text " + transcript_id)
            else:
                self.log("Failed to retrieve the TEI-XML Document for the variant text " + transcript_id)

        for node, witness_id in zip(docs, self.transcript_ids):
            # Ensure that Nodes which could not be parsed are logged as server errors
            # Resolves SPP-529
            if node is not None:
                witness_values = { 'node': node, 'id': witness_id, 'message': message }
            else:
                witness_values = { 'node': node, 'id': witness_id, 'message': 'Failed to parse the XML for the transcript ' + witness_id }
                self.log("Failed to parse the XML for the transcript %s", witness_id)

            self.variant_texts.append( witness_values )

        variants = []
        for item in self.variant_texts:
            if 'node' in item and item['node'] is not None:
                variants.append({ 'node': etree.tostring(item['node']), 'id': item['id'], 'message': item['message'] })

        self.response_body = variants

    def tokenize(self):

        # Retrieve the base Text
        self.base_text = Text(self.base_doc, self.base_id, self.tokenizer, self.tagger)
        self.base_text.tokenize()

        # Retrieve the variant Texts
        # self.witness_texts = map(lambda witness: Text(witness['node'], witness['id'], self.tokenizer, self.tagger), self.variants)

        # Filter for errors in the parsing of the XML Documents
        self.witness_texts = []
        for witness in self.variant_texts:
            if 'node' in witness and witness['node'] is not None:
                self.witness_texts.append( Text(witness['node'], witness['id'], self.tokenizer, self.tagger) )
                self.log("Tokenizing the TEI-XML Document for the variant text " + witness['id'])

        # Update the response body
        self.response_body = map(lambda witness_text: TextJSONEncoder().encode(witness_text), self.witness_texts)

    def collate(self):
        try:
            collation = collate_async(self.executor, self.base_text, self.witness_texts, self.poem_id, self.base_id, self.log, True)
            results = DifferenceTextJSONEncoder().encode(collation)

            self.response_body = results
            self.log("Collation completed")

#        except AlignmentException as alignEx:
#            self.log("Failed to align: " + alignEx)

        except Exception as ex:
            # raise CollationException(str(ex) + traceback.format_exc())
            raise Exception(str(ex) + traceback.format_exc())
            self.log("Failed to collate: " + str(ex) + traceback.format_exc())

    @tornado.web.asynchronous
    def get(self, *args, **kwargs):
        self.open_args = args
        self.open_kwargs = kwargs

        # Upgrade header should be present and should be equal to WebSocket
        if self.request.headers.get("Upgrade", "").lower() != 'websocket':
            self.set_status(400)
            log_msg = "Can \"Upgrade\" only to \"WebSocket\"."
            self.finish(log_msg)
            gen_log.debug(log_msg)
            return

        # Connection header should be upgrade.
        # Some proxy servers/load balancers
        # might mess with it.
        headers = self.request.headers
        connection = map(lambda s: s.strip().lower(),
                         headers.get("Connection", "").split(","))
        if 'upgrade' not in connection:
            self.set_status(400)
            log_msg = "\"Connection\" must be \"Upgrade\"."
            self.finish(log_msg)
            gen_log.debug(log_msg)
            return

        # Handle WebSocket Origin naming convention differences
        # The difference between version 8 and 13 is that in 8 the
        # client sends a "Sec-Websocket-Origin" header and in 13 it's
        # simply "Origin".
        if "Origin" in self.request.headers:
            origin = self.request.headers.get("Origin")
        else:
            origin = self.request.headers.get("Sec-Websocket-Origin", None)

        # If there was an origin header, check to make sure it matches
        # according to check_origin. When the origin is None, we assume it
        # did not come from a browser and that it can be passed on.
#        if origin is not None and not self.check_origin(origin):
#            self.set_status(403)
#            log_msg = "Cross origin websockets not allowed"
#            self.finish(log_msg)
#            gen_log.debug(log_msg)
#            return

        self.stream = self.request.connection.detach()
        self.stream.set_close_callback(self.on_connection_close)

        self.ws_connection = self.get_websocket_protocol()
        if self.ws_connection:
            self.ws_connection.accept_connection()
        else:
            if not self.stream.closed():
                self.stream.write(tornado.escape.utf8(
                    "HTTP/1.1 426 Upgrade Required\r\n"
                    "Sec-WebSocket-Version: 7, 8, 13\r\n\r\n"))
                self.stream.close()

    def open(self):
        access_log.info("Collation client connected")
        self.write_message(json.dumps({'status': "Collation engine ready"}))
        if self not in self.clients:
            self.clients.append(self)

    def on_message(self, message):
        if message == '9':
            access_log.info("Collation client pinged")
            return

        self.messages = []

        # Parse the arguments from the message
        self.json_args = json.loads(message)

        self.poem_id = self.json_args.get('poemId', None)

        base_text = self.json_args.get('baseText', None)

        self.transcript_ids = self.json_args.get('variantTexts', {})

        self.mode = self.json_args.get('mode', 'notaBene')
        
        tokenizer_class_name = self.json_args.get('tokenizer', 'SwiftSentenceTokenizer')
        tokenizer_factory = TokenizerFactory(tokenizer_class_name)
        self.tokenizer = tokenizer_factory.klass

        tagger_class_name = self.json_args.get('tagger', 'disabled')

        # Retrieve the POS tagger
        tagger_factory = TaggerFactory(tagger_class_name)
        self.tagger = tagger_factory.tagger
            
        # Load the documents
        self.base_id = base_text
        access_log.info("Collation request for %s using %s as the base text", self.poem_id, self.base_id)

        self.load()
        self.tokenize()
        self.collate()

        self.write_message(json.dumps({'status': "\n".join(self.messages),'collation': self.response_body}))

    def on_close(self):
        if self in self.clients:
            self.clients.remove(self)
        access_log.info("Collation client disconnected")
