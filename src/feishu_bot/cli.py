"""lark-cli 封装层。

本机器人不直接调用飞书开放平台 API，而是复用已授权的 ``lark-cli``
（飞书官方命令行工具），用两种身份执行操作：

- ``--as user`` ：以当前登录用户身份「读」消息（双向对话的关键）
- ``--as bot``  ：以机器人身份「发」消息（绕过开放平台后台的回调配置）

这样无需 App Secret、无需在开发者后台配置事件订阅即可跑起来。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time


def _win_quote(s: str) -> str:
    """Windows 命令行参数转义：含空格/特殊字符时用双引号包裹，内部双引号转义。"""
    if any(c in s for c in ' \t"&|<>()^%'):
        return '"' + s.replace('"', '\\"') + '"'
    return s


def _resolve_lark_cli() -> str:
    """定位 lark-cli 可执行文件。

    优先级：
      1) 环境变量 ``LARK_CLI``（显式指定，便于 Windows 用户指向 npm 全局路径）
      2) PATH 查找（含 Windows 上的 ``lark-cli.cmd`` / ``lark-cli.ps1``）
      3) 常见安装路径（WorkBuddy 内置、Homebrew、系统、Windows npm 全局）
      4) 兜底路径（即便不存在也返回，便于报错提示）
    """
    env_path = os.environ.get("LARK_CLI")
    if env_path:
        return env_path
    found = shutil.which("lark-cli")
    if found:
        return found
    if os.name == "nt":
        # Windows 上 npm 全局安装的 lark-cli 常是 .cmd / .ps1
        for ext in (".cmd", ".ps1", ".bat"):
            found = shutil.which("lark-cli" + ext)
            if found:
                return found
    candidates = [
        os.path.expanduser("~/AppData/Roaming/npm/lark-cli.cmd"),
        os.path.expanduser("~/AppData/Roaming/npm/lark-cli.ps1"),
        os.path.expanduser("~/.workbuddy/binaries/node/cli-connector-packages/bin/lark-cli"),
        "/usr/local/bin/lark-cli",
        "/opt/homebrew/bin/lark-cli",
        "/usr/bin/lark-cli",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    # 兜底：即便不存在也返回一个可读路径，便于报错提示
    return candidates[-1]


# 脱离子进程（登录项/后台）后 PATH 与可执行查找都可能失效，故一次性解析并缓存
LARK_CLI = _resolve_lark_cli()


# 调用失败时的重试策略（只重试「瞬时错误」，避免掩盖确定性失败）
MAX_RETRIES = int(os.environ.get("LARK_CLI_MAX_RETRIES", "3"))
RETRY_BACKOFF = float(os.environ.get("LARK_CLI_RETRY_BACKOFF", "1.0"))

# 命中以下关键词视为「瞬时错误」，可安全重试（网络抖动 / 飞书限流 / 5xx）
_TRANSIENT_HINTS = (
    "timeout", "timed out", "429", "rate limit", "too many requests",
    "connection", "econn", "reset by peer", "network", "502", "503", "504",
    "temporarily", "try again", "internal error", "server error", "broken pipe",
    "resource temporarily unavailable",
)


def _is_transient_error(r: dict) -> bool:
    err = r.get("error")
    msg = (err.get("message", "") if isinstance(err, dict) else str(err or ""))
    return any(h in msg.lower() for h in _TRANSIENT_HINTS)


def _succeeded(r: dict) -> bool:
    """lark-cli 信封带 ``ok`` 字段；OpenAPI 原始信封带 ``code`` 字段（code=0 成功、无 ok）。"""
    if r.get("ok") is True:
        return True
    if r.get("ok") is False:
        return False
    return r.get("code", 0) == 0


def _run_once(args: list) -> dict:
    """执行一次 lark-cli 调用并解析 JSON 结果（不含重试）。"""
    looks_like_path = (os.sep in LARK_CLI) or (os.altsep is not None and os.altsep in LARK_CLI)
    if looks_like_path and not os.path.exists(LARK_CLI):
        return {
            "ok": False,
            "error": {"message": f"未找到 lark-cli：{LARK_CLI}。请先安装并授权 lark-cli（或设置环境变量 LARK_CLI 指向它）。"},
        }
    # Windows 下 lark-cli 通常是 .cmd / .bat，需要经 cmd /c 执行（避免 CreateProcess 无法直启脚本）
    if os.name == "nt" and LARK_CLI.lower().endswith((".cmd", ".bat")):
        inner = " ".join(_win_quote(a) for a in args)
        cmd = ["cmd.exe", "/c", f'"{LARK_CLI}" {inner}']
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError:
            return {"ok": False, "error": {"message": f"无法执行 lark-cli：{LARK_CLI}（请确认已安装 Node.js 与 lark-cli）"}}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": {"message": f"{type(exc).__name__}: {exc}"}}
    else:
        cmd = [LARK_CLI, *args]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError:
            return {"ok": False, "error": {"message": f"无法执行 lark-cli：{LARK_CLI}"}}
        except Exception as exc:  # noqa: BLE001 - 任何异常都要兜底成可解析的错误结构
            return {"ok": False, "error": {"message": f"{type(exc).__name__}: {exc}"}}

    raw = (proc.stdout or proc.stderr or "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # 非 JSON 输出（例如帮助文本、授权提示）按错误回显前 200 字
        return {"ok": False, "error": {"message": raw[:200] or "lark-cli 无输出"}}


def run(args: list) -> dict:
    """调用 lark-cli 并把 stdout/stderr 的 JSON 解析成 dict。

    带「瞬时错误指数退避重试」：只重试网络抖动、飞书限流（429）、5xx 等可恢复错误；
    确定性失败（lark-cli 未安装、参数错误、权限不足）不重试，直接返回，避免误导上层。
    """
    last = None
    for attempt in range(1, MAX_RETRIES + 1):
        last = _run_once(args)
        if _succeeded(last):
            return last
        if attempt < MAX_RETRIES and _is_transient_error(last):
            wait = RETRY_BACKOFF * (2 ** (attempt - 1))
            time.sleep(wait)
            continue
        return last
    return last
