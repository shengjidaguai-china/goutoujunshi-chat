"""Explicit OpenAI-compatible route. No shared key, fallback provider, or telemetry."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

DEEPSEEK_BASE = "https://api.deepseek.com"
DEEPSEEK_BASES = (DEEPSEEK_BASE, DEEPSEEK_BASE + "/v1")
DEEPSEEK_MODEL = "deepseek-flash"
KEYCHAIN_SERVICE = "ai.goutoujunshi.deepseek"


def read_deepseek_keychain():
    if sys.platform != "darwin":
        return ""
    try:
        result = subprocess.run(
            ["/usr/bin/security", "find-generic-password", "-a", "default", "-s", KEYCHAIN_SERVICE, "-w"],
            capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise ValueError("无法读取 DeepSeek 钥匙串条目") from None
    if result.returncode == 44:
        return ""
    if result.returncode:
        raise ValueError("DeepSeek 钥匙串访问失败")
    return result.stdout.strip()


@dataclass(frozen=True)
class Config:
    base: str
    model: str
    key: str = field(repr=False)

    @classmethod
    def from_env(cls):
        # Dedicated variables deliberately do not inherit unrelated credentials.
        base = os.environ.get("GOUTOU_API_BASE", "").strip().rstrip("/")
        model = os.environ.get("GOUTOU_MODEL", "").strip()
        key = os.environ.get("GOUTOU_API_KEY", "").strip()
        # A stored provider key is bound to its exact official route. Partial
        # generic overrides must never silently inherit this credential.
        if not any(name in os.environ for name in ("GOUTOU_API_BASE", "GOUTOU_MODEL", "GOUTOU_API_KEY")):
            key = read_deepseek_keychain()
            if key:
                base, model = DEEPSEEK_BASE, DEEPSEEK_MODEL
        elif base in DEEPSEEK_BASES:
            model = model or DEEPSEEK_MODEL
            key = key or read_deepseek_keychain()
        parts = urllib.parse.urlsplit(base)
        local = parts.hostname in ("localhost", "127.0.0.1", "::1")
        if not base or not model or not parts.hostname:
            raise ValueError("请设置 GOUTOU_API_BASE 和 GOUTOU_MODEL；不会使用默认第三方中转")
        if parts.username or parts.password or parts.query or parts.fragment:
            raise ValueError("接口地址不能含账号、密码、查询参数或片段")
        if parts.scheme != "https" and not (parts.scheme == "http" and local):
            raise ValueError("远程接口必须使用 HTTPS；HTTP 仅允许本机服务")
        if not key and not local:
            raise ValueError("请设置 GOUTOU_API_KEY")
        return cls(base, model, key)

    @property
    def endpoint(self):
        return self.base + "/chat/completions"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward a chat or bearer token to another host.


def complete(config, messages):
    body = {"model": config.model, "messages": messages, "temperature": .6,
            "max_tokens": 2500, "stream": False}
    if config.base in DEEPSEEK_BASES:
        body.update(thinking={"type": "disabled"}, response_format={"type": "json_object"})
    headers = {"Content-Type": "application/json"}
    if config.key:
        headers["Authorization"] = "Bearer " + config.key
    request = urllib.request.Request(config.endpoint,
                                     data=json.dumps(body, ensure_ascii=False).encode(),
                                     headers=headers, method="POST")
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=60) as response:
            raw = response.read(256 * 1024 + 1)
        if len(raw) > 256 * 1024:
            raise ValueError("模型响应过大")
        data = json.loads(raw)
        if data["choices"][0].get("finish_reason") not in (None, "stop"):
            raise ValueError("模型未完整生成回复；未展示候选，请重试")
        content = data["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError("模型返回空内容；请检查模型是否支持普通文本输出")
        return content
    except urllib.error.HTTPError as error:
        # Provider error bodies may echo user text or credentials: never display them.
        raise ValueError(f"模型接口 HTTP {error.code}；请检查配置和额度") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ValueError("模型接口连接失败或超时，请检查网络和地址") from None
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        raise ValueError("接口响应不是预期的聊天模型格式") from None
