"""Dutch-market screening regressions using synthetic public metadata."""
import unittest

from regional_screening import clean_hardware_text, detect_creator_market, screen_candidate


def uploads(language, description=''):
    return [dict(id=str(i), title='RTX gaming PC build', description=description,
                 recentUpload=True, publishedAt=f'2026-09-2{i}T12:00:00Z',
                 audioLanguage=language, metadataLanguage=language) for i in range(3)]


class DutchScreeningTests(unittest.TestCase):
    def test_jargon_is_not_english_evidence(self):
        self.assertEqual(clean_hardware_text('RTX GPU gaming PC build: de beste voor jou'), ': de beste voor jou')
        result = screen_candidate('NL', 'NL', None, '', uploads(None), 'nl')
        self.assertEqual((result['eligibility'], result['market_match_tier']), ('review', 3))

    def test_direct_dutch_match(self):
        result = screen_candidate('NL', 'NL', 'nl', '', uploads('nl'), 'nl')
        self.assertEqual((result['eligibility'], result['market_match_tier']), ('match', 1))

    def test_english_dutch_local_requires_secondary_evidence(self):
        videos = uploads('en', 'Parts: https://www.megekko.nl/product/1')
        result = screen_candidate('NL', 'NL', 'en', '', videos, 'nl')
        self.assertEqual((result['eligibility'], result['market_match_tier']), ('match', 2))
        self.assertTrue(any('megekko.nl' in x for x in result['local_market_evidence']))
        self.assertEqual(screen_candidate('NL', 'NL', 'en', '', uploads('en'), 'nl')['eligibility'], 'review')
        self.assertTrue(detect_creator_market('NL', 'NL', 'Dutch creator in Amsterdam', []))

    def test_foreign_country_never_passes_via_dutch_links(self):
        for country in ('US', 'GB'):
            result = screen_candidate('NL', country, 'en', 'Dutch', uploads('en', 'https://megekko.nl'), 'nl')
            self.assertEqual(result['eligibility'], 'excluded')
            self.assertIn(country, result['failure_reasons'][0])

    def test_same_rules_cover_all_non_english_campaign_markets(self):
        fixtures={'FI':('fi','https://jimms.fi/pc'),'SE':('sv','https://inet.se/pc'),
                  'EE':('et','https://arvutitark.ee/pc'),'DE':('de','https://mindfactory.de/pc'),
                  'FR':('fr','https://materiel.net/pc'),'HU':('hu','https://ipon.hu/pc')}
        for market,(native,retailer) in fixtures.items():
            with self.subTest(market=market):
                direct=screen_candidate(market,market,native,'',uploads(native),native)
                self.assertEqual((direct['eligibility'],direct['market_match_tier']),('match',1))
                local=screen_candidate(market,market,'en','',uploads('en',retailer),native)
                self.assertEqual((local['eligibility'],local['market_match_tier']),('match',2))
                self.assertTrue(local['is_lingua_franca'])
                foreign=screen_candidate(market,'US','en','',uploads('en',retailer),native)
                self.assertEqual(foreign['reason_code'],'EXCLUDED_FOREIGN_LEAKAGE')


if __name__ == '__main__':
    unittest.main()
