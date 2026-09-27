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

    def test_early_filter_and_batched_videos(self):
        client=YouTube('test'); calls=[]
        def transport(endpoint, **args):
            calls.append((endpoint,args))
            if endpoint=='search': return {'items':[{'snippet':{'channelId':c}} for c in ['small','a','b']]}
            if endpoint=='channels': return {'items':[{'id':c,'snippet':{'title':c},'statistics':{'subscriberCount':str(n)},'contentDetails':{'relatedPlaylists':{'uploads':c}}} for c,n in [('small',500),('a',501),('b',1000)]]}
            if endpoint=='playlistItems': return {'items':[{'contentDetails':{'videoId':args['playlistId']}}]}
            if endpoint=='videos': return {'items':[{'id':c,'snippet':{'title':'budget PC','publishedAt':'2026-09-01','defaultAudioLanguage':'fi'},'statistics':{'viewCount':str(n)}} for c,n in [('a',5000),('b',5001)]]}
        client.get=transport
        result=client.search('pc','fi','all')
        self.assertEqual([c['channelId'] for c in result['creators']],['b'])
        self.assertEqual([a['playlistId'] for e,a in calls if e=='playlistItems'],['a','b'])
        self.assertEqual([a['id'] for e,a in calls if e=='videos'],['a,b'])
        self.assertEqual(result['funnel'],dict(videoMatches=3,channels=3,subscribers=2,size=2,language=2,views=1))
        self.assertTrue(client.search('pc','fi','all')['cached'])
        self.assertFalse(client.search('pc','fi','all',min_average_views=4999)['cached'])
        with self.assertRaises(APIError): client.search('pc','fi','all',min_subscribers='bad')

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
            if endpoint=='videos':return {'items':[{'id':'synthetic01','snippet':{'title':'pelikone budjetti testi','publishedAt':'2026-09-01T00:00:00Z','defaultAudioLanguage':'fi'},'statistics':{'viewCount':'6000','commentCount':'4'},'contentDetails':{}}]}
        client.get=transport
        response=client.search('halpa pelikone','fi','nano')
        self.assertEqual(len(response['creators']),1)
        c=response['creators'][0]
        self.assertEqual(c['followers'],1200);self.assertEqual(c['recentViews'],6000)
        self.assertIsNone(c['audienceCountry']);self.assertIsNone(c['engagement']);self.assertIsNone(c['videos'][0]['likes'])
        self.assertEqual(response['nextPageToken'],'next-fixture')
        self.assertNotIn('regionCode',calls[0][1]);self.assertEqual(calls[0][1]['relevanceLanguage'],'fi')
        self.assertTrue(client.search('halpa pelikone','fi','nano')['cached'])
        self.assertEqual(len(calls),4)
        self.assertEqual(client.search('pc','sv','all')['creators'],[])
        calls[:]=calls[:4]
        self.assertEqual(c['videos'][0]['matchedSearch'],False)
        client.search('halpa pelikone','fi','nano','next-fixture')
        self.assertEqual(calls[4][1]['pageToken'],'next-fixture')
        calls.clear()
        channel_result=client.search('halpa pelikone','fi','nano',mode='channel')
        self.assertFalse(channel_result['cached'])
        self.assertEqual(calls[0][1]['type'],'channel')
        self.assertNotIn('publishedAfter',calls[0][1])
        self.assertEqual(len(channel_result['creators']),1)
        self.assertTrue(client.search('halpa pelikone','fi','nano',mode='channel')['cached'])
        with self.assertRaises(APIError): client.search('pc','fi','all',mode='invalid')


    def test_search_keeps_matched_video_first(self):
        client=YouTube('test');video_ids=[]
        def transport(endpoint,**args):
            if endpoint=='search':return {'items':[{'id':{'videoId':'matched0001'},'snippet':{'channelId':'synthetic-channel'}}]}
            if endpoint=='channels':return {'items':[{'id':'synthetic-channel','snippet':{'title':'SYNTHETIC TEST ONLY'},'statistics':{'subscriberCount':'1200'},'contentDetails':{'relatedPlaylists':{'uploads':'synthetic-playlist'}}}]}
            if endpoint=='playlistItems':return {'items':[{'contentDetails':{'videoId':'latest00001'}}]}
            if endpoint=='videos':
                video_ids.append(args['id'])
                return {'items':[{'id':x,'snippet':{'title':x,'defaultAudioLanguage':'fi','publishedAt':'2026-09-01T00:00:00Z'},'statistics':{'viewCount':'6000'}} for x in reversed(args['id'].split(','))]}
        client.get=transport
        videos=client.search('halpa pelikone','fi','all')['creators'][0]['videos']
        self.assertEqual(video_ids,['matched0001,latest00001'])
        self.assertEqual([(v['id'],v['matchedSearch']) for v in videos],[('matched0001',True),('latest00001',False)])

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
