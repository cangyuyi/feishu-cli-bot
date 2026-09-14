"""配置加载。

配置来源（前者优先）：
  1) ``~/.feishu_bot_env`` 文件，每行 ``KEY=VALUE``
  2) 进程环境变量

这样既能让机器人脱离任何宿主应用独立运行，又不必把密钥写进代码。

注意：``load_env_file()`` 必须在读取任何 ``FEISHU_BOT_*`` 环境变量之前调用，
否则下方常量会取到默认值/占位符（例如 chat_id 落到占位符导致收不到消息）。
"""
from __future__ import annotations

import datetime
import os
import sys

# 配置文件路径（不在仓库内，已加入 .gitignore）
ENV_FILE = os.path.expanduser("~/.feishu_bot_env")


def load_env_file() -> None:
    """读取 ~/.feishu_bot_env 写入 os.environ（不覆盖已有环境变量）。"""
    if not os.path.exists(ENV_FILE):
        return
    try:
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key, value = key.strip(), value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception as exc:  # noqa: BLE001 - 配置解析失败不应中断启动，但需告知用户
        print(f"[config] 警告：读取配置文件 {ENV_FILE} 失败：{exc}", file=sys.stderr)


# 必须在读取任何 FEISHU_BOT_* 环境变量之前加载，否则常量会取到默认值/占位符
load_env_file()


def _safe_int(name: str, default: int, lo: int | None = None, hi: int | None = None) -> int:
    """安全读取整数型环境变量：非法值回退默认值并打印警告，不再直接崩溃。"""
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        val = int(raw)
    except (TypeError, ValueError):
        print(f"[config] 警告：环境变量 {name}={raw!r} 不是合法整数，已回退默认值 {default}", file=sys.stderr)
        return default
    if lo is not None and val < lo:
        print(f"[config] 警告：{name}={val} 小于下限 {lo}，已钳制为 {lo}", file=sys.stderr)
        return lo
    if hi is not None and val > hi:
        print(f"[config] 警告：{name}={val} 大于上限 {hi}，已钳制为 {hi}", file=sys.stderr)
        return hi
    return val


# 默认监听的会话（用户与机器人的私聊）。可通过环境变量覆盖。
# 公开仓库不含任何真实 id，请复制 config/feishu_bot_env.example 后填入你自己的。
CHAT_ID = os.environ.get(
    "FEISHU_BOT_CHAT_ID",
    "oc_xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
)

# 轮询间隔（秒）
INTERVAL = _safe_int("FEISHU_BOT_INTERVAL", 3, lo=1, hi=60)

# 对话记忆保留策略（默认贴近模型 256k 上下文窗口，留余量给系统提示/工具/回复）
# - 按 token 预算截断（主）：HISTORY_TOKEN_BUDGET，可通过 FEISHU_BOT_HISTORY_TOKEN_BUDGET 覆盖
# - 按消息条数硬上限（兜底，防 state 文件无限膨胀）：HISTORY_MAX，可通过 FEISHU_BOT_HISTORY_MAX 覆盖
HISTORY_MAX = _safe_int("FEISHU_BOT_HISTORY_MAX", 5000, lo=1)
HISTORY_TOKEN_BUDGET = _safe_int("FEISHU_BOT_HISTORY_TOKEN_BUDGET", 200000, lo=1000)

# function calling 最大轮数（防止模型无限循环调用工具）；可通过环境变量调整
MAX_TOOL_ROUNDS = _safe_int("FEISHU_BOT_MAX_TOOL_ROUNDS", 4, lo=1, hi=20)

# 时区（飞书默认 +08:00）
TZ = datetime.timezone(datetime.timedelta(hours=8))

# 状态持久化文件
STATE_FILE = os.path.expanduser("~/.feishu_bot_state.json")


def allow_write() -> bool:
    """是否允许写操作（建日程/建任务/发消息）。"""
    return os.environ.get("FEISHU_BOT_ALLOW_WRITE", "1") == "1"


def llm_configured() -> bool:
    """是否已配置大模型（base_url + key 同时存在）。"""
    return bool(os.environ.get("FEISHU_BOT_LLM_BASE_URL") and os.environ.get("FEISHU_BOT_LLM_KEY"))
