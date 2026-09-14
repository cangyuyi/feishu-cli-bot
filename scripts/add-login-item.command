#!/bin/bash
# 把飞书机器人加入 macOS 登录项（System Settings > General > Login Items）
# 开机/登录后自动后台启动，并清理旧版冲突的登录项。
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LAUNCH_CMD="$SCRIPT_DIR/launch.command"
NEW_NAME="Feishu Office Assistant"

osascript <<EOF
tell application "System Events"
    set existingNames to name of every login item
    repeat with oldName in {"启动飞书机器人", "启动飞书机器人.command", "Feishu Bot", "FeishuBot", "Feishu Office Assistant"}
        try
            if oldName is in existingNames then
                delete login item oldName
            end if
        end try
    end repeat
    make new login item at end with properties {name:"$NEW_NAME", path:"$LAUNCH_CMD", hidden:true}
end tell
EOF

if [ $? -eq 0 ]; then
    echo "✅ 已添加登录项：$NEW_NAME"
    echo "   启动脚本：$LAUNCH_CMD"
    echo "   请前往「系统设置 → 通用 → 登录项」确认出现 '$NEW_NAME'"
else
    echo "❌ 自动添加失败，请手动到「系统设置 → 通用 → 登录项」添加：$LAUNCH_CMD"
fi
