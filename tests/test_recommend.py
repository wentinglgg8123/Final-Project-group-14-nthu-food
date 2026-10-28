"""Regression tests for the actual Python recommendation engine and data."""
import unittest
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

from foodguide.data import load_restaurants, maps_url, is_google_maps_url, parse_favorites
from foodguide.recommend import Diner, Weights, recommend, opening_status
from foodguide.views import coins_html


class RecommendationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load_restaurants()
        cls.at = datetime(2026, 10, 28, 12)

    def test_all_original_records_and_deterministic_scores(self):
        results = recommend(self.records, [Diner()], at=self.at)
        self.assertEqual(len(results), 14)
        self.assertEqual(results, recommend(self.records, [Diner()], at=self.at))
        self.assertTrue(all(0 <= result['score'] <= 100 for result in results))
        self.assertEqual([r['score'] for r in results], sorted([r['score'] for r in results], reverse=True))

    def test_every_diners_budget_is_respected(self):
        results = recommend(self.records, [Diner(budget=2.5), Diner(budget=1)], at=self.at)
        self.assertEqual(len(results), 4)
        self.assertTrue(all(result['price'] <= 1 for result in results))

    def test_cuisine_weight_changes_top_recommendation(self):
        results = recommend(self.records, [Diner(cuisine='火鍋')], Weights(0, 100, 0))
        self.assertIn('六扇門', results[0]['name'])
        self.assertEqual(results[0]['score'], 100)
        self.assertIn('符合 1 人的料理偏好', results[0]['reasons'])

    def test_region_preference_is_not_a_travel_estimate(self):
        results = recommend(self.records, [Diner(area='清夜')], Weights(0, 0, 100))
        self.assertEqual(results[0]['location'], '清夜')
        self.assertTrue(all('walk' not in result and 'distance' not in result for result in results))
        self.assertTrue(all('分鐘' not in ' '.join(result['reasons']) for result in results))

    def test_relaxed_budget_and_zero_weights(self):
        results = recommend(self.records, [Diner(budget=1)], Weights(0, 0, 0), strict=False)
        self.assertEqual(len(results), 14)
        self.assertTrue(all(isinstance(result['score'], int) for result in results))
        with self.assertRaises(ValueError):
            Weights(-1, 1, 1).normalized()

    def test_combined_search_area_and_occasion(self):
        results = recommend(self.records, [Diner()], search='豆花', area='清夜', occasion='約會')
        self.assertEqual([result['name'] for result in results], ['立晉豆花'])
        self.assertEqual(recommend(self.records, [Diner()], search='不存在'), [])
        self.assertEqual(recommend(self.records, []), [])

    def test_sunday_and_monday_closures(self):
        self.assertEqual(opening_status(self.records[3], datetime(2026, 11, 1, 10))[0], 'closed')
        self.assertEqual(opening_status(self.records[12], datetime(2026, 11, 2, 13))[0], 'closed')

    def test_weekend_special_hours(self):
        self.assertEqual(opening_status(self.records[0], datetime(2026, 10, 31, 8))[0], 'closed')
        self.assertEqual(opening_status(self.records[0], datetime(2026, 10, 30, 8))[0], 'open')

    def test_breaks_midnight_and_unknown_hours(self):
        self.assertEqual(opening_status(self.records[6], datetime(2026, 10, 28, 14))[0], 'closed')
        self.assertEqual(opening_status(self.records[12], datetime(2026, 10, 28, 0))[0], 'closed')
        self.assertEqual(opening_status(self.records[12], datetime(2026, 10, 28, 23, 59))[0], 'open')
        self.assertEqual(opening_status(self.records[4], datetime(2026, 10, 28, 3))[0], 'open')
        self.assertEqual(opening_status(self.records[2], self.at)[0], 'unknown')
        self.assertEqual(opening_status(self.records[0], None)[0], 'unknown')

    def test_aware_datetimes_use_taiwan_timezone(self):
        # Sunday afternoon UTC is Monday midnight in Taiwan, when 豆花 is closed.
        self.assertEqual(opening_status(self.records[12], datetime(2026, 11, 1, 16, tzinfo=timezone.utc))[1], '當日公休')

    def test_open_only_excludes_unknown(self):
        results = recommend(self.records, [Diner()], at=self.at, open_only=True)
        self.assertGreater(len(results), 0)
        self.assertTrue(all(result['status'] == 'open' for result in results))
        self.assertNotIn(3, [result['id'] for result in results])

    def test_each_maps_query_contains_its_own_name_and_region(self):
        destinations = set()
        for restaurant in self.records:
            url = maps_url(restaurant)
            self.assertTrue(is_google_maps_url(url))
            query = parse_qs(urlparse(url).query)['query'][0]
            self.assertIn(restaurant['name'], query)
            self.assertIn('新竹市', query)
            self.assertIn('小吃部' if restaurant['location'] == '小吃部' else '清大夜市', query)
            destinations.add(url)
        self.assertEqual(len(destinations), 14)

    def test_optional_direct_merchant_link_and_url_validation(self):
        restaurant = {**self.records[0], 'mapsUrl': 'https://maps.app.goo.gl/example'}
        self.assertEqual(maps_url(restaurant), restaurant['mapsUrl'])
        for unsafe in ('javascript:alert(1)', 'https://google.com.evil/maps', 'https://www.google.com/search', 'http://maps.google.com'):
            self.assertFalse(is_google_maps_url(unsafe))

    def test_fractional_prices_render_full_plus_half_coins(self):
        html = coins_html(1.5)
        self.assertEqual(html.count('class="coin"'), 1)
        self.assertEqual(html.count('class="coin half"'), 1)
        self.assertIn('aria-label="1.5 個金幣"', html)
        self.assertEqual(coins_html(2).count('class="coin half"'), 0)
        self.assertEqual(coins_html(2.5).count('class="coin"'), 2)

    def test_invalid_bookmark_favorites_are_ignored(self):
        self.assertEqual(parse_favorites('1,999,x,2,1,<script>', {1, 2}), {1, 2})
