#!/bin/sh
# LaunchAgent 启动包装：显式设定 PYTHONPATH 与运行目录。
# 优先使用 WorkBuddy 托管的 python3.13（launchd 纯净环境拉得起来），否则回退系统 python3。
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
export PYTHONPATH="$REPO_DIR/src"
cd "$REPO_DIR" || exit 1

MANAGED_PY="$HOME/.workbuddy/binaries/python/versions/3.13.12/bin/python3"
if [ -x "$MANAGED_PY" ]; then
    exec "$MANAGED_PY" -m feishu_bot
else
    exec python3 -m feishu_bot
fi
