"""输出格式化辅助函数（纯函数，便于单元测试）。"""
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
