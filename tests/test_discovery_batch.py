"""Search coverage is measured in unique channels, never raw video matches."""
import unittest
from server import YouTube, APIError


class DiscoveryBatchTests(unittest.TestCase):
    def test_two_hundred_unique_channels_batched_at_fifty(self):
        client, calls = YouTube('fixture'), []
        def get(endpoint, **params):
            calls.append((endpoint, params))
            if endpoint == 'search':
                page = int(params.get('pageToken', 0))
                # Overlapping videos/channels force pagination past 200 raw matches.
                return {'items': [{'id': {'videoId': str(i)}, 'snippet': {'channelId': str(i)}}
                                  for i in range(page*40, page*40+50)], 'nextPageToken': str(page+1)}
            if endpoint == 'channels':
                return {'items': [{'id': cid, 'snippet': {'country': 'JP'}, 'statistics': {'subscriberCount': '1000'}}
                                  for cid in params['id'].split(',')]}
            self.fail('Wrong-country channels should not be enriched')
        client.get = get
        result = client.search('pelikone', 'fi', 'all', market='FI')
        self.assertEqual(result['funnel']['channels'], 200)
        self.assertEqual(result['funnel']['matches'], 250)
        self.assertEqual(result['discovery']['stopReason'], 'target_reached')
        channel_calls = [params for endpoint, params in calls if endpoint == 'channels']
        self.assertEqual([len(p['id'].split(',')) for p in channel_calls], [50]*4)
        self.assertEqual(len(set(','.join(p['id'] for p in channel_calls).split(','))), 200)
        self.assertTrue(all(p['order']=='relevance' and p['maxResults']==50 for e,p in calls if e=='search'))

    def test_alternatives_rotate_and_preserve_provenance(self):
        client, calls = YouTube('fixture'), []
        def get(endpoint, **params):
            calls.append((params['q'], params.get('pageToken')))
            return {'items': [{'id': {'videoId': params['q']}, 'snippet': {'channelId': 'same'}}],
                    **({'nextPageToken':'second'} if 'pageToken' not in params else {})}
        client.get = get
        ids, hits, origins, matches, stats, warnings = client.collect_candidates('pelikone | pelitietokone','fi','FI','video')
        self.assertEqual(calls,[('pelikone',None),('pelitietokone',None),('pelikone','second'),('pelitietokone','second')])
        self.assertEqual(ids,['same'])
        self.assertEqual(origins['same'],['pelikone','pelitietokone'])
        self.assertEqual(len(hits['same']),2)
        self.assertEqual(stats['stopReason'],'results_exhausted')

    def test_request_budget_and_repeated_tokens_terminate(self):
        client = YouTube('fixture')
        client.get = lambda endpoint, **p: {'items':[{'snippet':{'channelId':'same'}}], 'nextPageToken':str(int(p.get('pageToken',0))+1)}
        result = client.collect_candidates('speldator','sv','SE','video')
        self.assertEqual(result[4]['searchRequests'],12)
        self.assertEqual(result[4]['stopReason'],'request_budget')
        client.get = lambda endpoint, **p: {'items':[], 'nextPageToken':'repeated'}
        result = client.collect_candidates('speldator','sv','SE','video')
        self.assertEqual(result[4]['searchRequests'],2)

    def test_partial_search_reports_api_limit(self):
        client = YouTube('fixture')
        def get(endpoint, **params):
            if params.get('pageToken'):
                raise APIError('Local request budget reached',429)
            return {'items':[{'snippet':{'channelId':'one'}}],'nextPageToken':'next'}
        client.get = get
        result = client.collect_candidates('mänguarvuti','et','EE','video')
        self.assertEqual(result[0],['one'])
        self.assertEqual(result[4]['stopReason'],'upstream_limit')
        self.assertEqual(result[5],['Local request budget reached'])

    def test_invalid_query_family_and_channel_mode(self):
        client = YouTube('fixture')
        for query in [' | ', '|'.join(str(i) for i in range(9))]:
            with self.assertRaises(APIError):client.collect_candidates(query,'fi','FI','video')
        def get(endpoint, **params):
            self.assertNotIn('publishedAfter',params)
            return {'items':[]}
        client.get = get
        self.assertEqual(client.collect_candidates('test','fi','FI','channel')[4]['uniqueChannels'],0)


if __name__ == '__main__':
    unittest.main()
