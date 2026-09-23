"""Write only the two project-specific API keys to the macOS login Keychain.

The password is sent to ``security`` over stdin, never as a process argument,
printed message, plaintext settings file, or repository file.
"""
from __future__ import annotations

import subprocess
import sys

from client import KEYCHAIN_SERVICE as DEEPSEEK_SERVICE
from jev import KEYCHAIN_SERVICE as JEV_SERVICE


SERVICES = {'deepseek': DEEPSEEK_SERVICE, 'jev': JEV_SERVICE}
SECURITY = '/usr/bin/security'


def _service(provider: str) -> str:
    try:
        return SERVICES[provider]
    except (KeyError, TypeError):
        raise ValueError('只允许配置本项目的 DeepSeek 或 Jev 密钥') from None


def _run(args: list[str], *, input_text: str | None = None) -> int:
    try:
        result = subprocess.run([SECURITY, *args], input=input_text, text=True,
                                capture_output=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise ValueError('Mac 钥匙串操作失败或超时，请检查登录钥匙串') from None
    return result.returncode


def save_key(provider: str, value: str) -> None:
    service = _service(provider)
    if sys.platform != 'darwin':
        raise ValueError('可视化密钥配置仅支持 macOS')
    if not isinstance(value, str) or not 1 <= len(value) <= 4096 or any(
            ord(char) < 33 or ord(char) > 126 for char in value):
        raise ValueError('密钥须为不含空格或换行的有效文本')
    # With -w last, security reads and confirms the password from stdin. The
    # two identical lines cover both new entries and updates without exposing
    # the password in process listings or shell history.
    status = _run(['add-generic-password', '-a', 'default', '-s', service, '-U', '-w'],
                  input_text=value + '\n' + value + '\n')
    if status:
        raise ValueError('密钥未能保存到 Mac 钥匙串，请检查钥匙串权限')


def delete_key(provider: str) -> None:
    service = _service(provider)
    if sys.platform != 'darwin':
        raise ValueError('可视化密钥配置仅支持 macOS')
    status = _run(['delete-generic-password', '-a', 'default', '-s', service])
    if status not in (0, 44):  # 44: the entry is already absent.
        raise ValueError('无法从 Mac 钥匙串移除密钥，请检查钥匙串权限')
