"""OpenAI 兼容的 function calling 工具声明（schema）。

大模型根据这里的描述自主决定调用哪个工具、传什么参数。
顺序与 :data:`feishu_bot.tools.TOOL_IMPL` 中的实现一一对应。
"""
from __future__ import annotations


TOOL_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_agenda",
            "description": "查询某天的日程安排。不传 date 则默认今天。",
            "parameters": {
                "type": "object",
                "properties": {"date": {"type": "string", "description": "YYYY-MM-DD 格式日期"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_tasks",
            "description": "查询当前未完成任务列表。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_daily_chats",
            "description": "扫描所有飞书会话（群聊+单聊），汇总指定日期当天的对话。每条用 [我] / [对方名] 标记发送方。whose=all 全部 / mine 只看我发的 / others 只看别人发的。不传 date 则默认今天。",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "YYYY-MM-DD 格式日期"},
                    "whose": {
                        "type": "string",
                        "enum": ["all", "mine", "others"],
                        "description": "筛选发送方：all=全部 / mine=只看我发的 / others=只看别人发的",
                    },
                    "max_chats": {"type": "integer", "description": "最多扫描多少个会话，默认 25"},
                    "per_chat": {"type": "integer", "description": "每个会话最多取多少条，默认 30"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_my_activity",
            "description": "获取某天完整的飞书活动总览：我发出的所有消息 + 全天对话 + 日程 + 任务。用户问「我今天做了什么」「我的飞书活动」时优先用这个。",
            "parameters": {
                "type": "object",
                "properties": {"date": {"type": "string", "description": "YYYY-MM-DD 格式日期"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "创建一个新的待办任务。",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "任务标题"},
                    "due": {"type": "string", "description": "截止时间 ISO8601，如 2026-09-10T18:00:00+08:00"},
                },
                "required": ["summary"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_event",
            "description": "创建日历日程/会议。",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "日程标题"},
                    "start": {"type": "string", "description": "开始时间 ISO8601，如 2026-09-10T15:00:00+08:00"},
                    "end": {"type": "string", "description": "结束时间 ISO8601"},
                    "description": {"type": "string", "description": "备注"},
                },
                "required": ["summary", "start", "end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_chats",
            "description": "列出飞书会话（群聊和单聊）及其 chat_id。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_messages",
            "description": "按关键词搜索飞书消息记录。",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "搜索关键词"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_message",
            "description": "向指定会话发送消息。需先通过 list_chats 获取 chat_id。",
            "parameters": {
                "type": "object",
                "properties": {
                    "chat_id": {"type": "string", "description": "目标会话 oc_xxx"},
                    "text": {"type": "string", "description": "消息内容"},
                },
                "required": ["chat_id", "text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_report",
            "description": "生成当天日报，汇总日程、任务与全天对话。",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_chats": {
                        "type": "boolean",
                        "description": "是否包含当天对话汇总，默认 true",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "whoami",
            "description": "查询当前登录的飞书身份与 token 状态。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_document",
            "description": "读取飞书文档全文。用户贴任意飞书文档 URL 即可读出 Markdown 内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "飞书文档完整 URL 或 token"}
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_drive_files",
            "description": "列出云盘文件/文件夹。folder_token 不传则列根目录。需要 drive 相关 scope，未授权时会回显失败信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_token": {"type": "string", "description": "文件夹 token；不传则根目录"},
                    "limit": {"type": "integer", "description": "返回数量上限，默认 20"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_free_time",
            "description": "查询某天某时段内的空闲时间块，用于排会议或安排任务。",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "YYYY-MM-DD，不传则今天"},
                    "duration_minutes": {"type": "integer", "description": "所需时长（分钟），默认 30"},
                    "hour_start": {"type": "integer", "description": "时段起点（0-23），默认 9"},
                    "hour_end": {"type": "integer", "description": "时段终点（0-23），默认 18"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "task_search",
            "description": "按关键词搜索任务（标题/描述/列表），支持已完成/未完成过滤。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "limit": {"type": "integer", "description": "返回数量上限，默认 15"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reply_to_message",
            "description": "在指定消息（message_id）下做线程回复，需与机器人同会话内。",
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {"type": "string", "description": "目标消息 ID（om_xxx）"},
                    "text": {"type": "string", "description": "回复内容"},
                },
                "required": ["message_id", "text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_bitable",
            "description": "创建一个新的飞书多维表格（BaseApp，结构化在线表格，可后续加字段/记录）。用户说「建一张在线表格/多维表格/在线数据库」时优先用。folder_token 可选，不传则建在用户默认空间，无需预先配置即可一键建表。返回 app_token 与访问链接。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "多维表格名称"},
                    "workspace_token": {
                        "type": "string",
                        "description": "飞书空间/文件夹 token；不传则用默认空间（可在 ~/.feishu_bot_env 配 FEISHU_BOT_WORKSPACE_TOKEN）",
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_spreadsheet",
            "description": "创建一个新的飞书电子表格（类似 Excel 的在线表格）。用户说「建一个电子表格/在线 Excel 表格」时用。返回 spreadsheetToken 与访问链接。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "电子表格标题"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_doc",
            "description": "创建一个新的飞书文档（Docx，类似 Word 的在线文档）。用户说「建一个文档/飞书文档/Word 文档」时优先用。返回 document_id 与访问链接。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "文档标题"},
                    "folder_token": {"type": "string", "description": "父文件夹 token；不传则建在默认空间"},
                },
                "required": ["name"],
            },
        },
    },
]
