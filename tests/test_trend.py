"""Timestamped CSV trend candles stay evidence-based and local."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'integrations' / 'jev_mac'))
from trend import demo_cases, load_csv, load_demo


class TrendTests(unittest.TestCase):
    def csv(self, text):
        temp = tempfile.TemporaryDirectory()
        path = Path(temp.name) / 'chat.csv'
        path.write_text(text, encoding='utf-8')
        self.addCleanup(temp.cleanup)
        return path

    def test_candles_are_message_balance_not_relationship_probability(self):
        path = self.csv('timestamp,sender,message,event\n'
                        '2026-08-01 10:00:00,me,早,\n'
                        '2026-08-01 10:01:00,other,早上好,主动接话\n'
                        '2026-08-01 10:02:00,other,今天有空吗,\n'
                        '2026-08-03 12:00:00,me,周末见,\n')
        trend = load_csv(path)
        self.assertEqual(trend.messages, 4)
        self.assertEqual(len(trend.candles), 2)
        first, last = trend.candles
        self.assertEqual((first.open, first.high, first.low, first.close), (0, 1, -1, 1))
        self.assertEqual((first.mine, first.other, first.events), (1, 2, ('主动接话',)))
        self.assertEqual((last.open, last.high, last.low, last.close), (1, 1, 0, 0))

    def test_ambiguous_speaker_and_unsorted_time_are_rejected(self):
        for data, message in (
            ('2026-08-01 10:00:00,unknown,你好\n', 'sender'),
            ('2026-08-02 10:00:00,me,你好\n2026-08-01 10:00:00,other,你好\n', '升序'),
        ):
            with self.subTest(data=data):
                path = self.csv('timestamp,sender,message\n' + data)
                with self.assertRaisesRegex(ValueError, message):
                    load_csv(path)

    def test_demo_cases_use_existing_synthetic_chat_records(self):
        cases = demo_cases()
        self.assertEqual(len(cases), 5)
        for case_id, _ in cases:
            with self.subTest(case_id=case_id):
                trend = load_demo(case_id)
                self.assertTrue(trend.messages > 0)
                self.assertTrue(trend.candles)
                self.assertIn('合成示例', trend.title)
                self.assertEqual(trend.metric, 'synthetic_event_index')
                self.assertTrue(all(0 <= c.low <= c.high <= 100 for c in trend.candles))
                self.assertTrue(any(c.events for c in trend.candles))

    def test_missing_columns_or_bad_time_fail_without_guessing(self):
        for body, message in (
            ('when,sender,message\n2026-08-01,me,你好\n', '三列'),
            ('timestamp,sender,message\nyesterday,me,你好\n', 'timestamp'),
        ):
            with self.subTest(body=body):
                with self.assertRaisesRegex(ValueError, message):
                    load_csv(self.csv(body))


if __name__ == '__main__':
    unittest.main()
