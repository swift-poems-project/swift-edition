import requests
from .base import EditionTestCase

class IndexTestCase(EditionTestCase):
    def test_get(self):
        url = self.url('/')
        r = requests.get(url)
        self.assertEqual(r.status_code, 200)
