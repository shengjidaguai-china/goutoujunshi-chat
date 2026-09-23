#!/bin/zsh
set -eu
cd "$(dirname "$0")"
# Dependency installation is separate; startup never downloads a model or sends chats.
if [[ ! -x .venv/bin/python ]]; then
  print '请先按 README 安装桌面依赖（integrations/jev_mac/.venv）。'
  exit 1
fi
exec .venv/bin/python -B app.py "$@"
