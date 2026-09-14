#!/usr/bin/env bash
# 安装 macOS 开机自启（推荐：登录项；可选：LaunchAgent）
# 双击或在 Terminal 中运行: bash scripts/install-launchd.command

set -e

cd "$(dirname "$0")/.."
REPO_DIR="$(pwd)"

echo "=========================================="
echo "  飞书机器人 · 开机自启配置"
echo "  仓库: $REPO_DIR"
echo "=========================================="

# 1. 停掉当前终端里跑的看门狗/机器人（避免重复实例抢 lock）
echo "[1/2] 停止当前机器人进程..."
pkill -f "feishu-bot-watchdog" || true
pkill -f "feishu_bot" || true
sleep 1
rm -f /tmp/feishu_bot.lock

# 2. 优先推荐：登录项（钥匙串兼容最好）
echo "[2/2] 推荐方案：注册为 macOS 登录项..."
if bash "$REPO_DIR/scripts/add-login-item.command"; then
    echo ""
    echo "✅ 完成。机器人已加入登录项："
    echo "   系统设置 → 通用 → 登录项 → launch.command"
    echo "   重启 Mac 后会自动启动。"
    echo ""
    echo "验证："
    echo "  pgrep -fl feishu"
    echo "  tail -f bot-poller.log"
    exit 0
fi

echo ""
echo "⚠️ 登录项注册失败（通常因为未给 Terminal/System Events 辅助功能权限）。"
echo "   请按以下步骤手动添加："
echo "   1. 打开「系统设置 → 通用 → 登录项」"
echo "   2. 点击「+」，选择 $REPO_DIR/scripts/launch.command"
echo "   3. 重启 Mac 后自动启动"
echo ""
echo "临时启动："
echo "  bash $REPO_DIR/scripts/launch.command"
