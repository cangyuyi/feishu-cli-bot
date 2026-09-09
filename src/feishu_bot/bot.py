"""机器人主循环：轮询新消息 → 调用 Agent 生成回复 → 回写飞书。

同时负责：
- 收到消息先发一个「正在输入」表情，避免用户干等
- 把已处理消息 ID 与对话记忆持久化，重启可续
- 提供 --selftest / --once / --clear 等运维子命令
"""
import argparse
import os
import time

from . import agent
from . import cli
from . import config
from . import formatter
from . import storage
from . import tools


def list_messages_desc() -> list:
    """拉取监听会话里最新的消息（倒序）。"""
    r = cli.run([
        "im", "+chat-messages-list", "--as", "user",
        "--chat-id", config.CHAT_ID, "--order", "desc", "--page-size", "10",
    ])
    if not r.get("ok"):
        return []
    data = r.get("data", {})
    if isinstance(data, list):
        return data
    return data.get("messages") or data.get("items") or []


def send(text: str) -> bool:
    """以机器人身份在监听会话里发送一条消息。"""
    r = cli.run(["im", "+messages-send", "--as", "bot", "--chat-id", config.CHAT_ID, "--text", text])
    return r.get("ok") is True


def send_typing() -> bool:
    """发送飞书内置的「正在输入」表情，让用户知道机器人在处理。

    ``[Typing]`` 是飞书官方特殊表情，发送后会显示打字动画。
    可用 ``FEISHU_BOT_TYPING=0`` 关闭。撤回消息属 high-risk-write（需人工确认），故不自动删除。
    """
    if os.environ.get("FEISHU_BOT_TYPING", "1") != "1":
        return False
    r = cli.run(["im", "+messages-send", "--as", "bot", "--chat-id", config.CHAT_ID, "--text", "[Typing]"])
    return r.get("ok") is True


def process_new(state: dict, verbose: bool = True) -> None:
    """处理监听会话里的新消息（已处理过的按 message_id 去重）。"""
    last_id = state.get("last_message_id")
    history = state.get("history", [])
    msgs = list_messages_desc()

    new_msgs = []
    for m in msgs:
        if m.get("message_id") == last_id:
            break
        if m.get("sender", {}).get("sender_type") == "user":
            new_msgs.append(m)
    new_msgs.reverse()

    # 收到消息先回一个「正在输入」，避免用户干等（LLM + 工具可能要好几秒）
    if new_msgs and send_typing():
        if verbose:
            print(f"[{time.strftime('%H:%M:%S')}] [typing] 已提示正在输入", flush=True)

    for m in new_msgs:
        text = formatter.parse_content(m)
        if not text.strip():
            continue
        reply = agent.generate_reply(text, history)
        if not reply:
            continue
        if send(reply):
            history.append({"role": "user", "content": text})
            history.append({"role": "assistant", "content": reply})
            state["history"] = history[-config.HISTORY_MAX:]
            state["last_message_id"] = m["message_id"]
            storage.save_state(state)
            if verbose:
                ts = time.strftime("%H:%M:%S")
                preview = reply.replace("\n", " / ")[:70]
                print(f"[{ts}] ← {text[:30]}  →  {preview}", flush=True)


def selftest() -> None:
    """环境/授权/工具自检。"""
    print("=== 飞书机器人自检 ===")
    print(f"chat_id        : {config.CHAT_ID}")
    print(f"配置文件        : {config.ENV_FILE} {'存在' if os.path.exists(config.ENV_FILE) else '不存在'}")
    print(f"大模型          : {'已配置' if config.llm_configured() else '未配置（规则模式）'}")
    if config.llm_configured():
        print(f"  base_url     : {os.environ.get('FEISHU_BOT_LLM_BASE_URL')}")
        print(f"  model        : {os.environ.get('FEISHU_BOT_LLM_MODEL', 'gpt-4o-mini')}")
    print(f"写操作          : {'允许' if config.allow_write() else '禁止'}")
    print(f"轮询间隔        : {config.INTERVAL}s")
    print("\n--- 工具连通性 ---")
    for name, fn in (("whoami", tools.t_whoami), ("日程", tools.t_agenda), ("任务", tools.t_tasks)):
        try:
            r = fn()
            head = r.replace("\n", " / ")[:70]
            print(f"  {name:6s}: OK  {head}")
        except Exception as exc:  # noqa: BLE001
            print(f"  {name:6s}: FAIL {type(exc).__name__}: {exc}")
    print("\n--- 消息收发 ---")
    msgs = list_messages_desc()
    print(f"  读取  : {'OK，最近 ' + str(len(msgs)) + ' 条' if msgs else '无消息或读取失败'}")
    if msgs:
        last = msgs[0]
        print(f"  最新  : [{last.get('create_time')}] {formatter.parse_content(last)[:40]}")


def main() -> None:
    p = argparse.ArgumentParser(description="飞书 CLI 机器人（本地常驻 AI 助手）")
    p.add_argument("--once", action="store_true", help="只跑一轮轮询后退出")
    p.add_argument("--clear", action="store_true", help="清空对话记忆")
    p.add_argument("--selftest", action="store_true", help="环境/授权/工具自检")
    args = p.parse_args()

    if args.selftest:
        selftest()
        return

    state = storage.load_state()
    if args.clear:
        state["history"] = []
        storage.save_state(state)
        print("[clear] 记忆已清空")
        return

    if args.once:
        process_new(state)
        return

    print(f"[{time.strftime('%H:%M:%S')}] 飞书机器人启动 chat_id={config.CHAT_ID} interval={config.INTERVAL}s", flush=True)
    print(f"[{time.strftime('%H:%M:%S')}] 记忆 {len(state.get('history', []))} 条 / 起点 {state.get('last_message_id')}", flush=True)
    print(f"[{time.strftime('%H:%M:%S')}] 大模型：{'已接入（Agent 模式）' if config.llm_configured() else '未配置（规则模式）'}"
          f" / 写操作：{'开' if config.allow_write() else '关'}", flush=True)

    while True:
        try:
            process_new(state)
        except KeyboardInterrupt:
            print("\n[stop] bye")
            break
        except Exception as exc:  # noqa: BLE001 - 单轮异常不影响常驻
            print(f"[{time.strftime('%H:%M:%S')}] 异常: {exc}", flush=True)
        time.sleep(config.INTERVAL)


if __name__ == "__main__":
    main()
