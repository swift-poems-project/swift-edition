
import os
import ConfigParser

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
CLIENT_SECRET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'client_secret.json')
APPLICATION_NAME = 'Swift Poems Project Digital Edition'
MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = 3

# Retrieve the configuration settings
config = ConfigParser.RawConfigParser()
config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'swift_collate.cfg'))

# Work-around for multiprocessing within Tornado
MAX_WORKERS = config.getint('server', 'max_workers')
# Retrieve the cache configuration
MONGO_HOST = config.get('MongoDB', 'host')
MONGO_PORT = config.getint('MongoDB', 'port')
MONGO_DB = config.get('MongoDB', 'db_name')
# Retrieve the server configuration

DEBUG = config.getboolean('server', 'debug')
SECRET = config.get('server', 'secret')
TEI_DIR_PATH = config.get('tei_encoding', 'dir_path')
TEI_SERVICE_URL = config.get('tei_encoding', 'url')

from swift_edition.nota_bene import NotaBeneGDriveStore, NotaBeneEncoder
nota_bene_store = NotaBeneGDriveStore(CLIENT_SECRET_FILE, SCOPES)
nota_bene_encoder = NotaBeneEncoder(url = TEI_SERVICE_URL)

clients = []
