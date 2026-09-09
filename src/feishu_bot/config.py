"""配置加载。

配置来源（前者优先）：
  1) ``~/.feishu_bot_env`` 文件，每行 ``KEY=VALUE``
  2) 进程环境变量

这样既能让机器人脱离任何宿主应用独立运行，又不必把密钥写进代码。
"""
from __future__ import annotations

import datetime
import os

# 配置文件路径（不在仓库内，已加入 .gitignore）
ENV_FILE = os.path.expanduser("~/.feishu_bot_env")

# 默认监听的会话（用户与机器人的私聊）。可通过环境变量覆盖。
# 公开仓库不含任何真实 id，请复制 config/feishu_bot_env.example 后填入你自己的。
CHAT_ID = os.environ.get(
    "FEISHU_BOT_CHAT_ID",
    "oc_xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
)

# 轮询间隔（秒）
INTERVAL = int(os.environ.get("FEISHU_BOT_INTERVAL", "3"))

# 对话记忆保留的轮数
HISTORY_MAX = 16

# function calling 最大轮数（防止模型无限循环调用工具）
MAX_TOOL_ROUNDS = 4

# 时区（飞书默认 +08:00）
TZ = datetime.timezone(datetime.timedelta(hours=8))

# 状态持久化文件
STATE_FILE = os.path.expanduser("~/.feishu_bot_state.json")


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
    except Exception:  # noqa: BLE001 - 配置解析失败不应中断启动
        pass


# 模块导入即加载一次
load_env_file()


def allow_write() -> bool:
    """是否允许写操作（建日程/建任务/发消息）。"""
    return os.environ.get("FEISHU_BOT_ALLOW_WRITE", "1") == "1"


def llm_configured() -> bool:
    """是否已配置大模型（base_url + key 同时存在）。"""
    return bool(os.environ.get("FEISHU_BOT_LLM_BASE_URL") and os.environ.get("FEISHU_BOT_LLM_KEY"))
