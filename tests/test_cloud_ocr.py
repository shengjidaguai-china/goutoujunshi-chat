"""Offline checks for the opt-in image OCR boundary."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'integrations' / 'jev_mac'))

from client import Config
from core import Snapshot, assert_fill_target, from_capture
from cloud_ocr import deepseek_config, parse_transcription, read_conversation
import cloud_ocr


class CloudOcrTests(unittest.TestCase):
    def setUp(self):
        cloud_ocr._last_read = None
        self.config = Config('https://api.deepseek.com', 'deepseek-flash', 'test-secret')
        self.window = {'wid': 17, 'title': '微信', 'w': 800, 'h': 600, 'x': 0, 'y': 0}

    def test_only_official_deepseek_key_and_flash_are_used(self):
        with patch('cloud_ocr.Config.from_env', return_value=Config('https://other.test', 'm', 'other-secret')):
            with self.assertRaisesRegex(ValueError, '官方 DeepSeek'):
                deepseek_config()
        with patch('cloud_ocr.Config.from_env', return_value=Config('https://api.deepseek.com', 'other', 'own-secret')):
            selected = deepseek_config()
            self.assertEqual((selected.base, selected.model, selected.key),
                             ('https://api.deepseek.com', 'deepseek-flash', 'own-secret'))

    def test_cloud_capture_sends_only_cropped_image_and_caches_unchanged_periodic_frame(self):
        answer = json.dumps({'chat_title': '小 A', 'messages': [
            {'side': 'them', 'text': '今天有点忙', 'uncertain': False}]})
        with patch('cloud_ocr._capture_window', return_value=(self.window, b'fake cropped png')), \
                patch('cloud_ocr.complete', return_value=answer) as complete:
            first = read_conversation(self.config)
            second = read_conversation(self.config, reuse_unchanged=True)
        self.assertIs(first, second)
        self.assertEqual(complete.call_count, 1)
        self.assertEqual(complete.call_args.args[0].model, 'deepseek-flash')
        messages = complete.call_args.args[1]
        image = messages[1]['content'][1]
        self.assertEqual(image['type'], 'image_url')
        self.assertTrue(image['image_url']['url'].startswith('data:image/png;base64,'))
        self.assertNotIn('fake cropped png', str(messages))
        self.assertEqual(first['messages'][0].side, 'them')

    def test_uncertain_and_unknown_lines_require_review(self):
        result = parse_transcription(json.dumps({'chat_title': 'A\nB', 'messages': [
            {'side': 'unknown', 'text': '你好\n世界', 'uncertain': False}]}), self.window)
        snapshot = from_capture(result, source='deepseek_ocr')
        self.assertEqual(snapshot.title, 'A B')
        self.assertIn('说话人待确认：你好 世界 [OCR待核对]', snapshot.transcript)
        with self.assertRaisesRegex(ValueError, '待核对'):
            from core import build_messages
            build_messages(snapshot, '日常回复', '')

    def test_bad_shapes_fail_and_deepseek_fill_requires_same_snapshot(self):
        invalid = [
            {'chat_title': 'A', 'messages': []},
            {'chat_title': 'A', 'messages': [{'side': 'them', 'text': '你好'}]},
            {'chat_title': 'A', 'messages': [{'side': 'other', 'text': '你好', 'uncertain': False}]},
            {'chat_title': 'A', 'messages': [{'side': 'them', 'text': '你好', 'uncertain': 'false'}]},
        ]
        for bad in invalid:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse_transcription(json.dumps(bad), self.window)
        original = Snapshot('A', '对方：你好', 17, 'deepseek_ocr')
        assert_fill_target(original, original)
        for changed in (Snapshot('A', '对方：再见', 17, 'deepseek_ocr'),
                        Snapshot('A', '对方：你好', 18, 'deepseek_ocr'),
                        Snapshot('A', '对方：你好', 17, 'ocr')):
            with self.assertRaises(ValueError):
                assert_fill_target(original, changed)


if __name__ == '__main__':
    unittest.main()
