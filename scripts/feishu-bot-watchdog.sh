#!/bin/bash
# 飞书机器人看门狗：拉起 bot 主进程，崩溃后自动重启（自愈）。
# 由 launch.command 后台启动；彻底停止请 pkill -f feishu-bot-watchdog
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
PY="${PYTHON:-python3}"
LOG_FILE="$ROOT/bot-poller.log"
MODULE="feishu_bot"

MAX_FAIL=10  # 连续崩溃上限，避免「启动即崩」死循环刷日志
fail_count=0

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 看门狗启动，监控模块 $MODULE" >> "$LOG_FILE"

while true; do
    "$PY" -u -m "$MODULE" >> "$LOG_FILE" 2>&1
    code=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] bot 退出 (code=$code)，3s 后重启（第 $((fail_count + 1)) 次）" >> "$LOG_FILE"
    fail_count=$((fail_count + 1))
    if [ "$fail_count" -ge "$MAX_FAIL" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 连续崩溃 $MAX_FAIL 次，停止自愈，请检查日志：$LOG_FILE" >> "$LOG_FILE"
        break
    fi
    sleep 3
done
