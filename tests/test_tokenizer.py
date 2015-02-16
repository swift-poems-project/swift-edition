import os
import sys
import pytest

from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tokenizer import Tokenizer

class TestTokenizer:

    @pytest.fixture
    def tei_xml(self):

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures/test_tei.xml')) as f:

            data = f.read()

        return data

    def test_init(self):

        pass

    def test_parse(self, tei_xml):
        
        pass
