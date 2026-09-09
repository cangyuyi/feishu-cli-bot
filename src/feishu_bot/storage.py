"""对话状态持久化。

把「上一次读到的消息 ID」和最近 N 轮对话记忆写进 JSON 文件，
保证机器人重启后能续上上下文、不会重复回复同一条消息。
"""
import json
import os

from . import config


def load_state() -> dict:
    """读取状态文件；不存在或损坏时返回空状态。"""
    path = config.STATE_FILE
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:  # noqa: BLE001 - 损坏即视为空，避免崩溃
            pass
    return {"last_message_id": None, "history": []}


def save_state(state: dict) -> None:
    """写入状态文件。"""
    with open(config.STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)
