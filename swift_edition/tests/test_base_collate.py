from unittest import TestCase
from mock import Mock

import os.path
import json

from ..routes import BaseCollateHandler,CollateSocketHandler

class BaseCollateTestCase(TestCase):

    def setUp(self):

        app = Mock(ui_methods={})
        attrs = { 'set_close_callback.return_value': None }
        
        connection = Mock()
        connection.configure_mock(**attrs)
        request_mock = Mock(connection=connection)

        fixture_1 = open(os.path.join(os.path.dirname(__file__), 'fixtures','006-35D-.tei.xml')).read()
        fixture_2 = open(os.path.join(os.path.dirname(__file__), 'fixtures','006-ROGP.tei.xml')).read()
        fixture_3 = open(os.path.join(os.path.dirname(__file__), 'fixtures','006-WILH.tei.xml')).read()
        
        transcript_mock = Mock(side_effect=[fixture_1, fixture_2, fixture_3])
        encoder_mock = Mock(transcript=transcript_mock)
        
        self.handler = CollateSocketHandler(app, request_mock, clients=[], nota_bene_encoder=encoder_mock)

        ws_connection_mock = Mock()
        self.handler.ws_connection = ws_connection_mock

    def test_on_message(self):

        message = json.dumps({
            "poemId": '006-',
            "baseText": "006-35D-",
            "variantTexts": ["006-WILH", "006-ROGP"]
        })
        self.handler.on_message(message)

        # Verify the input
        self.assertEqual(self.handler.poem_id, '006-')
        self.assertEqual(self.handler.base_id, '006-35D-')
        self.assertEqual(self.handler.transcript_ids, ["006-WILH", "006-ROGP"])
        
        # Verify the output
        self.assertIsInstance(self.handler.response_body, str)
        
