#!/bin/bash
# 飞书机器人后台启动器（macOS 登录项 / 双击运行）
# 进程脱离终端，关闭本窗口后机器人继续运行。

# 定位项目根目录（scripts/ 的上一级）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
cd "$ROOT" || exit 1

# 包位于 src/feishu_bot，需把 src 加入导入路径（重构后必需）
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

PY="${PYTHON:-python3}"
LOG_FILE="$ROOT/bot-poller.log"
MODULE="feishu_bot"

# 已有实例先停掉，避免重复回复（匹配任意 python 路径下的 feishu_bot 进程）
pkill -f "feishu_bot" 2>/dev/null || true
sleep 1

echo "=========================================="
echo "  飞书机器人启动中..."
echo "  日志：$LOG_FILE"
echo "  关闭本窗口后机器人继续运行"
echo "=========================================="
echo

# 后台常驻：nohup + disown，脱离终端（登录项启动也不会随窗口关闭而终止）
nohup "$PY" -u -m "$MODULE" > "$LOG_FILE" 2>&1 &
PID=$!
disown $PID

sleep 2
if kill -0 "$PID" 2>/dev/null; then
    echo "已启动成功，PID: $PID"
    echo "查看实时日志：tail -f $LOG_FILE"
else
    echo "启动失败，请查看日志："
    tail -20 "$LOG_FILE"
fi
