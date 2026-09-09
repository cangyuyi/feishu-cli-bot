"""Agent 层：LLM 调用 + function calling 循环 + 无模型时的降级。

设计要点：
- 大模型采用 OpenAI 兼容接口（任意 base_url 均可，如火山方舟豆包、OpenAI、本地 Ollama）。
- ``agent_reply`` 实现多轮 function calling：模型可以连续调用多个工具，直到它认为
  已经收集到足够信息，再给出最终自然语言回复。
- 未配置大模型时，退化为关键词工具 + 规则回复，保证离线也能用。
"""
from __future__ import annotations

import json
import os
import urllib.request

from . import config
from . import formatter
from . import tools
from . import schemas
from . import storage

SYSTEM_PROMPT = (
    "你是「专属飞书办公小助手」（Feishu Office Assistant），一台本机常驻的飞书 AI 助手，能真正执行任务而不只是聊天。\n"
    "当前时间：{now}\n"
    "风格：简洁、直接、有主见，中文回答。\n"
    "可用能力（按需调用）：\n"
    "- 日程：get_agenda、create_event、find_free_time\n"
    "- 任务：get_tasks、create_task、task_search\n"
    "- 通信：list_chats、search_messages、send_message、reply_to_message\n"
    "- 文档：read_document（用户贴 URL）、list_drive_files\n"
    "- 信息：get_my_activity（今日总览）、get_daily_chats（可按 mine/others 筛选）、whoami\n"
    "- 报告：generate_report\n"
    "重要：用户问「我今天做了什么」「我的飞书活动」「我今天发了什么」时，"
    "优先调用 get_my_activity 或 get_daily_chats(whose='mine')，必须真实调用工具，不要凭空回答。\n"
    "原则：\n"
    "1. 需要真实数据时必须调用工具，绝不凭空编造。\n"
    "2. 工具返回什么就基于什么回答；查不到就直说查不到。\n"
    "3. 涉及写入（建日程/建任务/发消息）前，确认参数完整；缺关键信息就先问用户。\n"
    "4. 涉及其他会话时先用 list_chats 拿到 chat_id 再 send_message。\n"
    "5. 用户贴飞书文档 URL 时，直接调 read_document。\n"
    "6. 回答控制在 300 字内。"
)


def llm_configured() -> bool:  # re-export 便于调用方从 agent 层取用
    return config.llm_configured()


def _post_chat(payload: dict) -> dict:
    """向大模型 chat/completions 端点发起请求并返回解析后的 JSON。"""
    base = os.environ.get("FEISHU_BOT_LLM_BASE_URL", "").rstrip("/")
    key = os.environ.get("FEISHU_BOT_LLM_KEY", "")
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def agent_reply(user_text: str, history: list) -> tuple[str, list]:
    """function calling 循环：模型自主决定调用哪些工具。

    返回 (最终回复文本, 工具调用轨迹)。
    """
    model = os.environ.get("FEISHU_BOT_LLM_MODEL", "gpt-4o-mini")
    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(now=formatter.now_str())}]
    for h in storage.trim_history(history):
        messages.append(h)
    messages.append({"role": "user", "content": user_text})

    trace: list[str] = []
    try:
        for _ in range(config.MAX_TOOL_ROUNDS):
            payload = {"model": model, "messages": messages, "temperature": 0.6}
            if schemas.TOOL_SCHEMA:
                payload["tools"] = schemas.TOOL_SCHEMA
                payload["tool_choice"] = "auto"
            data = _post_chat(payload)
            msg = data["choices"][0]["message"]
            tool_calls = msg.get("tool_calls") or []

            if not tool_calls:
                return msg.get("content", "").strip(), trace

            messages.append(msg)
            for tc in tool_calls:
                fn = tc["function"]["name"]
                try:
                    args = json.loads(tc["function"].get("arguments") or "{}")
                except json.JSONDecodeError:
                    args = {}
                impl = tools.TOOL_IMPL.get(fn)
                result = impl(args) if impl else f"未知工具：{fn}"
                if impl:
                    trace.append(f"{fn}({json.dumps(args, ensure_ascii=False)[:60]})")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": str(result),
                })
        # 轮次用尽，再向模型要一次总结
        data = _post_chat({"model": model, "messages": messages, "temperature": 0.6})
        return data["choices"][0]["message"].get("content", "").strip(), trace
    except Exception as exc:  # noqa: BLE001 - 模型层异常不能让主循环崩
        return f"（模型调用失败：{type(exc).__name__}: {str(exc)[:120]}）", trace


# ---------- 无模型时的降级 ----------

def match_tool(text: str):
    t = text.strip()
    if any(k in t for k in ("日报", "工作总结", "今天干了")):
        return tools.t_report
    if any(k in t for k in ("日程", "安排", "有什么会", "今天有啥", "会议")):
        return tools.t_agenda
    if any(k in t for k in ("任务", "待办", "todo")):
        return tools.t_tasks
    if any(k in t for k in ("我是谁", "你的身份")):
        return tools.t_whoami
    return None


def rule_reply(user_text: str) -> str:
    t = user_text.strip()
    if any(k in t for k in ("你好", "hi", "hello", "哈喽", "在吗")):
        return "在。我能查日程、查待办、出日报。接了大模型后还能自由对话和执行更多任务。"
    if any(k in t for k in ("帮助", "help", "怎么用", "能干")):
        return ("直接说：\n· 今天日程 / 有什么会\n· 我的待办\n· 日报\n· 我是谁\n\n"
                f"当前模式：{'大模型已接入' if llm_configured() else '规则模式（未接大模型）'}")
    return ("现在是规则模式，只认关键词。\n"
            "能做的：发「日程」「待办」「日报」「我是谁」。\n"
            "接上大模型后可自由对话并自主调用工具完成任务。")


def generate_reply(user_text: str, history: list) -> str:
    """统一入口：有模型走 Agent，无模型走规则。"""
    if llm_configured():
        reply, trace = agent_reply(user_text, history)
        if trace:
            print(f"    [tools] {' → '.join(trace)}", flush=True)
        return reply
    fn = match_tool(user_text)
    if fn:
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            return f"工具执行出错：{type(exc).__name__}: {str(exc)[:100]}"
    return rule_reply(user_text)
