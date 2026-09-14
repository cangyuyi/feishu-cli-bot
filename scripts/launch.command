#!/bin/bash
# 飞书机器人启动器（macOS 登录项 / 双击运行），崩溃自愈由看门狗负责。
# 本脚本只做「停止旧实例 + 拉起看门狗」，看门狗常驻并自动重启 bot。

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
cd "$ROOT" || exit 1

# 先停掉旧的看门狗与 bot，避免重复拉起（feishu_bot 与 feishu-bot-watchdog 用不同分隔符，互不误杀）
pkill -f "feishu-bot-watchdog" 2>/dev/null || true
pkill -f "feishu_bot" 2>/dev/null || true
sleep 1

echo "=========================================="
echo "  飞书机器人启动中（崩溃自愈模式）..."
echo "  日志：$ROOT/bot-poller.log"
echo "  彻底停止：pkill -f feishu-bot-watchdog"
echo "=========================================="

# 后台常驻：nohup + disown，脱离终端（登录项启动也不会随窗口关闭而终止）
nohup "$SCRIPT_DIR/feishu-bot-watchdog.sh" > /dev/null 2>&1 &
disown

echo "已启动看门狗（具体 PID 见日志）。"
echo "查看实时日志：tail -f $ROOT/bot-poller.log"
