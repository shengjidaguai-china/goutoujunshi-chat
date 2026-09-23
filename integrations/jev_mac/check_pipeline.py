"""Explicit live Jev + reply-model check using synthetic dialogue only."""
import json
import sys
import time

from client import Config
from core import Snapshot
from jev import JevConfig
from pipeline import analyze_snapshot
from experience import ReplyPreferences, empty_profile, profile_context


def main():
    try:
        reply = Config.from_env()
        jev = JevConfig.optional()
        if jev is None:
            raise ValueError("完整链路测试需要配置 Jev")
        started = time.monotonic()
        options = ReplyPreferences('直接', '简短', 2)
        profile = empty_profile('合成对象')
        profile.update(stage='了解中', goal='主动邀约', background='仅测试，不发送消息。')
        result = analyze_snapshot(
            Snapshot("合成测试", "我：这周六要不要一起去看展？\n对方：这周有点忙，下周再看看吧。"),
            "邀约推进", profile_context(profile), reply, jev, options)
        print(json.dumps({"ok": True, "reply_model_requested": reply.model,
                          "jev": result["jev_decision"], "strategy": result["strategy"],
                          "candidates": result["candidates"], "data": "synthetic only",
                          "intent": result.get("intent"), "intent_confidence": result.get("intent_confidence"),
                          "ranking_status": result.get("ranking_status"),
                          "reply_preferences": options.as_dict(),
                          "seconds": round(time.monotonic() - started, 1)}, ensure_ascii=False))
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
