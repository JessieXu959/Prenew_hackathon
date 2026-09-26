"""Synthetic transport fixtures only. These are never loaded by the app."""
import io
import json
import unittest
from unittest.mock import patch
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import YouTube, APIError, import_csv

class ServerTests(unittest.TestCase):
    def test_missing_key(self):
        with self.assertRaisesRegex(APIError,'not configured'):
            YouTube('').search('pelikone','fi','all')

    def test_cached_transport_and_secret_not_in_response(self):
        client=YouTube('secret-for-test-only')
        with patch('server.urlopen',return_value=io.BytesIO(b'{"items":[]}')) as transport:
            self.assertEqual(client.get('search',q='pelikone'),{'items':[]})
            self.assertEqual(client.get('search',q='pelikone'),{'items':[]})
            self.assertEqual(transport.call_count,1)
            self.assertEqual(client.searches,1)

    def test_local_quota(self):
        from datetime import datetime,timezone
        client=YouTube('test');client.day=datetime.now(timezone.utc).date().isoformat();client.searches=40
        with self.assertRaisesRegex(APIError,'budget'):
            client.get('search',q='new')

    def test_upstream_error_redacted(self):
        from urllib.error import HTTPError
        client=YouTube('DO_NOT_LEAK')
        with patch('server.urlopen',side_effect=HTTPError('https://x/?key=DO_NOT_LEAK',403,'secret',{},None)):
            with self.assertRaises(APIError) as error: client.get('search',q='pc')
            self.assertNotIn('DO_NOT_LEAK',str(error.exception))

    def test_search_normalization_and_dedup(self):
        client=YouTube('test');calls=[]
        def transport(endpoint,**args):
            calls.append((endpoint,args))
            if endpoint=='search':return {'items':[{'snippet':{'channelId':'synthetic-channel'}}]*2,'nextPageToken':'next-fixture'}
            if endpoint=='channels':return {'items':[{'id':'synthetic-channel','snippet':{'title':'SYNTHETIC TEST ONLY'},'statistics':{'subscriberCount':'1200'},'contentDetails':{'relatedPlaylists':{'uploads':'synthetic-playlist'}}}]}
            if endpoint=='playlistItems':return {'items':[{'contentDetails':{'videoId':'synthetic01'}}]}
            if endpoint=='videos':return {'items':[{'id':'synthetic01','snippet':{'title':'pelikone budjetti testi','publishedAt':'2026-09-01T00:00:00Z','defaultAudioLanguage':'fi'},'statistics':{'viewCount':'600','commentCount':'4'},'contentDetails':{}}]}
        client.get=transport
        response=client.search('halpa pelikone','fi','nano')
        self.assertEqual(len(response['creators']),1)
        c=response['creators'][0]
        self.assertEqual(c['followers'],1200);self.assertEqual(c['recentViews'],600)
        self.assertIsNone(c['audienceCountry']);self.assertIsNone(c['engagement']);self.assertIsNone(c['videos'][0]['likes'])
        self.assertEqual(response['nextPageToken'],'next-fixture')
        self.assertNotIn('regionCode',calls[0][1]);self.assertEqual(calls[0][1]['relevanceLanguage'],'fi')
        self.assertTrue(client.search('halpa pelikone','fi','nano')['cached'])
        self.assertEqual(len(calls),4)

    def test_search_keeps_matched_video_first(self):
        client=YouTube('test');video_ids=[]
        def transport(endpoint,**args):
            if endpoint=='search':return {'items':[{'id':{'videoId':'matched0001'},'snippet':{'channelId':'synthetic-channel'}}]}
            if endpoint=='channels':return {'items':[{'id':'synthetic-channel','snippet':{'title':'SYNTHETIC TEST ONLY'},'statistics':{'subscriberCount':'1200'},'contentDetails':{'relatedPlaylists':{'uploads':'synthetic-playlist'}}}]}
            if endpoint=='playlistItems':return {'items':[{'contentDetails':{'videoId':'latest00001'}}]}
            if endpoint=='videos':
                video_ids.append(args['id'])
                return {'items':[{'id':x,'snippet':{'title':x,'defaultAudioLanguage':'fi','publishedAt':'2026-09-01T00:00:00Z'},'statistics':{}} for x in reversed(args['id'].split(','))]}
        client.get=transport
        videos=client.search('halpa pelikone','fi','all')['creators'][0]['videos']
        self.assertEqual(video_ids,['matched0001,latest00001'])
        self.assertEqual([(v['id'],v['matchedSearch']) for v in videos],[('matched0001',True),('latest00001',False)])
