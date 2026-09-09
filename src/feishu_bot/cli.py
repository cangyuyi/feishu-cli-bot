"""lark-cli 封装层。

本机器人不直接调用飞书开放平台 API，而是复用已授权的 ``lark-cli``
（飞书官方命令行工具），用两种身份执行操作：

- ``--as user`` ：以当前登录用户身份「读」消息（双向对话的关键）
- ``--as bot``  ：以机器人身份「发」消息（绕过开放平台后台的回调配置）

这样无需 App Secret、无需在开发者后台配置事件订阅即可跑起来。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess


def _resolve_lark_cli() -> str:
    """定位 lark-cli 可执行文件。

    优先级：PATH 查找 → 常见安装路径 → WorkBuddy 内置路径 → 兜底路径。
    """
    found = shutil.which("lark-cli")
    if found:
        return found
    candidates = [
        os.path.expanduser("~/.workbuddy/binaries/node/cli-connector-packages/bin/lark-cli"),
        "/usr/local/bin/lark-cli",
        "/opt/homebrew/bin/lark-cli",
        "/usr/bin/lark-cli",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    # 兜底：即便不存在也返回一个可读路径，便于报错提示
    return candidates[-1]


# 脱离子进程（登录项/后台）后 PATH 与可执行查找都可能失效，故一次性解析并缓存
LARK_CLI = _resolve_lark_cli()


def run(args: list) -> dict:
    """调用 lark-cli 并把 stdout/stderr 的 JSON 解析成 dict。

    lark-cli 的错误信息可能走 stderr，这里优先取带 ``ok`` 字段的信封；
    解析失败时返回 ``{"ok": False, "error": {"message": ...}}`` 以便上层处理。
    """
    if not os.path.exists(LARK_CLI):
        return {
            "ok": False,
            "error": {"message": f"未找到 lark-cli：{LARK_CLI}。请先安装并授权 lark-cli。"},
        }
    cmd = [LARK_CLI, *args]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        return {"ok": False, "error": {"message": f"无法执行 lark-cli：{LARK_CLI}"}}
    except Exception as exc:  # noqa: BLE001 - 任何异常都要兜底成可解析的错误结构
        return {"ok": False, "error": {"message": f"{type(exc).__name__}: {exc}"}}

    raw = (proc.stdout or proc.stderr or "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # 非 JSON 输出（例如帮助文本、授权提示）按错误回显前 200 字
        return {"ok": False, "error": {"message": raw[:200] or "lark-cli 无输出"}}
