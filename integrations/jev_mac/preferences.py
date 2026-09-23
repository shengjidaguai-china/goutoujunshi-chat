"""Persist display/model preferences only; no keys, chat or relationship text."""
import json
import os
from pathlib import Path

PATH = Path(__file__).with_name("settings.local.json")
OCR_METHODS = ('vision', 'deepseek')


def load(path=PATH):
    try:
        data = json.loads(path.read_text())
        if (not isinstance(data, dict) or not isinstance(data.get("model"), str)
                or not isinstance(data.get("base"), str) or len(data["model"]) > 160
                or isinstance(data.get("opacity"), bool)
                or not isinstance(data.get("opacity"), (float, int))
                or not 55 <= data["opacity"] <= 100):
            return {}
        from experience import ReplyPreferences
        options = data.get('reply', {})
        reply = ReplyPreferences(**options)
        result = {key: data[key] for key in ("model", "base", "opacity")}
        ocr_method = data.get('ocr_method', 'vision')
        if ocr_method not in OCR_METHODS:
            return {}
        result['ocr_method'] = ocr_method
        if options:
            result['reply'] = {'tone': reply.tone, 'length': reply.length, 'count': reply.count}
        return result
    except (OSError, ValueError, TypeError):
        return {}


def save(model, base, opacity, path=PATH, reply=None, ocr_method='vision'):
    if ocr_method not in OCR_METHODS:
        raise ValueError('请选择有效的 OCR 识别方式')
    temporary = path.with_suffix(".tmp")
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            data = {"model": model, "base": base, "opacity": opacity,
                    "ocr_method": ocr_method}
            if reply:
                data['reply'] = {'tone': reply.tone, 'length': reply.length, 'count': reply.count}
            json.dump(data, stream)
        os.replace(temporary, path)
    except OSError:
        raise ValueError("无法保存设置，请检查目录写入权限") from None
