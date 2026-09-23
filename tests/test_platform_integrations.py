import unittest
from unittest.mock import patch

from integrations.jev_windows.core.goutou import brief, explicit_boundary
from integrations.jev_windows.core.engine import analyze
from integrations.jev_windows.core.jev_client import JevError


class WindowsGoutouContractTest(unittest.TestCase):
    def test_no_contact_request_stops_before_any_model_call(self):
        messages = [("me", "晚点聊？"), ("her", "请不要联系我")]
        with patch("integrations.jev_windows.core.engine.ask", side_effect=AssertionError("called")):
            result = analyze(messages, "朋友")
        self.assertEqual(result["candidates"], [])
        self.assertIsNone(result["best_reply"])
        self.assertIn("停止", result["goutou"]["action"])

    def test_only_latest_other_message_triggers_boundary(self):
        self.assertFalse(explicit_boundary([("her", "请不要联系我"), ("me", "好")]))
        self.assertTrue(explicit_boundary([("me", "好"), ("her", "请不要联系我")]))

    def test_evidence_and_confidence_keep_their_limits(self):
        result = brief([("her", "下周再说吧")], {
            "true_intent": {"choice": "request_action", "confidence": .62},
            "best_action": {"choice": "say_less"},
        })
        self.assertEqual(result["intent_confidence"], .62)
        self.assertIn("对方：「下周再说吧」", result["facts"])
        self.assertIn("不是对方真实意图概率", result["evidence_note"])

    def test_failed_judgment_does_not_draft_blindly(self):
        messages = [("me", "周六看展吗"), ("her", "下周再说吧")]
        with patch("integrations.jev_windows.core.engine.ask", side_effect=JevError("判断接口失败")):
            with patch("integrations.jev_windows.core.engine.draft_candidates",
                       side_effect=AssertionError("should not draft")):
                with self.assertRaises(JevError):
                    analyze(messages, "朋友")


if __name__ == "__main__":
    unittest.main()
