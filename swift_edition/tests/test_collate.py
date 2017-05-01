# import requests
import tornado
from tornado import testing
import json
import time

from .async_base import AsyncEditionTestCase

class CollateSocketTestCase(AsyncEditionTestCase):

    @tornado.testing.gen_test
    def test_open(self):
        ws_url = "ws://localhost:" + str(self.get_http_port()) + "/stream"
        ws_client = yield tornado.websocket.websocket_connect(ws_url)

        response = yield ws_client.read_message()
        message = json.loads(response)

        self.assertEqual(message, {"status": "Collation engine ready"})

    @tornado.testing.gen_test        
    def test_ping(self):

        ws_url = "ws://localhost:" + str(self.get_http_port()) + "/stream"
        ws_client = yield tornado.websocket.websocket_connect(ws_url, io_loop=self.io_loop)

        # self.assertEqual(message, {"status": "Collation engine ready"})
        #        client_message = { 'poemId': "006-", 'baseText': "006-35D-", 'variantTexts': ["006-ROGP", "006-WILH"] }
        #        ws_client.write_message(json.dumps(client_message))
        ws_client.write_message('9')

        response = yield ws_client.read_message()
        server_message = json.loads(response)

        self.assertEqual(server_message, {"status": "Collation engine ready"})
        # @todo Assert that this was logged
