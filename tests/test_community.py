import unittest
from community import analyze, classify
from discovery_evidence import MARKETS

class CommunityTests(unittest.TestCase):
    def test_new_languages_and_classification(self):
        self.assertEqual(MARKETS['EE'], 'et')
        self.assertEqual(MARKETS['HU'], 'hu')
        self.assertIn('Hardware discussion', classify('Would this GPU run CS2?'))
        self.assertEqual(classify('Lovely video!'), ['Uncertain / general reaction'])

    def test_dedup_replies_and_repeat_participants(self):
        class Client:
            calls = 0
            def get(self, endpoint, **args):
                self.calls += 1
                if endpoint == 'videos':
                    return {'items':[{'id':v,'snippet':{'channelId':'creator'}} for v in args['id'].split(',')]}
                vid=args['videoId']
                return {'items':[{'snippet':{'topLevelComment':{'id':vid,'snippet':{'textDisplay':'Should I buy this PC?', 'authorChannelId':{'value':'viewer'}}}},'replies':{'comments':[{'snippet':{'textDisplay':'Here are the specs', 'authorChannelId':{'value':'creator'}}}]}}]}
        client=Client()
        result=analyze(client,'creator',['abcdefghijk','lmnopqrstuv'])
        self.assertEqual(client.calls,5)
        self.assertEqual(result['sampleSize'],2)
        self.assertEqual(result['discussionShare'],100)
        self.assertEqual(result['creatorReplyShare'],100)
        self.assertEqual(result['repeatParticipants'],1)
        self.assertEqual(result['videoCount'],2)

    def test_no_data_not_zero_and_validation(self):
        class Client:
            def get(self,*args,**kwargs): return {'items':[]}
        self.assertIsNone(analyze(Client(),'creator',['abcdefghijk'])['discussionShare'])
        with self.assertRaises(ValueError):analyze(Client(),'creator',['bad'])
        with self.assertRaises(ValueError):analyze(Client(),'creator',['abcdefghij'+str(i) for i in range(4)])
