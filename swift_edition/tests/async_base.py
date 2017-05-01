from tornado import testing
from tornado.escape import to_unicode

from .. import application

class AsyncEditionTestCase(testing.AsyncHTTPTestCase):
    """ Base case for testing the Digital Edition app asynchronously
    """
    def get_app(self):
        """ create an Edition tornado app instance for testing
        """
        return application
    
    def assertIn(self, observed, expected, *args, **kwargs):
        """ test whether the observed contains the expected, in utf-8
        """
        return super(AsyncNbviewerTestCase, self).assertIn()
