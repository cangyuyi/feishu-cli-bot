#!/usr/bin/env bash
# feishu-cli-bot 安装脚本
# 检查依赖、生成配置文件、引导 lark-cli 授权，并可注册为 macOS 登录项。

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$HOME/.feishu_bot_env"
EXAMPLE="$ROOT/config/feishu_bot_env.example"

echo "== feishu-cli-bot 安装 =="
echo "项目目录: $ROOT"

# 1) Python 版本检查
if ! command -v python3 >/dev/null 2>&1; then
    echo "[错误] 未找到 python3，请先安装 Python 3.9+"
    exit 1
fi
PY_VER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "[ok] Python $PY_VER"

# 2) lark-cli 检查
if ! command -v lark-cli >/dev/null 2>&1; then
    echo "[提示] 未检测到 lark-cli。请通过你的宿主应用（如 WorkBuddy）安装飞书 CLI 连接包，"
    echo "       或确认其在 PATH 中。安装完成后重新运行本脚本。"
    LARK_MISSING=1
else
    echo "[ok] lark-cli 已安装"
    LARK_MISSING=0
fi

# 3) 生成配置文件
if [ -f "$ENV_FILE" ]; then
    echo "[跳过] 配置文件已存在: $ENV_FILE"
else
    cp "$EXAMPLE" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo "[ok] 已生成配置文件: $ENV_FILE（权限 600）"
    echo "     请编辑该文件，填入你的 LLM base_url / key，以及监听的 chat_id。"
fi

# 4) 引导授权
if [ "$LARK_MISSING" -eq 0 ]; then
    echo
    echo "== 飞书授权 =="
    echo "接下来请完成设备码授权（会打开浏览器）。需要以下 scope："
    echo "  - 消息读取（im）  - 消息发送（bot）  - 日历（calendar）  - 任务（task）"
    echo "若只需读取活动/日报，授权 im + calendar + task 即可。"
    read -r -p "现在就运行授权吗？(y/N) " ANS
    if [ "$ANS" = "y" ] || [ "$ANS" = "Y" ]; then
        lark-cli auth login --domain calendar || true
    else
        echo "稍后请手动运行： lark-cli auth login --domain calendar"
    fi
fi

# 5) 注册登录项（macOS）
if [[ "$(uname)" == "Darwin" ]]; then
    read -r -p "注册为 macOS 登录项（开机自启）吗？(y/N) " ANS2
    if [ "$ANS2" = "y" ] || [ "$ANS2" = "Y" ]; then
        LAUNCH="$ROOT/scripts/launch.command"
        chmod +x "$LAUNCH"
        # 通过 AppleScript 加入系统登录项（无需 sudo）
        osascript -e "tell application \"System Events\" to make login item at end with properties {path:\"$LAUNCH\", hidden:false}" 2>/dev/null \
            && echo "[ok] 已加入登录项" \
            || echo "[提示] 自动添加失败，请手动到 系统设置 → 通用 → 登录项 添加：$LAUNCH"
    fi
fi

echo
echo "== 完成 =="
echo "运行自检：    python3 -m feishu_bot --selftest"
echo "前台启动：    python3 -m feishu_bot"
echo "后台启动：    $ROOT/scripts/launch.command"
