import os
import sys
import pytest

from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tokenizer import ElementToken

class TestElementToken:

    @pytest.fixture
    def tei_doc(self):

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures/test_tei.xml')) as f:

            data = f.read()

        return etree.fromstring(data)

    @pytest.fixture
    def tei_stanza(self):

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures/test_tei.xml')) as f:

            data = f.read()
            doc = etree.fromstring(data)
            elems = doc.xpath('//tei:lg', namespaces={'tei': 'http://www.tei-c.org/ns/1.0'})
            elem = elems.pop()

        return elem

    def test_init(self, tei_stanza):

        tag = tei_stanza.xpath('local-name()')
        token = ElementToken(tag, tei_stanza.attrib)
        assert token.name == 'lg'
        assert token.attrib['n'] == '1'

        pass
