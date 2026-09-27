"""Synthetic transport fixtures only. These are never loaded by the app."""
import io
import json
import unittest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import YouTube, APIError, import_csv

class ServerTests(unittest.TestCase):
    def test_rate_limit_cooldown_and_recovery(self):
        from urllib.error import HTTPError
        client=YouTube('SECRET')
        with patch('server.time.time',return_value=1000), patch('server.urlopen',side_effect=HTTPError('https://x/?key=SECRET',429,'limited',{'Retry-After':'120'},None)) as transport:
            with self.assertRaises(APIError) as caught: client.get('search',q='pc')
            self.assertEqual(caught.exception.status,429)
            self.assertNotIn('SECRET',str(caught.exception))
            with self.assertRaises(APIError): client.get('search',q='different')
            self.assertEqual(transport.call_count,1)
        with patch('server.time.time',return_value=1121), patch('server.urlopen',return_value=io.BytesIO(b'{"items":[]}')):
            self.assertEqual(client.get('search',q='pc'),{'items':[]})

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
            if endpoint=='search':return {'items':[{'snippet':{'channelId':'synthetic-channel'}}]*2,**({'nextPageToken':'next-fixture'} if not args.get('pageToken') else {})}
            if endpoint=='channels':return {'items':[{'id':'synthetic-channel','snippet':{'title':'SYNTHETIC TEST ONLY','country':'FI'},'statistics':{'subscriberCount':'1200'},'contentDetails':{'relatedPlaylists':{'uploads':'synthetic-playlist'}}}]}
            if endpoint=='playlistItems':return {'items':[{'contentDetails':{'videoId':vid}} for vid in ['synthetic01','synthetic02','synthetic03']]}
            if endpoint=='videos':return {'items':[{'id':vid,'snippet':{'title':'pelikone budjetti testi','publishedAt':datetime.now(timezone.utc).isoformat(),'defaultAudioLanguage':'fi'},'statistics':{'viewCount':'600','commentCount':'4'},'contentDetails':{}} for vid in args['id'].split(',')]}
        client.get=transport
        response=client.search('halpa pelikone','fi','nano')
        self.assertEqual(len(response['creators']),1)
        c=response['creators'][0]
        self.assertEqual(c['followers'],1200);self.assertEqual(c['recentViews'],600)
        self.assertIsNone(c['audienceCountry']);self.assertIsNone(c['engagement']);self.assertIsNone(c['videos'][0]['likes'])
        self.assertIsNone(response['nextPageToken'])
        self.assertEqual(response['discovery']['searchRequests'],2)
        self.assertEqual(response['discovery']['uniqueChannels'],1)
        self.assertEqual(calls[0][1]['regionCode'],'FI');self.assertEqual(calls[0][1]['relevanceLanguage'],'fi')
        self.assertTrue(client.search('halpa pelikone','fi','nano')['cached'])
        self.assertEqual(len(calls),5)
        self.assertEqual(client.search('pc','sv','all')['creators'],[])
        calls.clear()
        self.assertEqual(c['videos'][0]['matchedSearch'],False)
        client.search('halpa pelikone','fi','nano','next-fixture')
        self.assertEqual(calls[0][1]['pageToken'],'next-fixture')

    def test_search_keeps_matched_video_first(self):
        client=YouTube('test');video_ids=[]
        def transport(endpoint,**args):
            if endpoint=='search':return {'items':[{'id':{'videoId':'matched0001'},'snippet':{'channelId':'synthetic-channel'}}]}
            if endpoint=='channels':return {'items':[{'id':'synthetic-channel','snippet':{'title':'SYNTHETIC TEST ONLY','country':'FI'},'statistics':{'subscriberCount':'1200'},'contentDetails':{'relatedPlaylists':{'uploads':'synthetic-playlist'}}}]}
            if endpoint=='playlistItems':return {'items':[{'contentDetails':{'videoId':vid}} for vid in ['latest00001','latest00002','latest00003']]}
            if endpoint=='videos':
                video_ids.append(args['id'])
                return {'items':[{'id':x,'snippet':{'title':x,'defaultAudioLanguage':'fi','publishedAt':'2026-09-01T00:00:00Z'},'statistics':{}} for x in reversed(args['id'].split(','))]}
        client.get=transport
        videos=client.search('halpa pelikone','fi','all')['creators'][0]['videos']
        self.assertEqual(video_ids,['matched0001,latest00001,latest00002,latest00003'])
        self.assertEqual([(v['id'],v['matchedSearch']) for v in videos],[('matched0001',True),('latest00001',False),('latest00002',False),('latest00003',False)])

    def test_csv_unknowns_and_quoted_fields(self):
        value='name,platform,source_url,provenance,followers,audience_country\n"SYNTHETIC, TEST",Twitch,https://www.twitch.tv/synthetic_test_only,TEST FIXTURE ONLY,,FI\n'
        result=import_csv(value,'test.csv')['creators'][0]
        self.assertEqual(result['name'],'SYNTHETIC, TEST');self.assertIsNone(result['followers']);self.assertIsNone(result['audienceCountry'])
        self.assertEqual(result['sourceType'],'imported')
        duplicate=value+value.splitlines()[1]+'\n'
        self.assertEqual(import_csv(duplicate,'test.csv')['count'],1)

    def test_csv_validation_atomic(self):
        for row in ['bad,Twitch,javascript:alert(1),test,', 'bad,Twitch,https://example.com/test,test,', 'bad,Twitch,https://twitch.tv/test,test,-2']:
            with self.assertRaises(APIError):import_csv('name,platform,source_url,provenance,followers\n'+row,'test.csv')
        with self.assertRaises(APIError):import_csv('name\nx','test.csv')

if __name__=='__main__':unittest.main()
