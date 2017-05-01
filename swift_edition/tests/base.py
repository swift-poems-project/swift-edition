import time
import requests
from contextlib import contextmanager
from threading import Thread, Event
from unittest import TestCase

from tornado.escape import to_unicode
from tornado.ioloop import IOLoop
import tornado.options

# from nbviewer.app import main
from .. import application
from ..utils import url_path_join

class EditionTestCase(TestCase):
    """A base class for tests that need a running nbviewer server."""

    port = 12341
    processes = 1

    def assertIn(self, observed, expected, *args, **kwargs):
        return super(NBViewerTestCase, self).assertIn(
            to_unicode(observed),
            to_unicode(expected),
            *args,
            **kwargs
        )

    def assertNotIn(self, observed, expected, *args, **kwargs):
        return super(NBViewerTestCase, self).assertNotIn(
            to_unicode(observed),
            to_unicode(expected),
            *args,
            **kwargs
        )
            
    @classmethod
    def wait_until_alive(cls):
        """Wait for the server to be alive"""
        while True:
            try:
                requests.get(cls.url())
            except Exception:
                time.sleep(.1)
            else:
                break

    @classmethod
    def wait_until_dead(cls):
        """Wait for the server to stop getting requests after shutdown"""
        while True:
            try:
                requests.get(cls.url())
            except Exception:
                break
            else:
                time.sleep(.1)

    @classmethod
    def setup_class(cls):
        cls._start_evt = Event()
        cls.server = Thread(target=cls._server_main)
        # cls.server = cls._server_main()
        cls.server.start()
        cls._start_evt.wait()
        cls.wait_until_alive()

    @classmethod
    def get_server_args(cls):
        return []

    @classmethod
    def _server_main(cls):
        cls._server_loop = loop = IOLoop()
        loop.make_current()
        cls._server_loop.add_callback(cls._start_evt.set)

        # Need to push this into a separate Module
        #        main(['', '--port=%d' % cls.port] + cls.get_server_args())
        http_server = tornado.httpserver.HTTPServer(application)
        http_server.bind(cls.port)
        http_server.start(cls.processes)
        ioloop = tornado.ioloop.IOLoop.current().start()

        loop.close(all_fds=True)
    @classmethod
    def teardown_class(cls):
        cls._server_loop.add_callback(cls._server_loop.stop)
        cls.server.join()
        cls.wait_until_dead()

    @classmethod
    def url(cls, *parts):
        return url_path_join('http://localhost:%i' % cls.port, *parts)
    
