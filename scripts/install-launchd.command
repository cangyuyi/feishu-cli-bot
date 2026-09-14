#!/usr/bin/env bash
# 用 launchd 托管机器人，实现开机自启 + 崩溃自动拉起
# 双击或在 Terminal 中运行: bash scripts/install-launchd.command

set -e

cd "$(dirname "$0")/.."
REPO_DIR="$(pwd)"
PLIST="$HOME/Library/LaunchAgents/com.feishu-bot.assistant.plist"
LABEL="com.feishu-bot.assistant"
DOMAIN="gui/$(id -u)"

echo "=========================================="
echo "  正在把飞书机器人交给 launchd 托管..."
echo "  仓库: $REPO_DIR"
echo "  Plist: $PLIST"
echo "=========================================="

# 1. 停掉当前终端里跑的看门狗/机器人（避免重复实例抢 lock）
echo "[1/4] 停止当前终端会话里的机器人..."
pkill -f "feishu-bot-watchdog" || true
pkill -f "feishu_bot" || true
sleep 1

# 2. 把仓库里的 plist 复制到 ~/Library/LaunchAgents/
REPO_PLIST="$REPO_DIR/scripts/com.feishu-bot.assistant.plist"
if [[ ! -f "$REPO_PLIST" ]]; then
    echo "❌ 仓库里缺少 LaunchAgent plist：$REPO_PLIST"
    exit 1
fi
mkdir -p "$HOME/Library/LaunchAgents"
cp "$REPO_PLIST" "$PLIST"
plutil -lint "$PLIST" >/dev/null 2>&1 || { echo "❌ plist 格式校验失败"; exit 1; }

# 3. 如果之前加载过，先 unload
echo "[2/4] 清理旧的 launchd 注册..."
launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true

# 4. 注册并立即启动
echo "[3/4] 注册 LaunchAgent..."
if launchctl bootstrap "$DOMAIN" "$PLIST"; then
    echo "[4/4] 立即启动..."
    launchctl kickstart "$DOMAIN/$LABEL" || true
    echo "✅ 完成。机器人已交给 launchd 托管，重启 Mac 后会自动启动。"
else
    echo "⚠️ launchctl bootstrap 失败，尝试 legacy load..."
    if launchctl load -w "$PLIST" 2>/dev/null; then
        echo "✅ legacy load 成功。"
    else
        echo "❌ 当前环境无法直接加载 LaunchAgent。请手动执行："
        echo "   launchctl bootstrap $DOMAIN $PLIST"
        echo "   launchctl kickstart $DOMAIN/$LABEL"
        exit 1
    fi
fi

echo ""
echo "验证命令："
echo "  launchctl list | grep $LABEL"
echo "  pgrep -fl feishu"
echo "  tail -f bot-launchd.err"
