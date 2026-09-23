"""Ranking identity, failure and rewrite boundaries; no real API calls."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'integrations/jev_mac'))
from ranking import apply_scores, rank_candidates
from pipeline import analyze_snapshot, rewrite_snapshot
from core import Snapshot, parse_advice
from client import Config
from experience import ReplyPreferences
from test_jev_mac import advice


def drafts():
    data = advice()
    data['intent'] = '可能想暂缓安排'
    data['candidates'] += [dict(data['candidates'][0], text='行，那改天再聊', reason='第二条理由')]
    return data


class RankingTests(unittest.TestCase):
    def setUp(self):
        self.data = drafts()
        self.snapshot = Snapshot('A', '我：周六见吗\n对方：这周忙')
        self.config = Config('http://localhost', 'test', '')

    def test_ranking_reorders_whole_candidates_and_sums_to_100(self):
        original = copy.deepcopy(self.data['candidates'])
        rows = apply_scores(original, json.dumps({'scores': [{'id': 1, 'score': 80}, {'id': 0, 'score': 20}]}))
        self.assertEqual([row['weight'] for row in rows], [80, 20])
        self.assertEqual(rows[0]['text'], original[1]['text'])
        self.assertEqual(rows[0]['reason'], original[1]['reason'])
        self.assertNotIn('weight', original[0])
        equal = apply_scores(original + [original[0]], json.dumps({'scores': [{'id': i, 'score': 1} for i in range(3)]}))
        self.assertEqual([r['weight'] for r in equal], [34, 33, 33])

    def test_bad_identity_scores_and_nonfinite_values_rejected(self):
        invalid = ['{}', '[]', 'not json']
        for scores in ([{'id': 0, 'score': 1}] * 2,
                       [{'id': 0, 'score': 1}, {'id': 2, 'score': 5}],
                       [{'id': i, 'score': 0} for i in range(2)]):
            invalid.append(json.dumps({'scores': scores}))
        for value in (True, -1, 101, float('nan'), float('inf'), '80'):
            invalid.append(json.dumps({'scores': [{'id': 0, 'score': value}, {'id': 1, 'score': 10}]}))
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                apply_scores(self.data['candidates'], raw)

    def test_failed_ranking_retains_drafts_without_fake_weights(self):
        for response in ('bad json', ValueError('provider failed')):
            kwargs = {'side_effect': response} if isinstance(response, Exception) else {'return_value': response}
            with patch('ranking.complete', **kwargs) as scorer:
                result = rank_candidates(self.config, self.snapshot, '日常回复', '', self.data)
                self.assertEqual(result['ranking_status'], 'unavailable')
                self.assertEqual(result['candidates'], self.data['candidates'])
                scorer.assert_called_once()

    def test_zero_and_single_candidates_need_no_scoring_request(self):
        with patch('ranking.complete') as scorer:
            for n in (0, 1):
                result = rank_candidates(self.config, self.snapshot, '日常回复', '',
                                         dict(self.data, candidates=self.data['candidates'][:n]))
                self.assertEqual(result['ranking_status'], 'not_needed' if n == 0 else 'single')
                if n:
                    self.assertEqual(result['candidates'][0]['weight'], 100)
            scorer.assert_not_called()

    def test_generation_then_ranking_on_same_provider_with_context(self):
        events = []
        def generate(*args):
            events.append('generate')
            return json.dumps(self.data)
        def score(config, messages):
            events.append('rank')
            self.assertIs(config, self.config)
            payload = json.loads(messages[1]['content'])
            self.assertEqual(payload['visible_transcript'], self.snapshot.transcript)
            self.assertEqual(payload['strategy'], '降压')
            self.assertEqual(payload['user_background'], '当前对象专属背景')
            self.assertNotIn('reason', payload['candidates'][0])
            return json.dumps({'scores': [{'id': 0, 'score': 20}, {'id': 1, 'score': 80}]})
        with patch('pipeline.complete', side_effect=generate), patch('ranking.complete', side_effect=score):
            result = analyze_snapshot(self.snapshot, '日常回复', '当前对象专属背景', self.config)
        self.assertEqual(events, ['generate', 'rank'])
        self.assertEqual(result['candidates'][0]['text'], self.data['candidates'][1]['text'])

    def test_rewrite_preserves_analysis_and_does_not_call_jev(self):
        rewritten = dict(self.data, facts=['模型试图换掉事实'], recommendation='模型试图换掉建议')
        rewritten['candidates'] = [dict(self.data['candidates'][0], text='行，你先忙')]
        with patch('pipeline.complete', return_value=json.dumps(rewritten)), patch('pipeline.decide') as jev:
            result = rewrite_snapshot(self.snapshot, '日常回复', '', self.config, self.data, ReplyPreferences())
            self.assertEqual(result['facts'], self.data['facts'])
            self.assertEqual(result['intent'], self.data['intent'])
            self.assertEqual(result['recommendation'], self.data['recommendation'])
            self.assertEqual(result['candidates'][0]['text'], '行，你先忙')
            jev.assert_not_called()
        self.assertNotIn('weight', self.data['candidates'][0])

    def test_rewrite_accepts_candidate_only_json_and_ignores_unused_evidence(self):
        candidates = [dict(self.data['candidates'][0], text='行，你先忙')]
        for reply in ({'candidates': candidates},
                      {'strategy': '降压', 'facts': {'unexpected': 'shape'},
                       'candidates': candidates}):
            with self.subTest(reply=reply), patch('pipeline.complete', return_value=json.dumps(reply)):
                result = rewrite_snapshot(self.snapshot, '日常回复', '', self.config,
                                          self.data, ReplyPreferences())
                self.assertEqual(result['facts'], self.data['facts'])
                self.assertEqual(result['candidates'][0]['text'], '行，你先忙')

    def test_rewrite_rejects_strategy_change_empty_and_length_overflow(self):
        for change in ({'strategy': '约见'}, {'candidates': []},
                       {'candidates': [dict(self.data['candidates'][0], text='字'*41)]}):
            with patch('pipeline.complete', return_value=json.dumps(dict(self.data, **change))), self.assertRaises(ValueError):
                rewrite_snapshot(self.snapshot, '日常回复', '', self.config, self.data, ReplyPreferences())

    def test_invalid_intent_not_rendered(self):
        for value in ([], '', '字'*81):
            with self.assertRaises(ValueError):
                parse_advice(json.dumps(dict(self.data, intent=value)))


class IntentConfidenceTests(unittest.TestCase):
    def test_numeric_confidence_is_bounded_and_requires_an_intent_and_evidence(self):
        for value in (True, False, -0.1, 1.01, '62%', float('nan'), float('inf')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_advice(json.dumps(dict(drafts(), intent_confidence=value)))
        for change in ({'intent': ''}, {'facts': []}):
            with self.assertRaises(ValueError):
                parse_advice(json.dumps(dict(drafts(), intent_confidence=.62, **change)))
        for value in (0, .62, 1, None):
            self.assertEqual(parse_advice(json.dumps(dict(drafts(), intent_confidence=value)))['intent_confidence'], value)

    def test_unknown_confidence_is_not_rendered_as_zero(self):
        from core import intent_confidence_label
        self.assertIn('暂无法判断', intent_confidence_label(drafts()))
        self.assertIn('暂无法判断', intent_confidence_label(dict(drafts(), intent_confidence=None)))
        self.assertIn('62%', intent_confidence_label(dict(drafts(), intent_confidence=.62)))
        self.assertIn('0%', intent_confidence_label(dict(drafts(), intent_confidence=0)))

    def test_rewrite_cannot_replace_intent_confidence(self):
        previous = dict(drafts(), intent_confidence=.62)
        changed = dict(previous, intent_confidence=.99, candidates=previous['candidates'][:1])
        with patch('pipeline.complete', return_value=json.dumps(changed)):
            result = rewrite_snapshot(Snapshot('A','我：周六见吗\n对方：这周忙'), '日常回复', '',
                                      Config('http://localhost','test',''), previous, ReplyPreferences())
        self.assertEqual(result['intent_confidence'], .62)
