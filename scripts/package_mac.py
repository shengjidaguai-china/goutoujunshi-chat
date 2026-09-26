#!/usr/bin/env python3
"""Build a clean Mac source ZIP with one-click setup and launch scripts."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "goutoujunshi-jev-chat-mac"
FILES = ("README.md", "PRIVACY.md", "LICENSE", "SKILL.md", "scripts/memory_store.py")
DIRS = ("integrations/jev_mac", "references", "examples/relationship_cases", "assets", "agents", "documentation")
EXCLUDED = {".venv", "__pycache__", ".DS_Store", "settings.local.json", "settings.local.tmp"}

INSTALL = """#!/bin/zsh
set -eu
cd "$(dirname "$0")/integrations/jev_mac"
if ! command -v uv >/dev/null 2>&1; then
  print '请先安装 uv：https://docs.astral.sh/uv/getting-started/installation/'
  exit 1
fi
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
print '依赖安装完成。双击「启动.command」打开狗头军师。'
"""
START = """#!/bin/zsh
set -eu
cd "$(dirname "$0")/integrations/jev_mac"
exec /bin/zsh ./start.command "$@"
"""
DEMO = """#!/bin/zsh
set -eu
cd "$(dirname "$0")/integrations/jev_mac"
exec /bin/zsh ./start.command --demo
"""
INTRO = """# 狗头军师 Jev Chat · Mac 预览包

这是 macOS 源码预览包，包含完整的狗头军师规则、关系案例和桌面悬浮窗。它不是签名或公证的 .app，首次使用需要安装 Python 3.12 与 uv。

1. 双击「安装依赖.command」。依赖只装入包内的 `integrations/jev_mac/.venv`。
2. 双击「离线演示.command」确认界面可以打开；演示不读取微信也不调用模型。
3. 双击「启动.command」，进入设置页填写自己的模型密钥。读取微信需给启动程序的终端屏幕录制权限；填入草稿还需辅助功能权限。

你的个人聊天、设置和密钥不包含在此包中。数据使用见 `PRIVACY.md`；完整功能及限制见 `integrations/jev_mac/README.md`。
"""


def add_bytes(archive: ZipFile, name: str, content: bytes, mode: int = 0o644) -> None:
    info = ZipInfo(f"{PREFIX}/{name}", (2026, 1, 1, 0, 0, 0))
    info.compress_type = ZIP_DEFLATED
    info.external_attr = (0o100000 | mode) << 16
    archive.writestr(info, content)


def build(output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest: list[str] = []
    with ZipFile(output, "w") as archive:
        paths = [ROOT / name for name in FILES]
        paths.extend(path for dirname in DIRS for path in (ROOT / dirname).rglob("*") if path.is_file())
        for path in sorted(set(paths)):
            relative = path.relative_to(ROOT)
            if any(part in EXCLUDED for part in relative.parts) or path.suffix == ".pyc":
                continue
            content = path.read_bytes()
            mode = 0o755 if os.access(path, os.X_OK) else 0o644
            add_bytes(archive, str(relative), content, mode)
            manifest.append(f"{hashlib.sha256(content).hexdigest()}  {relative}")
        for name, body, mode in (
            ("安装依赖.command", INSTALL, 0o755),
            ("启动.command", START, 0o755),
            ("离线演示.command", DEMO, 0o755),
            ("README-先看这里.md", INTRO, 0o644),
        ):
            content = body.encode("utf-8")
            add_bytes(archive, name, content, mode)
            manifest.append(f"{hashlib.sha256(content).hexdigest()}  {name}")
        add_bytes(archive, "SHA256SUMS.txt", ("\n".join(manifest) + "\n").encode("utf-8"))
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "goutoujunshi-jev-chat-mac.zip")
    args = parser.parse_args()
    result = build(args.output)
    print(f"{result} ({result.stat().st_size} bytes)")
