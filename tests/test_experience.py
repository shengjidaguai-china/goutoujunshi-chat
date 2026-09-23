import copy
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'integrations' / 'jev_mac'))
from experience import AutoGate, Conversations, ReplyPreferences, empty_profile, validate_profile, profile_context
from core import Snapshot
from client import Config
from pipeline import analyze_snapshot
from memory_bridge import MemoryBridge
from test_jev_mac import advice


class ExperienceTests(unittest.TestCase):
    def test_objects_do_not_share_context_and_explicit_rebinding(self):
        conversations = Conversations()
        a, b = Snapshot('A', '对方：你好', 1, 'ocr'), Snapshot('B', '对方：你好', 1, 'ocr')
        profile = conversations.select(a)
        profile['background'] = 'A 独有背景'
        conversations.update(profile)
        identity = profile['id']
        self.assertEqual(conversations.select(b)['background'], '')
        self.assertEqual(conversations.select(a)['background'], 'A 独有背景')
        conversations.select(b)
        conversations.bind(identity)
        self.assertEqual(conversations.select(b)['background'], 'A 独有背景')
        self.assertEqual(conversations.select(Snapshot('A', '对方：你好', 2, 'ocr'))['background'], '')

    def test_profile_validation_and_no_ids_in_model_context(self):
        profile = empty_profile('A')
        for score in ('-1', '101', 'not a score'):
            with self.assertRaises(ValueError):
                validate_profile(dict(profile, my_score=score))
        self.assertNotIn(profile['id'], profile_context(profile))

    def test_automatic_gate_scope_stability_direction_and_deduplication(self):
        gate = AutoGate()
        a = Snapshot('A', '对方：你好', 1, 'ocr')
        self.assertFalse(gate.ready(a, 0))
        with self.assertRaises(ValueError):
            gate.configure(True, None)
        gate.configure(True, (1, 'A'))
        self.assertFalse(gate.ready(Snapshot('B', a.transcript, 1, 'ocr'), 0))
        self.assertFalse(gate.ready(a, 1))
        self.assertFalse(gate.ready(a, 2))
        self.assertTrue(gate.ready(a, 3))
        self.assertFalse(gate.ready(a, 30))
        for text in ('我：你好', '说话人待确认：你好', '对方：你好 [OCR待核对]'):
            self.assertFalse(gate.ready(Snapshot('A', text, 1, 'ocr'), 40))
            self.assertFalse(gate.ready(Snapshot('A', text, 1, 'ocr'), 43))
        gate.configure(False, None)
        self.assertFalse(gate.ready(a, 100))
        gate.configure(True, (1, 'A'), a.identity)
        self.assertFalse(gate.ready(a, 101))
        self.assertFalse(gate.ready(a, 104))

    def test_reply_preferences_are_in_request_and_enforced(self):
        config = Config('http://localhost', 'test', '')
        options = ReplyPreferences('直接', '简短', 1)
        data = advice()
        with patch('pipeline.complete', return_value=json.dumps(data)) as complete:
            analyze_snapshot(Snapshot('A', '对方：你好'), '日常回复', '', config, preferences=options)
            prompt = complete.call_args[0][1][0]['content']
            self.assertIn('直接', prompt)
            self.assertIn('最多 40 字', prompt)
        for change in ({'candidates': data['candidates']*2}, {'candidates': [dict(data['candidates'][0], text='字'*41)]}):
            output = dict(data, **change)
            with patch('pipeline.complete', return_value=json.dumps(output)), self.assertRaises(ValueError):
                analyze_snapshot(Snapshot('A', '对方：你好'), '日常回复', '', config, preferences=options)

    def test_only_uncertain_text_never_reaches_either_model(self):
        for transcript in ('说话人待确认：那就周六老地方 [OCR待核对]',
                           '我：周六？ [OCR待核对]\n对方：好 [OCR待核对]'):
            with patch('pipeline.complete') as writer, patch('pipeline.decide') as decider:
                with self.assertRaisesRegex(ValueError, '全部待核对'):
                    analyze_snapshot(Snapshot('A', transcript), '日常回复', '',
                                     Config('http://localhost', 'test', ''), jev_config=object())
                writer.assert_not_called()
                decider.assert_not_called()

    def test_unknown_speaker_does_not_discard_other_reliable_context(self):
        data = advice()
        with patch('pipeline.complete', return_value=json.dumps(data)):
            result = analyze_snapshot(Snapshot('A', '说话人待确认：早\n对方：今天没空'),
                                      '日常回复', '', Config('http://localhost', 'test', ''))
            self.assertEqual(result['candidates'][0]['text'], data['candidates'][0]['text'])


class ArchiveTests(unittest.TestCase):
    def test_consent_pause_save_recall_undo_and_delete_in_isolated_store(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = MemoryBridge(env=dict(os.environ, GOUTOUJUNSHI_MEMORY_DIR=directory))
            profile = empty_profile('测试对象')
            profile['background'] = '测试背景'
            self.assertEqual(memory.save_profile(profile), 0)
            self.assertFalse((Path(directory)/'memory.sqlite3').exists())
            memory.call('enable', '--confirm')
            self.assertGreater(memory.save_profile(profile), 0)
            self.assertEqual(memory.load_profile(profile['id'])['background'], '测试背景')
            self.assertEqual(memory.save_profile(profile), 0)
            profile['background'] = '更新背景'
            self.assertEqual(memory.save_profile(profile), 1)
            memory.undo_save()
            self.assertEqual(memory.load_profile(profile['id'])['background'], '测试背景')
            memory.call('pause')
            self.assertEqual(memory.save_profile(profile), 0)
            self.assertEqual(memory.list_profiles(), [])
            memory.call('resume')
            profile['background'] = ''
            memory.save_profile(profile)
            self.assertEqual(memory.load_profile(profile['id'])['background'], '')
            memory.call('forget-object', profile['id'], '--confirm')
            self.assertEqual(memory.list_profiles(), [])
            memory.call('revoke', '--confirm')
            self.assertFalse(memory.active())
