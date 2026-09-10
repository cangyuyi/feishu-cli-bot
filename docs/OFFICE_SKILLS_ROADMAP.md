# 飞书办公小助手 · 可扩展技能清单

> 当前已实现 **19 个**工具。下面按办公场景列出还能增加的能力，供你按优先级挑选。
> 优先级：🔴 高（常用、价值大） / 🟡 中（有场景） / 🟢 低（锦上添花）
> 难度：⭐ 易（单 API） / ⭐⭐ 中（需组装） / ⭐⭐⭐ 难（多步骤/复杂解析）

---

## 一、文档类（Docs / Slides / Wiki）

| 技能 | 说明 | 优先级 | 难度 | 实现要点 |
|------|------|--------|------|----------|
| `create_doc` | 创建飞书文档（Docx） | ✅ 已做 | — | `POST /open-apis/docx/v1/documents` |
| `append_to_doc` | 往已有 Docx 文档追加段落/图片/表格 | 🔴 高 | ⭐⭐ | 需先 `GET /docx/v1/documents/{id}` 取 blocks，再 `POST /docx/v1/documents/{id}/blocks/batch_create` |
| `create_slides` | 创建飞书幻灯片（PPT） | 🟡 中 | ⭐ | `POST /open-apis/slides/v1/presentations` 或 `lark-cli slides create` |
| `create_wiki_space` | 创建飞书知识库空间 | 🟡 中 | ⭐ | `POST /open-apis/wiki/v2/spaces` |
| `share_doc` | 设置文档分享/权限（全员可读、指定人编辑等） | 🟡 中 | ⭐⭐ | `POST /open-apis/drive/v1/permissions/{token}/public` 或类似权限 API |
| `export_doc` | 导出文档为 PDF / Word | 🟢 低 | ⭐⭐ | 飞书支持异步导出，需轮询任务状态 |

---

## 二、表格类（Bitable / Spreadsheet）

| 技能 | 说明 | 优先级 | 难度 | 实现要点 |
|------|------|--------|------|----------|
| `create_bitable` | 创建多维表格 | ✅ 已做 | — | `POST /open-apis/bitable/v1/apps` |
| `create_spreadsheet` | 创建电子表格 | ✅ 已做 | — | `lark-cli sheets spreadsheets create` |
| `add_bitable_records` | 往多维表格追加记录 | 🔴 高 | ⭐ | `POST /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records` |
| `query_bitable` | 按条件查询多维表格记录 | 🟡 中 | ⭐⭐ | 需先列 table / field，再 `POST /search` 或逐条过滤 |
| `add_spreadsheet_values` | 往电子表格写单元格 | 🟡 中 | ⭐ | `lark-cli sheets values update` 或 raw API `PUT /sheets/v2/spreadsheets/{token}/values` |
| `create_bitable_fields` | 给多维表格新增字段/列 | 🟡 中 | ⭐ | `POST /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields` |

---

## 三、日程 / 任务

| 技能 | 说明 | 优先级 | 难度 | 实现要点 |
|------|------|--------|------|----------|
| `get_agenda` | 查日程 | ✅ 已做 | — | `lark-cli calendar +agenda` |
| `create_event` | 建日程 | ✅ 已做 | — | `lark-cli calendar +create` |
| `find_free_time` | 查空闲时段 | ✅ 已做 | — | `lark-cli calendar +suggestion` |
| `get_tasks` / `create_task` / `task_search` | 任务相关 | ✅ 已做 | — | `lark-cli task` |
| `complete_task` | 完成任务 | 🟡 中 | ⭐ | `lark-cli task +complete` |
| `delete_event` | 删除日程 | 🟢 低 | ⭐ | `lark-cli calendar +delete` |
| `list_calendars` | 列出我拥有的日历 | 🟢 低 | ⭐ | `lark-cli calendar +calendar-list` |

---

## 四、通信协作

| 技能 | 说明 | 优先级 | 难度 | 实现要点 |
|------|------|--------|------|----------|
| `list_chats` / `send_message` / `reply_to_message` / `search_messages` | 消息相关 | ✅ 已做 | — | `lark-cli im` |
| `create_group` | 创建群聊 | 🟡 中 | ⭐ | `lark-cli im +chat-create` |
| `add_group_members` | 拉人进群 | 🟡 中 | ⭐ | `lark-cli im +chat-members-add` |
| `send_card` | 发送交互卡片（按钮、表单） | 🟡 中 | ⭐⭐ | `lark-cli im +messages-send --msg-type interactive` |
| `set_group_announcement` | 设置群公告 | 🟢 低 | ⭐⭐ | 需 chat_id + 文本 |

---

## 五、云盘

| 技能 | 说明 | 优先级 | 难度 | 实现要点 |
|------|------|--------|------|----------|
| `list_drive_files` | 列文件 | ✅ 已做 | — | `lark-cli drive files list` |
| `create_folder` | 创建云盘文件夹 | 🟡 中 | ⭐ | `POST /open-apis/drive/v1/files/create_folder` |
| `upload_file` | 上传文件到云盘 | 🟡 中 | ⭐⭐ | 需分片上传大文件，小文件可走 `POST /open-apis/drive/v1/files/upload_all` |
| `share_drive_file` | 分享云盘文件/文件夹 | 🟢 低 | ⭐⭐ | 与文档分享 API 类似 |

---

## 六、会议 / 审批 / 邮箱

| 技能 | 说明 | 优先级 | 难度 | 实现要点 |
|------|------|--------|------|----------|
| `create_meeting` | 预约视频会议 | 🟡 中 | ⭐ | `lark-cli vc +create` 或 calendar 建日程时带 vc 配置 |
| `get_meeting_minutes` | 获取妙记/会议纪要 | 🟡 中 | ⭐⭐ | `lark-cli minutes` / `lark-cli meeting` 系列 |
| `create_approval` | 发起审批实例 | 🟢 低 | ⭐⭐ | 需知道审批定义 code 和表单字段 |
| `send_email` | 通过飞书邮箱发邮件 | 🟢 低 | ⭐⭐ | 需 mail:send 权限，走 `lark-cli mail` |

---

## 七、搜索 / 智能

| 技能 | 说明 | 优先级 | 难度 | 实现要点 |
|------|------|--------|------|----------|
| `search_docs` | 按关键词搜索飞书文档 | 🔴 高 | ⭐⭐ | `lark-cli docs +search` 或 `drive/v1/files?search` |
| `search_contacts` | 搜索联系人/用户 | 🟡 中 | ⭐ | `lark-cli contact +search` |
| `translate` | 翻译文本 | 🟢 低 | ⭐ | `lark-cli translation +text` |
| `ocr_image` | OCR 识别图片中的文字 | 🟢 低 | ⭐⭐ | 需先下载图片再调 OCR API |

---

## 推荐下一步（3 个）

如果你只想再补几个最实用的，我建议：

1. **`append_to_doc`** —— 创建文档后通常要往里写内容，闭环价值最大。
2. **`add_bitable_records`** —— 让机器人能把对话/数据直接写入多维表格，配合 `create_bitable` 完成「建表→填数」。
3. **`search_docs`** —— 机器人能基于你的文档库做问答/检索，扩展性最强。
