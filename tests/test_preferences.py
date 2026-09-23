import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "integrations" / "jev_mac"))
import preferences


class PreferenceTests(unittest.TestCase):
    def test_round_trip_contains_no_chat_or_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            preferences.save("deepseek-flash", "https://api.deepseek.com", 80, path)
            data = preferences.load(path)
            self.assertEqual(set(data), {"model", "base", "opacity", "ocr_method"})
            self.assertEqual(data["opacity"], 80)
            self.assertEqual(data["model"], "deepseek-flash")
            self.assertEqual(data['ocr_method'], 'vision')

    def test_deepseek_ocr_choice_persists_without_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'settings.json'
            preferences.save('deepseek-flash', 'https://api.deepseek.com', 92, path,
                             ocr_method='deepseek')
            self.assertEqual(preferences.load(path)['ocr_method'], 'deepseek')
            self.assertNotIn('key', path.read_text())

    def test_corrupt_settings_use_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            self.assertEqual(preferences.load(path), {})
            for data in ("broken", "[]", json.dumps({"model": "m", "base": "b", "opacity": 0})):
                path.write_text(data)
                self.assertEqual(preferences.load(path), {})

    def test_unrecognized_fields_are_not_loaded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text(json.dumps({"model": "m", "base": "b", "opacity": 92, "background": "private"}))
            self.assertNotIn("background", preferences.load(path))
