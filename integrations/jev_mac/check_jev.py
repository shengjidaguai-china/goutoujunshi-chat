"""Explicit live smoke test with synthetic messages only; no chat-model call."""
import json
import sys

from core import Snapshot
from jev import JevConfig, decide


def main():
    try:
        config = JevConfig.optional()
        if config is None:
            raise ValueError("尚未配置 Jev Key，请保存到项目专用钥匙串或设置 GOUTOU_JEV_API_KEY")
        result = decide(config, Snapshot("合成测试", "我：这周六要不要一起去看展？\n对方：这周有点忙，下周再看看吧。"),
                        "邀约推进", "仅测试策略选择，不发送消息。")
        print(json.dumps({"ok": True, "model": result.model, "strategy": result.strategy,
                          "confidence": result.confidence, "data": "synthetic only"}, ensure_ascii=False))
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
