"""工具实现层。

每个 ``t_*`` 函数对应一个可被大模型通过 function calling 调用的能力，
最终汇总进 ``TOOL_IMPL``（名字 -> 实现）。这些函数只通过 :mod:`cli` 与飞书交互，
返回字符串给模型阅读。

涉及写操作（建日程/建任务/发消息/回复）会先检查 :func:`config.allow_write`。
"""
from __future__ import annotations

import json
import os
import tempfile

from . import cli
from . import config
from . import formatter


def json_dumps(obj) -> str:
    """把对象序列化为 JSON 字符串（ensure_ascii=False，便于中文阅读）。"""
    return json.dumps(obj, ensure_ascii=False)


_MY_OPEN_ID = None


def get_my_open_id() -> str | None:
    """缓存并返回当前登录用户的 open_id（用于判断一条消息是不是自己发的）。"""
    global _MY_OPEN_ID
    if _MY_OPEN_ID:
        return _MY_OPEN_ID
    r = cli.run(["whoami"])
    d = r if "identity" in r else r.get("data", {})
    _MY_OPEN_ID = (d.get("onBehalfOf") or {}).get("openId")
    return _MY_OPEN_ID


# ---------- 日程 / 任务 ----------

def t_agenda(date: str | None = None) -> str:
    day = date or formatter.today_str()
    r = cli.run(["calendar", "+agenda", "--as", "user",
                 "--start", f"{day}T00:00:00+08:00", "--end", f"{day}T23:59:59+08:00"])
    if not r.get("ok"):
        return f"查日程失败：{r.get('error', {}).get('message', '未知错误')}"
    data = r.get("data", [])
    events = data if isinstance(data, list) else (data.get("items") or [])
    if not events:
        return f"{day} 没有日程。"
    out = [f"{day} 共 {len(events)} 项："]
    for ev in events:
        st = formatter.ts_to_hhmm(ev.get("start_time", {}).get("timestamp"))
        et = formatter.ts_to_hhmm(ev.get("end_time", {}).get("timestamp"))
        out.append(f"· {st}-{et} {ev.get('summary', '(无标题)')}")
    return "\n".join(out)


def t_tasks() -> str:
    r = cli.run(["task", "+get-my-tasks", "--as", "user", "--complete=false"])
    if not r.get("ok"):
        return f"查任务失败：{r.get('error', {}).get('message', '未知错误')}"
    data = r.get("data", {})
    items = (data.get("items") or []) if isinstance(data, dict) else (data or [])
    if not items:
        return "当前没有未完成任务。"
    out = [f"未完成 {len(items)} 项："]
    for t in items[:20]:
        due = t.get("due", {}).get("timestamp")
        out.append(f"· {t.get('summary', '(无标题)')}（截止 {formatter.ts_to_hhmm(due) if due else '无'}）")
    return "\n".join(out)


def t_create_task(summary: str, due: str | None = None) -> str:
    if not config.allow_write():
        return "写操作已关闭（FEISHU_BOT_ALLOW_WRITE=0）。"
    args = ["task", "+create", "--as", "user", "--summary", summary]
    if due:
        args += ["--due", due]
    r = cli.run(args)
    if not r.get("ok"):
        return f"创建失败：{r.get('error', {}).get('message', '未知错误')}"
    return f"已创建任务：{summary}"


def t_create_event(summary: str, start: str, end: str, description: str | None = None) -> str:
    if not config.allow_write():
        return "写操作已关闭（FEISHU_BOT_ALLOW_WRITE=0）。"
    args = ["calendar", "+create", "--as", "user",
            "--summary", summary, "--start", start, "--end", end]
    if description:
        args += ["--description", description]
    r = cli.run(args)
    if not r.get("ok"):
        return f"创建日程失败：{r.get('error', {}).get('message', '未知错误')}"
    return f"已创建日程：{summary}（{start} ~ {end}）"


def t_find_free_time(date: str | None = None, duration_minutes: int = 30,
                     hour_start: int = 9, hour_end: int = 18) -> str:
    day = date or formatter.today_str()
    start = f"{day}T{hour_start:02d}:00:00+08:00"
    end = f"{day}T{hour_end:02d}:00:00+08:00"
    r = cli.run(["calendar", "+suggestion", "--as", "user",
                 "--start", start, "--end", end,
                 "--duration-minutes", str(duration_minutes)])
    if not r.get("ok"):
        return f"查空闲失败：{r.get('error', {}).get('message', '未知错误')}"
    data = r.get("data", {})
    slots = data.get("free_slots") or (data if isinstance(data, list) else [])
    if not slots:
        return f"{day} 在 {hour_start}-{hour_end} 点没有 {duration_minutes} 分钟以上的空闲时段。"
    out = [f"{day} 可用时段："]
    for s in slots[:6]:
        st = formatter.ts_to_hhmm(s.get("start_time", {}).get("timestamp") or s.get("start"))
        et = formatter.ts_to_hhmm(s.get("end_time", {}).get("timestamp") or s.get("end"))
        out.append(f"· {st}-{et}")
    return "\n".join(out)


def t_task_search(query: str | None = None, limit: int = 15) -> str:
    args = ["task", "+search", "--as", "user", "--page-size", str(min(limit, 50))]
    if query:
        args += ["--query", query]
    r = cli.run(args)
    if not r.get("ok"):
        return f"搜任务失败：{r.get('error', {}).get('message', '未知错误')}"
    data = r.get("data", {})
    items = data.get("items") or (data if isinstance(data, list) else [])
    if not items:
        return f"没找到任务（关键词：{query or '无'}）。"
    out = [f"搜到 {len(items)} 项："]
    for t in items[:limit]:
        due = t.get("due", {}).get("timestamp")
        due_str = formatter.ts_to_hhmm(due) if due else "无截止"
        st = "✓" if t.get("status") == "completed" else "·"
        out.append(f"· {st} {t.get('summary', '(无标题)')}（截止 {due_str}）")
    return "\n".join(out)


# ---------- 通信 ----------

def t_chats() -> str:
    r = cli.run(["im", "+chat-list", "--as", "user", "--types", "p2p,group", "--page-size", "20"])
    if not r.get("ok"):
        return f"查会话失败：{r.get('error', {}).get('message', '未知错误')}"
    data = r.get("data", {})
    chats = data.get("chats") or []
    if not chats:
        return "没有会话。"
    out = []
    for c in chats:
        out.append(f"· {c.get('name') or '(无名)'} [{c.get('chat_mode')}] id={c.get('chat_id')}")
    return "\n".join(out)


def t_search_messages(query: str) -> str:
    r = cli.run(["im", "+messages-search", "--as", "user", "--query", query, "--page-size", "10"])
    if not r.get("ok"):
        return f"搜索失败：{r.get('error', {}).get('message', '未知错误')}"
    data = r.get("data", {})
    items = data.get("items") or data.get("messages") or []
    if not items:
        return f"没搜到含「{query}」的消息。"
    out = [f"搜到 {len(items)} 条："]
    for m in items[:10]:
        txt = formatter.parse_content(m)
        out.append(f"· {m.get('create_time', '')} {txt[:60]}")
    return "\n".join(out)


def t_send_to(chat_id: str, text: str) -> str:
    if not config.allow_write():
        return "写操作已关闭（FEISHU_BOT_ALLOW_WRITE=0）。"
    r = cli.run(["im", "+messages-send", "--as", "bot", "--chat-id", chat_id, "--text", text])
    if not r.get("ok"):
        return f"发送失败：{r.get('error', {}).get('message', '未知错误')}"
    return f"已发送到 {chat_id}。"


def t_reply_to_message(message_id: str, text: str) -> str:
    if not config.allow_write():
        return "写操作已关闭（FEISHU_BOT_ALLOW_WRITE=0）。"
    r = cli.run(["im", "+messages-reply", "--as", "bot",
                 "--message-id", message_id, "--text", text])
    if not r.get("ok"):
        return f"回复失败：{r.get('error', {}).get('message', '未知错误')}"
    return f"已回复消息 {message_id}。"


# ---------- 文档 / 云盘 ----------

def t_read_document(url: str, fmt: str = "markdown") -> str:
    r = cli.run(["docs", "+fetch", "--as", "user", "--doc", url,
                 "--doc-format", fmt, "--format", "markdown"])
    if not r.get("ok"):
        return f"读文档失败：{r.get('error', {}).get('message', '未知错误')}"
    data = r.get("data", {})
    content = data.get("content") or json_dumps(data)
    return f"文档内容（截断 3500 字）：\n{str(content)[:3500]}"


def t_list_drive_files(folder_token: str | None = None, limit: int = 20) -> str:
    args = ["drive", "files", "list", "--as", "user", "--page-size", str(min(limit, 100))]
    if folder_token:
        args += ["--folder-token", folder_token]
    r = cli.run(args)
    if not r.get("ok"):
        return f"列云盘失败：{r.get('error', {}).get('message', '未知错误')}"
    data = r.get("data", {})
    files = data.get("files") or []
    if not files:
        return "云盘根目录为空。"
    out = [f"共 {len(files)} 项（按编辑时间倒序）："]
    for f in files[:limit]:
        url = f.get("url") or ""
        out.append(f"· {f.get('name', '?')} [{f.get('type', '?')}] {url}")
    return "\n".join(out)


# ---------- 飞书在线表格（多维表格 / 电子表格）----------

def t_create_bitable(name: str, workspace_token: str | None = None) -> str:
    """创建一个新的飞书多维表格（BaseApp，结构化在线表格）。

    走底层 OpenAPI（POST /open-apis/bitable/v1/apps），folder_token 可选：
    不传则建在用户默认空间，从而无需预先配置 workspace 也能一键建表。
    返回 app_token 与访问链接。
    """
    if not config.allow_write():
        return "写操作已关闭（FEISHU_BOT_ALLOW_WRITE=0）。"
    body = {"name": name}
    ws = workspace_token or os.environ.get("FEISHU_BOT_WORKSPACE_TOKEN")
    if ws:
        body["folder_token"] = ws
    r = cli.run(["api", "POST", "/open-apis/bitable/v1/apps", "--as", "user",
                 "--data", json.dumps(body, ensure_ascii=False)])
    # 兼容 lark-cli 包装信封 {ok,data,error} 与 OpenAPI 原始信封 {code,data,msg}
    if not r.get("ok", True) and r.get("ok") is not None:
        return f"创建多维表格失败：{r.get('error', {}).get('message', '未知错误')}"
    if r.get("code", 0) != 0:
        return f"创建多维表格失败：{r.get('msg', '未知错误')}"
    data = r.get("data") or {}
    app = data.get("app") or data
    app_token = app.get("app_token") or data.get("app_token")
    url = app.get("url") or data.get("url") or (f"https://feishu.cn/base/{app_token}" if app_token else "")
    return f"已创建多维表格：{name}\napp_token={app_token}\n链接：{url}"


def t_create_spreadsheet(name: str) -> str:
    """创建一个新的飞书电子表格（类似 Excel 的在线表格）。返回 spreadsheetToken 与链接。"""
    if not config.allow_write():
        return "写操作已关闭（FEISHU_BOT_ALLOW_WRITE=0）。"
    body = json.dumps({"title": name}, ensure_ascii=False)
    r = cli.run(["sheets", "spreadsheets", "create", "--as", "user", "--data", body])
    if not r.get("ok"):
        return f"创建电子表格失败：{r.get('error', {}).get('message', '未知错误')}"
    data = r.get("data", {})
    sp_token = data.get("spreadsheetToken") or data.get("spreadsheet_token")
    url = data.get("url") or (f"https://feishu.cn/sheets/{sp_token}" if sp_token else "")
    return f"已创建电子表格：{name}\nspreadsheetToken={sp_token}\n链接：{url}"


def t_create_doc(name: str, folder_token: str | None = None, content: str | None = None) -> str:
    """创建一个新的飞书文档（Docx，类似 Word 的在线文档）。

    如果提供 ``content``，会把它作为 Markdown 通过 ``lark-cli docs +create`` 直接导入，
    生成飞书原生的标题、列表、粗体等格式；不再只创建空文档。
    """
    if not config.allow_write():
        return "写操作已关闭（FEISHU_BOT_ALLOW_WRITE=0）。"

    tmp_path = ""
    try:
        # lark-cli docs +create 支持直接导入 Markdown；用临时文件避免命令行转义/长度问题。
        # lark-cli 的安全策略要求文件必须位于当前目录、/tmp 或 ~/files，故显式指定 dir="/tmp"。
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".md", delete=False, dir="/tmp"
        ) as tmp:
            tmp.write(content or "")
            tmp_path = tmp.name

        args = [
            "docs",
            "+create",
            "--title",
            name,
            "--content",
            f"@{tmp_path}",
            "--doc-format",
            "markdown",
            "--as",
            "user",
        ]
        if folder_token:
            args.extend(["--parent-token", folder_token])

        r = cli.run(args)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    if not r.get("ok", True):
        err = r.get("error", {})
        return f"创建文档失败：{err.get('message', err.get('code', '未知错误'))}"
    if r.get("code", 0) != 0:
        return f"创建文档失败：{r.get('msg', '未知错误')}"

    data = r.get("data") or {}
    doc = data.get("document") or data
    doc_id = doc.get("document_id") or data.get("document_id")
    url = doc.get("url") or data.get("url") or (f"https://feishu.cn/docx/{doc_id}" if doc_id else "")

    result = f"已创建飞书文档：{name}\ndocument_id={doc_id}\n链接：{url}"
    if content:
        result += "\n已按 Markdown 自动转为飞书原生格式（标题、列表、粗体等）。"
    return result


# ---------- 身份 ----------

def t_whoami() -> str:
    r = cli.run(["whoami"])
    d = r if "identity" in r else r.get("data", {})
    if not d.get("identity"):
        return f"查询失败：{r.get('error', {}).get('message', r)}"
    who = d.get("onBehalfOf") or {}
    return f"身份：{d.get('identity')} / {who.get('userName', '?')} / token {d.get('tokenStatus', '?')}"


# ---------- 当天活动扫描（核心能力）----------

def scan_day_messages(day: str, max_chats: int = 25, per_chat: int = 30):
    """扫一遍全部会话，返回 ( [(会话名, [消息...])], error )。

    抽出来是为了让 ``t_daily_chats`` / ``t_my_activity`` 复用同一次扫描，
    避免重复打 API。
    """
    start, end = f"{day}T00:00:00+08:00", f"{day}T23:59:59+08:00"
    r = cli.run(["im", "+chat-list", "--as", "user", "--types", "p2p,group", "--page-size", "50"])
    if not r.get("ok"):
        return None, f"列会话失败：{r.get('error', {}).get('message', '未知错误')}"
    chats = (r.get("data", {}) or {}).get("chats") or []
    if not chats:
        return [], None

    result = []
    for c in chats[:max_chats]:
        cid, name = c.get("chat_id"), c.get("name") or "(无名)"
        if not cid:
            continue
        r2 = cli.run(["im", "+chat-messages-list", "--as", "user", "--chat-id", cid,
                      "--start", start, "--end", end, "--order", "asc", "--page-size", "50"])
        if not r2.get("ok"):
            continue
        d2 = r2.get("data", {})
        msgs = d2 if isinstance(d2, list) else (d2.get("messages") or d2.get("items") or [])
        if msgs:
            result.append((name, msgs[:per_chat]))
    return result, None


def render_messages(scan, day: str, whose: str = "all") -> str:
    """把扫描结果渲染成文本。whose: all / mine / others"""
    me = get_my_open_id()
    blocks = []
    total = mine_cnt = others_cnt = 0
    for name, msgs in scan:
        rows = []
        for m in msgs:
            sender = m.get("sender") or {}
            is_me = bool(me and sender.get("id") == me)
            if whose == "mine" and not is_me:
                continue
            if whose == "others" and is_me:
                continue
            total += 1
            mine_cnt += is_me
            others_cnt += (not is_me)
            tag = "[我]" if is_me else f"[{sender.get('name') or '对方'}]"
            t = m.get("create_time", "")[-5:] if m.get("create_time") else ""
            txt = formatter.parse_content(m).replace("\n", " ").strip() or f"[{m.get('msg_type', '非文本')}]"
            rows.append(f"  {t} {tag} {txt[:150]}")
        if rows:
            blocks.append(f"【{name}】{len(rows)} 条")
            blocks.extend(rows)

    if not blocks:
        scope = {"mine": "我发的", "others": "别人发的"}.get(whose, "")
        return f"{day} 没有{scope}对话记录。"
    head = f"{day} 对话汇总（共 {total} 条：我发 {mine_cnt} / 收到 {others_cnt}）"
    return head + "\n" + "\n".join(blocks)


def t_daily_chats(date: str | None = None, max_chats: int = 25,
                  per_chat: int = 30, whose: str = "all") -> str:
    """扫描全部会话，汇总当天对话。whose: all / mine / others"""
    day = date or formatter.today_str()
    scan, err = scan_day_messages(day, max_chats, per_chat)
    if err:
        return err
    return render_messages(scan, day, whose)


def t_my_activity(date: str | None = None) -> str:
    """今日完整活动快照：我的发言 + 全天对话 + 日程 + 任务（只扫一次会话）。"""
    day = date or formatter.today_str()
    scan, err = scan_day_messages(day)
    if err:
        return err
    parts = [
        f"【{day} 飞书活动总览】",
        "",
        "=== 一、我今天发出的消息 ===",
        render_messages(scan, day, whose="mine"),
        "",
        "=== 二、全天对话（含对方发言）===",
        render_messages(scan, day, whose="all"),
        "",
        "=== 三、日程 ===",
        t_agenda(day),
        "",
        "=== 四、任务 ===",
        t_tasks(),
    ]
    return "\n".join(parts)


def t_report(include_chats: bool = True) -> str:
    day = formatter.today_str()
    parts = [f"【{day} 日报】", "", "一、日程", t_agenda(), "", "二、任务", t_tasks()]
    if include_chats:
        parts += ["", "三、对话", t_daily_chats(day)]
    return "\n".join(parts)


# ---------- 工具注册表 ----------

TOOL_IMPL = {
    "get_agenda": lambda a: t_agenda(a.get("date")),
    "get_tasks": lambda a: t_tasks(),
    "get_daily_chats": lambda a: t_daily_chats(
        a.get("date"), int(a.get("max_chats", 25)), int(a.get("per_chat", 30)),
        a.get("whose", "all")),
    "get_my_activity": lambda a: t_my_activity(a.get("date")),
    "create_task": lambda a: t_create_task(a["summary"], a.get("due")),
    "create_event": lambda a: t_create_event(a["summary"], a["start"], a["end"], a.get("description")),
    "list_chats": lambda a: t_chats(),
    "search_messages": lambda a: t_search_messages(a["query"]),
    "send_message": lambda a: t_send_to(a["chat_id"], a["text"]),
    "reply_to_message": lambda a: t_reply_to_message(a["message_id"], a["text"]),
    "generate_report": lambda a: t_report(a.get("include_chats", True)),
    "whoami": lambda a: t_whoami(),
    "read_document": lambda a: t_read_document(a["url"]),
    "list_drive_files": lambda a: t_list_drive_files(a.get("folder_token"), int(a.get("limit", 20))),
    "find_free_time": lambda a: t_find_free_time(
        a.get("date"), int(a.get("duration_minutes", 30)),
        int(a.get("hour_start", 9)), int(a.get("hour_end", 18))),
    "task_search": lambda a: t_task_search(a.get("query"), int(a.get("limit", 15))),
    "create_bitable": lambda a: t_create_bitable(a["name"], a.get("workspace_token")),
    "create_spreadsheet": lambda a: t_create_spreadsheet(a["name"]),
    "create_doc": lambda a: t_create_doc(a["name"], a.get("folder_token"), a.get("content")),
}
