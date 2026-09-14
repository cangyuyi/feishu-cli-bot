# 专属飞书办公小助手 · Windows 安装教程

> 一个**本机常驻**的飞书 AI 助手：你只要在飞书里给它发消息，它就能查你的日程、待办、飞书活动，出日报，甚至帮你**新建飞书在线表格**。
> 全部运行在你自己电脑上，数据不离开本机（只调用你授权过的飞书账号和大模型 Key）。
>
> 本教程面向 **Windows 10 / 11** 用户，一步步照做即可，不需要会编程。

---

## 一、你需要准备什么

| 依赖 | 用途 | 获取方式 |
|---|---|---|
| **Python 3.9+** | 运行机器人本体（纯标准库，零第三方包） | python.org 下载安装 |
| **Node.js 18+** | 为飞书官方命令行 `lark-cli` 提供运行环境 | nodejs.org 下载安装 |
| **飞书账号** | 你自己的飞书，用来授权机器人读写你的消息/日程 | 已有 |
| **大模型 API Key** | 让机器人「会聊天、会思考」（OpenAI 兼容接口） | 火山方舟 / OpenAI / 硅基流动 等任选 |

> 💡 大模型推荐用**火山方舟豆包**（国内访问快、便宜）：注册后在「火山方舟」控制台创建 API Key，模型名填 `doubao-seed-2-1-pro-260628`。

---

## 二、安装依赖（只需一次）

### 1. 安装 Python
1. 打开 https://www.python.org/downloads/windows/
2. 下载 **Windows installer (64-bit)** 最新版。
3. 运行安装包，**务必勾选 `Add python.exe to PATH`**（最下面一行），然后点 `Install Now`。
4. 验证：打开「命令提示符」（Win+R → 输入 `cmd` → 回车），输入：
   ```bat
   py -3 --version
   ```
   能看到版本号（如 `Python 3.13.x`）就成功。

### 2. 安装 Node.js
1. 打开 https://nodejs.org/ ，下载 **LTS** 版（左侧绿色按钮）。
2. 一路下一步安装即可（默认会加进 PATH）。
3. 验证（重新开一个 cmd）：
   ```bat
   node -v
   npm -v
   ```
   都能输出版本号即成功。

### 3. 安装并授权飞书官方 CLI（lark-cli）
在 cmd 里执行：
```bat
npm install -g @larksuite/cli
```
装完后验证：
```bat
lark-cli --version
```
能输出版本号说明安装成功。

接着做**飞书账号授权**（设备码登录，安全）：
```bat
lark-cli auth login
```
屏幕会打印一个网址 + 一串验证码。用浏览器打开网址，登录你的飞书，输入验证码，点允许授权。
授权范围建议**全部允许**（消息 im / 日历 calendar / 任务 task / 云文档 docx / 多维表格 bitable）。授权完成会提示 `login success`。

> 若以后机器人回报「权限不足 / scope 不足」，重新跑一次 `lark-cli auth login` 刷新授权即可。

---

## 三、拿到你的私聊 chat_id（机器人要监听哪个会话）

机器人在**你和它的 1 对 1 私聊**里工作。先去飞书里找到 lark-cli 对应的机器人，给它发一条任意消息（这样才会生成 1 对 1 会话），然后在 cmd 里列出你的会话：

```bat
lark-cli im +chat-list --as user
```

输出里找你刚和机器人对话的那一条，复制它的 `chat_id`（形如 `oc_xxxxxxxxxxxxxxxxxxxx`）。
也可以确认身份：
```bat
lark-cli whoami
```

> 如果列表里没有机器人会话，先去飞书搜索「lark」或「飞书 CLI」相关机器人，发一条消息建立会话，再重跑上面的命令。

---

## 四、准备大模型 Key

以**火山方舟豆包**为例：
1. 打开 https://console.volcengine.com/ark
2. 开通「火山方舟」，创建一个 API Key（形如 `ak-xxxx`）。
3. 记下 Key 和模型名 `doubao-seed-2-1-pro-260628`。

（用 OpenAI / 硅基流动 / 本地 Ollama 也行，只要填对应的 `base_url` 和 `model`，见下一步注释。）

---

## 五、填写配置文件

机器人读取的配置文件路径是：
```
C:\Users\<你的用户名>\.feishu_bot_env
```

1. 在本项目目录里找到 `config\feishu_bot_env.example`，**复制一份**。
2. 把复制出来的文件**重命名**为 `.feishu_bot_env`（注意开头有个点）。
   - Windows 资源管理器可能不让文件名以点开头，保存时选「另存为」，文件名输入 `.feishu_bot_env.`（末尾多打个点，系统会自动去掉最后的空点），或用记事本「保存」时文件名加英文引号：`".feishu_bot_env"`。
3. 用记事本打开，按下面填：

```ini
# 大模型（必填）
FEISHU_BOT_LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
FEISHU_BOT_LLM_KEY=你刚拿到的Key
FEISHU_BOT_LLM_MODEL=doubao-seed-2-1-pro-260628

# 监听的会话（必填，第三步拿到的）
FEISHU_BOT_CHAT_ID=oc_xxxxxxxxxxxxxxxxxxxx

# 可选
FEISHU_BOT_INTERVAL=3
FEISHU_BOT_ALLOW_WRITE=1
FEISHU_BOT_TYPING=1
```

保存即可。这个文件含密钥，**不要发给别人、不要提交到网盘公开处**。

> 更省事的做法：也可以不建文件，直接在本机「系统设置 → 关于 → 高级系统设置 → 环境变量」里添加上面这些**用户变量**，效果一样。

---

## 六、首次运行与自检

进到本项目目录（含 `src` 文件夹那一层），在地址栏输入 `cmd` 回车，打开命令行，然后：

**先跑自检**，确认环境、授权、大模型都通（在项目根目录打开 cmd 执行）：
```bat
py -3 -m feishu_bot --selftest
```
看到 `大模型：已配置`、`工具连通性` 几行都是 `OK`、`消息收发：读取 OK` 就说明一切就绪。

如果某项 `FAIL`：
- `大模型` 未配置 → 检查第五步的 base_url / key。
- `whoami / 日程 / 任务` FAIL → 重新 `lark-cli auth login` 授权。
- `消息收发` 读取失败 → 检查 `FEISHU_BOT_CHAT_ID` 是否填对。

**正式运行（前台，方便看日志）：**
```bat
scripts\run.bat
```
窗口会持续打印日志。去飞书给机器人发一句「你好」，能回就成功了！按 `Ctrl+C` 可停止。

---

## 七、开机自启（后台常驻）

确认前台能正常回复后，配置开机自动运行：

1. 双击运行 `scripts\register-autostart.bat` → 会创建名为 **FeishuOfficeAssistant** 的任务计划，登录系统时自动在后台启动。
2. 想**立刻启动一次**（不用等重启）：双击 `scripts\start-hidden.bat`，机器人会在后台最小化窗口运行，日志写在项目根目录 `bot-poller.log`。
3. **重启电脑**验证：进桌面后直接去飞书给机器人发消息，能回即自启成功。

查看运行状态 / 日志：
```bat
# 看实时日志
type bot-poller.log

# 看是否在运行
tasklist | findstr python
```

**取消自启**：双击 `scripts\unregister-autostart.bat`。

---

## 八、进阶：让小助手「建飞书在线表格」

这是内置技能，只要授权里有 **bitable** 权限（第四步授权时全部允许即可），直接对机器人说：

- 「帮我建一张在线表格，叫 **客户跟进**」 → 建**多维表格**（结构化，可加字段）
- 「建一个电子表格，叫 **本周开销**」 → 建**在线 Excel**

它会返回表格链接，点开就能用。

> 如果建表回报权限错误，重跑 `lark-cli auth login` 确保勾选了 bitable 相关 scope。

### 其他能做的事（直接说就行）
- 「我今天有什么会 / 今天日程」
- 「我的待办」
- 「给我写一份今日日报」
- 「我是谁」（确认机器人身份）
- 「把这段话发给 XX：……」（先让它 `list_chats` 拿到对方 chat_id）

---

## 九、常见问题排查（FAQ）

**Q1：`lark-cli` 报 `command not found` / 不是内部或外部命令**
- 确认 `npm install -g @larksuite/cli` 成功，且 Node 安装时勾了「Add to PATH」。
- 重开一个 cmd 再试；仍不行就手动把 `%APPDATA%\npm` 加进系统 PATH。
- 极端情况：在 `.feishu_bot_env` 里加一行 `LARK_CLI=C:\Users\<你>\AppData\Roaming\npm\lark-cli.cmd`。

**Q2：机器人只回「规则模式」，不会自由对话**
- 大模型没配置上。检查 `.feishu_bot_env` 里 `FEISHU_BOT_LLM_BASE_URL` / `FEISHU_BOT_LLM_KEY` 是否填对，重跑 `--selftest` 看「大模型」那行。

**Q3：飞书里机器人不回我**
- 看日志 `bot-poller.log` 有没有「飞书机器人启动」「记忆 N 条」。
- `chat_id` 填错了最常见：用 `lark-cli im +chat-list --as user` 重新核对。
- 后台进程可能没起来：`tasklist | findstr python` 看有没有；没有就双击 `start-hidden.bat`。

**Q4：发消息说「写操作已关闭」**
- 在 `.feishu_bot_env` 设 `FEISHU_BOT_ALLOW_WRITE=1` 后重启机器人。

**Q5：重启后机器人没自启**
- 确认 `register-autostart.bat` 跑过；任务计划程序里看 `FeishuOfficeAssistant` 是否存在、是否在「登录时」触发。
- 也可去「任务计划程序 → FeishuOfficeAssistant → 属性 → 安全选项」勾「不管用户是否登录都要运行」。

**Q6：怎样彻底停掉机器人**
- 任务管理器结束 `python.exe` 进程；并跑 `unregister-autostart.bat` 取消自启。

---

## 十、项目结构（你拿到的压缩包）

```
feishu-cli-bot-windows/
├── README-Windows.md          # 本教程
├── README.md                   # 项目总说明（含技能清单）
├── config/
│   └── feishu_bot_env.example  # 配置模板（照抄填值）
├── src/feishu_bot/             # 机器人源码（纯 Python 标准库）
│   ├── cli.py                  # 飞书 CLI 封装（已兼容 Windows）
│   ├── bot.py                  # 主循环
│   ├── agent.py                # 大模型调用 + 工具调度
│   ├── tools.py                # 16 个飞书能力
│   ├── schemas.py              # 工具定义
│   └── ...
├── scripts/
│   ├── run.bat                 # 前台运行（测试用）
│   ├── start-hidden.bat        # 后台隐藏运行
│   ├── register-autostart.bat  # 注册开机自启
│   └── unregister-autostart.bat# 取消开机自启
├── tests/                      # 单元测试（开发者用）
├── docs/                       # 架构 / 工具文档
└── LICENSE                     # MIT 开源协议
```

## 十一、卸载
1. 跑 `scripts\unregister-autostart.bat` 取消自启。
2. 任务管理器结束 `python.exe`。
3. 删除整个项目文件夹，以及 `C:\Users\<你>\.feishu_bot_env`。

---

> 开源协议：MIT。可自由使用、修改、再分发。
> 项目地址（macOS/Linux 同源）：https://github.com/cangyuyi/feishu-cli-bot
