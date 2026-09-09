"""输出格式化辅助函数（纯函数，便于单元测试）。"""
from __future__ import annotations

import datetime
import json

from . import config


def parse_content(msg: dict) -> str:
    """从一条飞书消息里提取纯文本。

    飞书文本消息的 content 可能是 JSON（``{"text": "..."}``）也可能是原始字符串。
    """
    raw = msg.get("content", "")
    if not raw:
        return ""
    if raw.startswith("{"):
        try:
            return json.loads(raw).get("text", raw)
        except json.JSONDecodeError:
            return raw
    return raw


def ts_to_hhmm(ts) -> str:
    """把 Unix 时间戳转成 HH:MM；空值返回 '?'。"""
    if ts in (None, ""):
        return "?"
    try:
        return datetime.datetime.fromtimestamp(int(ts), tz=config.TZ).strftime("%H:%M")
    except (ValueError, OSError, TypeError):
        return "?"


def now_str() -> str:
    """当前时间的可读字符串（含星期）。"""
    return datetime.datetime.now(config.TZ).strftime("%Y-%m-%d %H:%M:%S %A")


def today_str() -> str:
    """今天日期 YYYY-MM-DD。"""
    return datetime.datetime.now(config.TZ).strftime("%Y-%m-%d")


def estimate_tokens(text: str) -> int:
    """粗略估算文本的 token 数（零依赖近似，用于历史截断预算）。

    中文按 ~1.6 token/字、英文/数字按 ~0.3 token/字符、标点与空白按 ~0.15 估算。
    这是保守上偏的近似：宁可按略多估算，避免历史意外顶破模型上下文窗口。
    """
    if not text:
        return 0
    n = 0.0
    for ch in text:
        cp = ord(ch)
        if 0x4E00 <= cp <= 0x9FFF or 0x3040 <= cp <= 0x30FF or 0xFF00 <= cp <= 0xFFEF:
            n += 1.6  # CJK / 假名 / 全角
        elif ch.isascii() and ch.isalnum():
            n += 0.3  # 英文 / 数字
        else:
            n += 0.15  # 标点 / 空白
    return max(1, int(n) + 1)
