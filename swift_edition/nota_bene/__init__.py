from ..g_drive_service import GDriveService
import requests
import os
import json
from lxml import etree

class NotaBeneStore(object):

    def __init__(self):
        pass

class NotaBeneGDriveStore(NotaBeneStore):

    def __init__(self, client_secret_file, scopes):

        self._service = GDriveService(client_secret_file, scopes)

    def source(self, source_id):

        drive_files = []
        query = "name contains '" + source_id + "'"

        for item in self._service.items(query):
            word_doc_match = re.search('\.doc$', item['name'], flags=re.IGNORECASE)
            if not word_doc_match:
                fh = self._service.file(item['id'])
                drive_file_content = fh.getvalue()
                drive_files.append(drive_file_content)
                fh.close()

        return drive_files

    def transcript(self, transcript_id):

        drive_files = []
        query = "name = '" + transcript_id + "'"

        for item in self._service.items(query):

            fh = self._service.file(item['id'])
            drive_file_content = fh.getvalue()
            drive_files.append(drive_file_content)
            fh.close()

        try:
            return drive_files.pop()
        except:
            raise IOError("Failed to find the Google Drive File for " + transcript_id)


class NotaBeneEncoder(object):

    def __init__(self, protocol = 'http', host = 'localhost', port = 9292, url = 'http://localhost', cache_path = None):
        
        self._url = url
        if cache_path:
            self.cache_path
        else:
            self.cache_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'tmp', 'tei')

    def poem_cache_get(self, poem_id):

        cached_glob_path = os.path.join(self.cache_path, '*.tei.xml')
        cached = []
        for cached_file_path in glob.glob(cached_glob_path):
            if os.path.isfile(cached_file_path):
                fh = open(cached_file_path, 'rb')
                cached.append(fh.read())
                fh.close()
        return cached

    def transcript_cache_get(self, transcript_id):

        cached_file_path = os.path.join(self.cache_path, transcript_id + '.tei.xml')
        cached = None
        if os.path.isfile(cached_file_path):
            fh = open(cached_file_path, 'rb')
            cached = fh.read()
            fh.close()

        return cached

    def transcript_cache_set(self, transcript_id, cached):

        cached_file_path = os.path.join(self.cache_path, transcript_id + '.tei.xml')
        fh = open(cached_file_path, 'wb')
        fh.write(cached)
        fh.close()

    def transcript(self, source_id, transcript_id, nota_bene = None):
        tei_xml = self.transcript_cache_get(transcript_id)

        if tei_xml is None:

            if nota_bene:
                endpoint = "/".join([self._url, source_id, transcript_id, 'encode'])
                response = requests.post(endpoint, data=nota_bene, verify=False)
                tei_xml = response.text
            else:
                endpoint = "/".join([self._url, 'transcripts', transcript_id])
                response = requests.get(endpoint, verify=False)
                try:
                    transcript = json.loads(response.text)
                    tei_xml = transcript['tei']
                except Exception as e:
                    tei_xml = ''

            self.transcript_cache_set(transcript_id, tei_xml.encode('utf-8'))
            
        return tei_xml

    def transcripts(self, poem = None):
        if poem:
            endpoint = "/".join([self._url, 'transcripts', 'encode'])
            response = requests.post(endpoint, data={'poem': poem}, verify=False)
            
            transcript_ids = json.loads(response.text)
            transcripts_xml = map(lambda transcript_id: self.transcript(None, transcript_id), transcript_ids)

            tei_docs = []
            for xml in transcripts_xml:
                try:
                    tei_doc = etree.fromstring(xml)
                    tei_docs.append(tei_doc)
                except:
                    pass

        return [transcript_ids,tei_docs]

    def poems(self):
        endpoint = "/".join([self._url, 'poems'])
        response = requests.get(endpoint, verify=False)
        return json.loads(response.text)

    def poem(self, poem_id):
        endpoint = "/".join([self._url, 'poems', poem_id])
        response = requests.get(endpoint, verify=False)
        response_ids = json.loads(response.text)

        tei_docs = []
        transcript_ids = []
        for transcript_id in response_ids:
            xml = self.transcript(None, transcript_id)

            try:
                tei_doc = etree.fromstring(xml)
                tei_docs.append(tei_doc)
                transcript_ids.append(transcript_id)
            except Exception as e:
                print("Failed to retrieve the TEI Document for " + transcript_id)
                print(str(e))

        return [transcript_ids,tei_docs]

