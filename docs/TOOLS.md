# 工具清单

以下 19 个能力由大模型通过 function calling 自主调用（也可在规则模式/降级模式下被关键词触发）。每个工具最终都通过 `lark-cli` 与飞书交互。

> 标记 ✏️ 的为写操作，受 `FEISHU_BOT_ALLOW_WRITE` 开关控制。

## 日程 / 任务

| 工具 | 说明 | 关键参数 |
|------|------|----------|
| `get_agenda` | 查询某天日程；不传 `date` 默认今天 | `date`: YYYY-MM-DD |
| `create_event` ✏️ | 创建日历日程/会议 | `summary`, `start`, `end`(ISO8601), `description?` |
| `find_free_time` | 查询某天某时段的空闲时间块，便于排会 | `date?`, `duration_minutes?`, `hour_start?`, `hour_end?` |
| `get_tasks` | 查询当前未完成任务 | — |
| `create_task` ✏️ | 新建待办 | `summary`, `due?`(ISO8601) |
| `task_search` | 按关键词搜索任务 | `query?`, `limit?` |

## 通信

| 工具 | 说明 | 关键参数 |
|------|------|----------|
| `list_chats` | 列出会话（群聊+单聊）及其 `chat_id` | — |
| `search_messages` | 按关键词搜索消息记录 | `query` |
| `send_message` ✏️ | 向指定会话发消息（需先 `list_chats` 拿 `chat_id`） | `chat_id`, `text` |
| `reply_to_message` ✏️ | 在指定消息下做线程回复 | `message_id`, `text` |

## 文档 / 云盘

| 工具 | 说明 | 关键参数 |
|------|------|----------|
| `read_document` | 读取飞书文档全文（贴 URL 即可） | `url` |
| `list_drive_files` | 列出云盘文件/文件夹（不传 `folder_token` 列根目录） | `folder_token?`, `limit?` |
| `create_bitable` ✏️ | 创建飞书多维表格（BaseApp） | `name`, `workspace_token?` |
| `create_spreadsheet` ✏️ | 创建飞书电子表格（类似 Excel） | `name` |
| `create_doc` ✏️ | 创建飞书文档（Docx，类似 Word）；`content` 会按 Markdown 导入为飞书原生格式 | `name`, `folder_token?`, `content?` |

## 信息 / 报告

| 工具 | 说明 | 关键参数 |
|------|------|----------|
| `whoami` | 查询当前登录身份与 token 状态 | — |
| `get_daily_chats` | 扫描所有会话，汇总某天对话；`whose` 可筛 `mine`/`others` | `date?`, `whose?`, `max_chats?`, `per_chat?` |
| `get_my_activity` | **核心能力**：某天完整活动总览 = 我发的消息 + 全天对话 + 日程 + 任务（只扫一次会话） | `date?` |
| `generate_report` | 生成当天日报（日程+任务+对话） | `include_chats?` |

## 设计约定

- 工具函数一律返回**字符串**给模型阅读；出错时返回带「失败/错误」字样的可读文本，绝不抛异常中断主循环。
- 工具名与 `schemas.TOOL_SCHEMA` 中的声明**一一对应**，由 `tests/test_tools.py` 的 `test_impl_keys_match_schema_names` 强制保证一致（19 对 19）。
- 涉及写操作前先确认参数完整；缺关键信息时模型会先反问用户，而不是直接报错。
