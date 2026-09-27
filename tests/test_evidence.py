"""Regression tests for trustworthy publication-window metrics and strict discovery."""
import unittest
from datetime import datetime, timezone, timedelta
from discovery_evidence import recent_view_summary, assess_language, public_contact
from server import YouTube, APIError, import_csv

END = datetime(2026, 9, 27, 12, tzinfo=timezone.utc)
def video(i, days=5, views=100, **kwargs):
    return dict(id=str(i), title='Rakensin halvan pelikoneen', description='Näytönohjain ja tietokone',
                url='https://youtube.com/watch?v='+str(i), publishedAt=(END-timedelta(days=days)).isoformat(),
                views=views, recentUpload=True, audioLanguage='fi', **kwargs)

class EvidenceTests(unittest.TestCase):
    def test_thirty_days_excludes_old_search_matches_and_future_or_live_videos(self):
        videos=[video(1,views=100), video(2,views=200),video(3,views=300),video(4,days=45,views=9000),
                video(5,days=-1,views=8000),video(6,broadcastStatus='live')]
        videos.append(dict(video(7,views=1000000), recentUpload=False, matchedSearch=True))
        result=recent_view_summary(videos,END.isoformat())
        self.assertEqual((result['average'],result['windowDays'],result['sampleSize']),(200,30,3))
        self.assertEqual(result['videoIds'],['1','2','3'])

    def test_ninety_day_fallback_with_exact_boundary(self):
        result=recent_view_summary([video(1,10,0),video(2,40,60),video(3,90,120),video(4,91,999)],END.isoformat())
        self.assertEqual((result['average'],result['windowDays'],result['sampleSize']),(60,90,3))

    def test_small_sample_does_not_display_misleading_average(self):
        result=recent_view_summary([video(1),video(2,views=None)],END.isoformat())
        self.assertIsNone(result['average']);self.assertEqual(result['sampleSize'],1)
        self.assertEqual(result['status'],'insufficient');self.assertEqual(result['missingViewCount'],1)

    def test_missing_dates_and_view_counts_stay_unknown(self):
        result=recent_view_summary([dict(video(1),publishedAt=None),video(2,views=None)],END.isoformat())
        self.assertIsNone(result['average']);self.assertEqual(result['sampleSize'],0)

    def test_upload_cap_is_disclosed_only_when_window_truncated(self):
        videos=[video(i) for i in range(50)]
        self.assertTrue(recent_view_summary(videos,END.isoformat(),True)['sampleLimited'])
        videos.append(video(51,days=100))
        self.assertFalse(recent_view_summary(videos,END.isoformat(),True)['sampleLimited'])

    def test_consistent_recent_language_required(self):
        videos=[video(i) for i in range(5)]
        self.assertTrue(assess_language(None,videos,'fi')['accepted'])
        self.assertFalse(assess_language('fi',[], 'fi')['accepted'])
        self.assertFalse(assess_language('fi',videos[:1],'fi')['accepted'])
        videos[1]['audioLanguage']=None;videos[2]['audioLanguage']=None
        self.assertTrue(assess_language(None,videos,'fi')['accepted'])

    def test_conflicting_language_excluded_even_with_positive_metadata(self):
        for conflict in ['pt-BR','zh-Hans','ja','en']:
            videos=[dict(video(i),audioLanguage='sv-SE') for i in range(5)]
            videos[0]['audioLanguage']=conflict
            self.assertFalse(assess_language('sv',videos,'sv')['accepted'])
        self.assertTrue(assess_language('en',[dict(video(i),metadataLanguage='en') for i in range(5)],'fi')['accepted'])
        self.assertFalse(assess_language(None,[dict(video(i),audioLanguage=None,metadataLanguage='de') for i in range(5)],'fi')['accepted'])
        self.assertTrue(assess_language(None,[dict(video(i),audioLanguage=None,metadataLanguage='fi') for i in range(5)],'fi')['accepted'])

    def test_search_hit_and_english_game_title_cannot_rescue_no_evidence(self):
        videos=[dict(video(i),title='Minecraft Fortnite RTX 5090',audioLanguage=None) for i in range(5)]
        videos.append(dict(video(9),recentUpload=False,matchedSearch=True))
        self.assertFalse(assess_language(None,videos,'fi')['accepted'])

    def test_only_five_latest_uploads_used_for_language(self):
        videos=[video(i,days=i+1) for i in range(5)]+[dict(video(9,days=40),audioLanguage='en')]
        self.assertTrue(assess_language(None,videos,'fi')['accepted'])

    def test_contact_requires_explicit_public_contact_context(self):
        self.assertIsNone(public_contact('Visit my channel!','https://youtube.com/channel/example'))
        self.assertIsNone(public_contact('Discount code: offers@example.com','https://youtube.com/channel/example'))
        found=public_contact('Business inquiries: hello@example.com','https://youtube.com/channel/example/about')
        self.assertEqual(found['value'],'hello@example.com')
        self.assertEqual(found['kind'],'Public business email')
        self.assertEqual(public_contact('Kontakt: https://example.com/contact','https://youtube.com/channel/example/about')['value'],'https://example.com/contact')

    def test_country_mismatch_or_unknown_rejected_before_upload_fetch(self):
        client=YouTube('test');calls=[]
        def get(endpoint,**kwargs):
            calls.append(endpoint)
            if endpoint=='search':return {'items':[{'snippet':{'channelId':str(i)}} for i in range(4)]}
            if endpoint=='channels':return {'items':[{'id':str(i),'statistics':{'subscriberCount':'1000'},'snippet':{'title':'Fixture','country':country}} for i,country in enumerate(['BR','CN','JP',None])]}
            self.fail('Must not enrich mismatched countries')
        client.get=get
        result=client.search('speldator','sv','all',market='SE')
        self.assertEqual(result['creators'],[]);self.assertEqual(result['excluded']['countryMismatch'],3)
        self.assertEqual(result['excluded']['countryUnknown'],1);self.assertEqual(calls,['search','channels'])

    def test_market_in_cache_identity_and_unsupported_market_fails(self):
        client=YouTube('test');client.get=lambda endpoint,**params:{'items':[]}
        self.assertFalse(client.search('PC','en','all',market='FI')['cached'])
        self.assertFalse(client.search('PC','en','all',market='DE')['cached'])
        self.assertTrue(client.search('PC','en','all',market='FI')['cached'])
        self.assertEqual(client.search('mänguarvuti','et','all',market='EE')['creators'],[])
        with self.assertRaises(APIError):client.search('PC','en','all',market='ZZ')

    def test_csv_one_video_is_not_recent_average(self):
        c=import_csv('name,platform,source_url,provenance,video_url,video_title,views\nTest,TikTok,https://tiktok.com/@test,Fixture,https://tiktok.com/@test/video/1,Sample,5000','fixture.csv')['creators'][0]
        self.assertIsNone(c['recentViews']);self.assertEqual(c['sourceType'],'imported')
        self.assertEqual(c['videos'][0]['views'],5000)

if __name__=='__main__':unittest.main()

from server import APIError

class SubscriberGateTests(unittest.TestCase):
    def test_floor_cap_and_search_order(self):
        client=YouTube('test'); calls=[]
        def get(endpoint,**kwargs):
            calls.append((endpoint,kwargs))
            if endpoint=='search':return {'items':[{'snippet':{'channelId':str(n)}} for n in [799,800,1000,1001]]}
            if endpoint=='channels':return {'items':[{'id':str(n),'statistics':{'subscriberCount':str(n)},'snippet':{'title':'Fixture','country':'JP'}} for n in [799,800,1000,1001]]}
            self.fail('Wrong country must be rejected before upload retrieval')
        client.get=get
        result=client.search('pc','fi','all',market='FI',max_subscribers=1000)
        self.assertEqual(result['funnel']['subscribers'],2)
        self.assertEqual(calls[0][1]['order'],'relevance')
        with self.assertRaises(APIError):client.search('pc','fi','all',max_subscribers=799)
