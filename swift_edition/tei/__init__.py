from lxml import etree

class TeiParser(object):

    @staticmethod
    def parse(content):
        return etree.fromstring(content)
