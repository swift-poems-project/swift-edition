#!/usr/bin/env python

import os.path
import string
import re
import subprocess
import os
import time
import importlib
import ConfigParser
import fnmatch
import pickle
import logging
import signal
import json
import traceback

from lxml import etree

from pymongo import MongoClient
from bson.binary import Binary

import requests
import tornado.ioloop
import tornado.web
from tornado.web import URLSpec as URL
import tornado.escape
import tornado.httpserver
import tornado.websocket
from tornado.concurrent import run_on_executor

from tornado import gen, queues
from tornado.options import define, options, parse_command_line
from tornado_cors import CorsMixin

from swift_collate.collate import DifferenceText, Collation, CollationJSONEncoder, DifferenceTextJSONEncoder
from swift_collate.text import Line, Text, TextJSONEncoder
from swift_collate.tokenize import SwiftSentenceTokenizer

from swift_edition.nota_bene import NotaBeneGDriveStore, NotaBeneEncoder
from swift_edition import application
from settings import DEBUG, MAX_WORKERS, SECRET, MONGO_HOST, MONGO_PORT, MONGO_DB, CLIENT_SECRET_FILE, SCOPES, TEI_SERVICE_URL, MAX_WAIT_SECONDS_BEFORE_SHUTDOWN

# Set the global variables for the server
define("port", default=8888, help="run on the given port", type=int)
define("debug", default=DEBUG, help="run in debug mode", type=bool)
define("processes", default=MAX_WORKERS, help="concurrency", type=int)
define("secret", default=SECRET, help="secret for cookies")
define("cache", default=True, help="caching", type=bool)

client = MongoClient(MONGO_HOST, MONGO_PORT)
# pool = ProcessPoolExecutor(max_workers=MAX_WORKERS)
nota_bene_store = NotaBeneGDriveStore(CLIENT_SECRET_FILE, SCOPES)
nota_bene_encoder = NotaBeneEncoder(url = TEI_SERVICE_URL)

def transcript_ids(poem_id):
    """Retrieve all transcripts ID's for any given poem

    """

    transcript_paths = []

    for f in os.listdir(os.path.join(TEI_DIR_PATH, poem_id)):
        if fnmatch.fnmatch(f, '*.tei.xml') and f[0] != '.':
            transcript_id = re.sub(r'\.tei\.xml$', '', f)
            transcript_paths.append(transcript_id)

    return sorted(transcript_paths)

tokenizer_modules = {'SwiftSentenceTokenizer': 'swift_collate.tokenize',
                     'PunktSentenceTokenizer': 'swift_collate.tokenize',
                     'TreebankWordTokenizer': 'nltk.tokenize.treebank',
                     'StanfordTokenizer': 'nltk.tokenize.stanford'}
def tokenizer_module(tokenizer_class_name):

    if tokenizer_class_name in tokenizer_modules:
        module = tokenizer_modules[tokenizer_class_name]
    else:
        raise Exception("Failed to locate the tokenizer Module for %s" % tokenizer_class_name)

    return module

tagger_modules = {'AveragedPerceptron': 'nltk.tag.perceptron.AveragedPerceptron',
                  'UnigramTagger': 'nltk.tag.sequential.UnigramTagger'}
def tagger_module(tagger_class_name):

    if tagger_class_name == 'disabled':
        module = None
    elif tagger_class_name in tagger_modules:
        module = tagger_modules[tagger_class_name]
    else:
        raise Exception("Failed to locate the tagger Module for %s" % tagger_class_name)

    return module

class TokenizerFactory:

    def __init__(self, tokenizer_class_name):
        try:
            module_name = tokenizer_module(tokenizer_class_name)
            m = importlib.import_module(module_name)
            self.klass = getattr(m, tokenizer_class_name)
        except:
            raise "Could not load the selected tokenizer"

class TaggerFactory:

    def __init__(self, tagger_class_name):

        if tagger_class_name == 'disabled':
            self.tagger = None
        else:
            try:
                module_name = tagger_module(tagger_class_name)
                m = importlib.import_module(module_name)
                tagger_class = getattr(m, tagger_class_name)
                self.tagger = tagger_class()
            except Exception as tagger_ex:
                raise Exception("Could not load the selected part-of-speech tagger %s" % tagger_ex)

# Please see https://gist.github.com/mywaiting/4643396
def sig_handler(sig, frame):
    logging.warning('Caught signal: %s', sig)
    tornado.ioloop.IOLoop.instance().add_callback(shutdown)

def shutdown():
    logging.info('Stopping http server')
    server.stop()

    logging.info('Will shutdown in %s seconds ...', MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
    io_loop = tornado.ioloop.IOLoop.instance()

    deadline = time.time() + MAX_WAIT_SECONDS_BEFORE_SHUTDOWN

    def stop_loop():
        now = time.time()
        if now < deadline and (io_loop._callbacks or io_loop._timeouts):
            io_loop.add_timeout(now + 1, stop_loop)
        else:
            io_loop.stop()
            logging.info('Shutdown')
    stop_loop()
    
def main():

    parse_command_line()

    # https://gist.github.com/mywaiting/4643396
    global server
    server = tornado.httpserver.HTTPServer(application)
    server.bind(options.port)
    server.start(options.processes)

    # Extending the cleaning for individual threads
    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    ioloop = tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()
