from invoke import run, task
import ConfigParser, os
from pymongo import MongoClient
from bson.binary import Binary
import fnmatch
import pickle
from SwiftDiff import TextToken
from SwiftDiff.text import Line, Text
from SwiftDiff.collate import DifferenceText, Collation
from SwiftDiff.tokenize import Tokenizer, SwiftSentenceTokenizer

# Retrieve the database
config = ConfigParser.RawConfigParser()
config.read( os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'swift_collate.cfg')  )
    
host = config.get('MongoDB', 'host')
port = config.getint('MongoDB', 'port')
client = MongoClient(host, port)

# Retrieve the server configuration
tei_dir_path = config.get('server', 'tei_dir_path')

import sys, traceback

@task
def validate_manuscript(dir_path, file_path):
    """Validate that an encoded manuscript can be collated

    """

    tei_source_dir_path = os.path.join(os.path.dirname(os.path.abspath(tei_dir_path)), 'sources')
    text_path = os.path.join(tei_source_dir_path, dir_path, file_path + '.tei.xml')
    file_doc = Tokenizer.parse_text(text_path)

    if file_doc is None:
        print "Failed to parse " + text_path
    try:
        Text(file_doc, 'validate', SwiftSentenceTokenizer)
        print "Successfully parsed " + text_path
    except Exception as e:
        print "Failed to encode " + text_path
        print "Error: %s" % str(e)
        print "Trace: %s" % traceback.format_exc()

@task
def validate_source(dir_path):
    """Validate that all encoded manuscripts for a given source can be collated

    """

    tei_source_dir_path = os.path.join(os.path.dirname(os.path.abspath(tei_dir_path)), 'sources')

    # Iterate for each manuscript
    for file_path in os.listdir(os.path.join(os.path.abspath(tei_source_dir_path), dir_path)):

        text_path = os.path.join(tei_source_dir_path, dir_path, file_path)
        file_doc = Tokenizer.parse_text(text_path)

        if file_doc is None:
            print "Failed to parse " + text_path
        try:
            Text(file_doc, 'validate', SwiftSentenceTokenizer)
            # print "Successfully parsed " + text_path
        except Exception as e:
            print "Failed to encode " + text_path
            print "Error: %s" % str(e)
            print "Trace: %s" % traceback.format_exc()

@task
def validate_sources():
    """Validate that all encoded manuscripts for all sources can be collated

    """

    tei_source_dir_path = os.path.join(os.path.dirname(os.path.abspath(tei_dir_path)), 'sources')

    for(path, dirs, files) in os.walk(tei_source_dir_path):
        for dir_path in dirs:
            for file_path in os.listdir(os.path.join(os.path.abspath(tei_source_dir_path), dir_path)):

                text_path = os.path.join(tei_source_dir_path, dir_path, file_path)
                file_doc = Tokenizer.parse_text(text_path)

                if file_doc is None:
                    print "Failed to parse " + text_path                    
                    continue
                try:
                    Text(file_doc, 'validate', SwiftSentenceTokenizer)
                    # print "Successfully parsed " + text_path
                except Exception as e:
                    print "Failed to encode " + text_path
                    print "Error: %s" % str(e)
                    print "Trace: %s" % traceback.format_exc()

def collate(base_text, witness_texts, poem_id, base_id):

    # Collate the witnesses in parallel
    diff_args = map( lambda witness_text: (base_text, witness_text), witness_texts )
    diffs = map( compare, diff_args )

    tei_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'xml', poem_id)
    result = Collation(base_text, diffs, tei_dir_path)

    return result

# @todo Deduplicate
def compare(_args, update=False):
    """Compares two <tei:text> Element trees

    :param _args: The arguments passed (within the context of invocation using a ProcessPoolExecutor instance)
    :type _args: tuple
    """

    base_text = _args[0]
    other_text = _args[1]

    diff = DifferenceText(base_text, other_text, SwiftSentenceTokenizer)
    
    return diff

@task
def seed_cache(poem_id, base_id):

    # Generate the collation
    uris = doc_uris(poem_id)

    # Retrieve the ID's
    ids = map(lambda path: path.split('/')[-1].split('.')[0], uris)
    ids = ids[1:]

    # Generate the values for the collation
    poem_file_paths = {
        poem_id: { 'uris': uris, 'ids': ids },
    }

    uris = poem_file_paths[poem_id]['uris']
    ids = poem_file_paths[poem_id]['ids']

    # Retrieve the stanzas
    texts = map(resolve, uris)

    # Set the base text
    base_text = texts[0]
    texts = texts[1:]

    # Structure the base and witness values
    base_values = { 'node': base_text, 'id': base_id }

    witnesses = []
    for node, witness_id in zip(texts, ids):

        # Ensure that Nodes which could not be parsed are logged as server errors
        # Resolves SPP-529
        if node is not None:
            witness_values = { 'node': node, 'id': witness_id }
            witnesses.append( witness_values )

    # Begin the tokenization
    base_text = Text(base_text, base_id, SwiftSentenceTokenizer)
    base_text.tokenize()

    witness_texts = map(lambda witness: Text(witness['node'], witness['id'], SwiftSentenceTokenizer), witnesses )

    collation = collate(base_text, witness_texts, poem_id, base_id)
    pass
