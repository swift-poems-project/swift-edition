
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from io import BytesIO
from apiclient import discovery
from apiclient.http import MediaIoBaseDownload
from httplib2 import Http

class GDriveService(object):

    def __init__(self, client_secret_file, scopes):

        credentials = ServiceAccountCredentials.from_json_keyfile_name(client_secret_file, scopes)
        _http = credentials.authorize(Http())
        self._service = discovery.build('drive', 'v3', http=_http)

    def file(self, file_id):

        request = self._service.files().get_media(fileId=file_id)
        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            # print "Download %d%%." % int(status.progress() * 100)
        return fh

    def items(self, query, _fields = "nextPageToken, files(id, name)"):

        results = self._service.files().list(q=query,fields=_fields).execute()
        items = results.get('files', [])
        return items
