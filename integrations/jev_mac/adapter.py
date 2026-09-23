"""macOS window capture and accessibility draft filling; no WeChat private APIs."""
from __future__ import annotations

from core import assert_fill_target, from_capture
from vendor import perception, fill


def capture(method='vision', reuse_unchanged=False):
    if not perception.screen_capture_ok():
        raise ValueError("请在系统设置中给启动终端屏幕录制权限，退出并重新启动后再读取")
    if method == 'vision':
        result = perception.read_conversation(max_messages=20)
        source = 'ocr'
    elif method == 'deepseek':
        from cloud_ocr import deepseek_config, read_conversation
        result = read_conversation(deepseek_config(), max_messages=20,
                                   reuse_unchanged=reuse_unchanged)
        source = 'deepseek_ocr'
    else:
        raise ValueError('请选择有效的 OCR 识别方式')
    return from_capture(result, source=source), result.get("window")


def fill_reply(original, text):
    method = 'deepseek' if original.source == 'deepseek_ocr' else 'vision'
    current, window = capture(method=method)
    assert_fill_target(original, current)
    if not fill.has_accessibility():
        raise ValueError("请先授予启动终端辅助功能权限，或使用复制后手动粘贴")
    target = fill.locate_input(window)
    if target.get("box") is None:
        raise ValueError("微信未开放可验证的输入控件，请复制后手动粘贴")
    # Only a macOS accessibility text control, never synthetic keystrokes/send.
    ok, reason = fill.fill_text(text, target=target)
    if not ok:
        raise ValueError(reason)
    return "已填入微信草稿，请核对接收人和内容后自行发送"
