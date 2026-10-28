"""Native Streamlit interactions, including widget reruns and reset callbacks."""
import runpy
import subprocess
import sys
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class DeploymentTest(unittest.TestCase):
    def app(self):
        app = AppTest.from_file(str(ROOT / 'streamlit_app.py')).run()
        self.assertEqual(len(app.exception), 0)
        return app

    def test_import_tool_is_safe_to_import_without_arguments(self):
        module = runpy.run_path(str(ROOT / 'scripts/import-restaurants.py'))
        self.assertTrue(callable(module['import_restaurants']))

    def test_missing_file_shows_usage_not_index_error(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/import-restaurants.py')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('usage:', result.stderr)
        self.assertNotIn('IndexError', result.stderr)

    def test_native_app_has_all_restaurants_without_iframe(self):
        app = self.app()
        self.assertEqual(len(app.get('iframe')), 0)
        self.assertEqual(len(app.error), 0)
        self.assertIn('14 間餐廳', ' '.join(element.value for element in app.caption))
        self.assertEqual(len(app.get('link_button')), 14)

    def test_diners_budget_search_and_remove(self):
        app = self.app()
        app.button(key='add_diner').click().run()
        self.assertEqual(app.session_state['diners'], [1, 2])
        app.selectbox(key='diner_2_budget').select(1.0).run()
        self.assertIn('4 間餐廳', ' '.join(element.value for element in app.caption))
        app.text_input(key='search').set_value('咖哩').run()
        self.assertTrue(any('沒有符合' in element.value for element in app.info))
        app.button(key='diner_2_remove').click().run()
        self.assertEqual(app.session_state['diners'], [1])
        self.assertIn('1 間餐廳', ' '.join(element.value for element in app.caption))
        self.assertEqual(len(app.exception), 0)

    def test_favorites_database_and_reset(self):
        app = self.app()
        app.button(key='favorite_1').click().run()
        self.assertEqual(app.session_state['favorites'], {1})
        self.assertEqual(app.query_params['favorites'], '1')
        app.radio(key='view').set_value('我的收藏').run()
        self.assertIn('1 間餐廳', ' '.join(element.value for element in app.caption))
        app.text_input(key='search').set_value('沒有這間店').run()
        app.radio(key='view').set_value('餐廳資料庫').run()
        self.assertIn('14 間餐廳', ' '.join(element.value for element in app.caption))
        app.button(key='reset').click().run()
        self.assertEqual(app.session_state['favorites'], {1})
        self.assertEqual(app.session_state['search'], '')
        self.assertEqual(app.session_state['view'], '探索美食')
        self.assertEqual(len(app.exception), 0)

    def test_dialog_opens_for_the_selected_restaurant(self):
        app = self.app()
        app.button(key='detail_9').click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any('好富' in element.value for element in app.subheader))
        links = app.get('link_button')
        self.assertTrue(any(link.key == 'detail-map' for link in links))


if __name__ == '__main__':
    unittest.main()
