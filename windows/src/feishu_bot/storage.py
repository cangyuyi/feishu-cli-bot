"""对话状态持久化。

把「上一次读到的消息 ID」和最近 N 轮对话记忆写进 JSON 文件，
保证机器人重启后能续上上下文、不会重复回复同一条消息。
"""
from __future__ import annotations

import json
import os
import sys
import time

from . import config
from . import formatter


def load_state() -> dict:
    """读取状态文件；不存在或损坏时返回空状态。

    状态文件损坏时**保留现场**：复制为 ``.corrupt-<时间戳>`` 备份并打印警告，
    而不是静默清空（否则会让用户误以为「第一次启动」并重处理旧消息）。
    """
    path = config.STATE_FILE
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:  # noqa: BLE001
            backup = f"{path}.corrupt-{int(time.time())}"
            try:
                import shutil as _sh
                _sh.copy2(path, backup)
            except Exception:
                backup = "(备份失败)"
            print(
                f"[storage] 警告：状态文件 {path} 损坏（{exc}），"
                f"已备份为 {backup}，本次按空状态启动。",
                file=sys.stderr,
            )
    return {"last_message_id": None, "history": []}


def save_state(state: dict) -> None:
    """原子写入状态文件：先写临时文件并 fsync，再 os.replace 替换，避免写入中途崩溃产生半截 JSON。"""
    path = config.STATE_FILE
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def trim_history(history: list) -> list:
    """按 token 预算保留最近的对话历史，避免顶破模型上下文窗口。

    - 先按消息条数硬上限 ``config.HISTORY_MAX`` 裁剪（兜底，防止 state 文件无限膨胀）。
    - 再按 token 预算 ``config.HISTORY_TOKEN_BUDGET`` 从新到旧保留，超出即丢弃最旧部分。
    返回的是 ``history`` 的一个新列表（不修改入参）。
    """
    if not history:
        return []
    recent = history[-config.HISTORY_MAX:] if config.HISTORY_MAX > 0 else list(history)
    budget = config.HISTORY_TOKEN_BUDGET
    kept: list = []
    used = 0
    for msg in reversed(recent):
        content = msg.get("content", "") if isinstance(msg, dict) else ""
        t = formatter.estimate_tokens(content) if isinstance(content, str) else 0
        if kept and used + t > budget:
            break
        kept.insert(0, msg)
        used += t
    return kept
