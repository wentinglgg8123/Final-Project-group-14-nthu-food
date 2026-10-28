"""Run with: python -m unittest discover -s tests -p 'test_*.py'."""
import runpy
import subprocess
import sys
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class DeploymentTest(unittest.TestCase):
    def test_import_tool_is_safe_to_import_without_arguments(self):
        module = runpy.run_path(str(ROOT / 'scripts/import-restaurants.py'))
        self.assertTrue(callable(module['import_restaurants']))

    def test_missing_file_shows_usage_not_index_error(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / 'scripts/import-restaurants.py')],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn('usage:', result.stderr)
        self.assertNotIn('IndexError', result.stderr)

    def test_streamlit_entry_renders_bundled_website(self):
        app = AppTest.from_file(str(ROOT / 'streamlit_app.py')).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.error), 0)
        self.assertEqual(len(app.get('iframe')), 1)
        html = app.get('iframe')[0].proto.srcdoc
        self.assertIn('清食指南', html)
        self.assertIn('包子商行', html)
        self.assertNotIn('src="/src/main.js"', html)
        self.assertNotIn('src="/assets/', html)


if __name__ == '__main__':
    unittest.main()
