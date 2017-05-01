
import tornado.ioloop
import tornado.escape
import tornado.httpserver
import tornado.websocket
from tornado.concurrent import run_on_executor

from tornado import gen, queues
from tornado.options import define, options, parse_command_line
from tornado_cors import CorsMixin

import tornado.web
import tornado.options
from tornado.web import URLSpec as URL
import os
from settings import MAX_WORKERS, nota_bene_encoder, clients
from routes import MainHandler, PoemAutocompleteHandler, TranscriptSearchHandler, CollateSocketHandler, CollateHandler, PoemsHandler, TeiHandler

from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor

CollateSocketHandler.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
CollateHandler.executor = ProcessPoolExecutor(max_workers=MAX_WORKERS)

application = tornado.web.Application(
    [
        URL(r"/", MainHandler, name='index'),
        URL(r"/suggest/poems/?", PoemAutocompleteHandler, kwargs={ 'nota_bene_encoder': nota_bene_encoder }),
        URL(r"/autocomplete/transcripts/([^/]+)/?", TranscriptSearchHandler),
        URL(r"/stream/?", CollateSocketHandler, name='stream', kwargs={ 'clients': clients, 'nota_bene_encoder': nota_bene_encoder }),
        URL(r"/collate/?", CollateHandler),
        URL(r"/poems/([^/]+)/?", PoemsHandler, name='poems', kwargs={ 'nota_bene_encoder': nota_bene_encoder }),
        URL(r"/tei/([^/]+)/?", TeiHandler, name='tei', kwargs={ 'nota_bene_encoder': nota_bene_encoder })
    ],
    template_path=os.path.join(os.path.dirname(__file__), '..', "templates"),
    static_path=os.path.join(os.path.dirname(__file__), '..', "static"),
    xsrf_cookies=False,
    #        debug=tornado.options.options.debug, # See http://stackoverflow.com/questions/22641015/run-multiple-tornado-processess
)

