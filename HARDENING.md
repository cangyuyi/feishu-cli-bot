# 安全与稳健性审计响应（audit-hardening 分支）

本分支针对 `feishu-cli-bot` 项目不足点审计（2026-09-14，64 条）中的**低风险、纯稳健性**项做了加固。
目标：不改变机器人对外行为，只提升健壮性、可观测性与启动安全性。
本地 `main` 分支与运行中的机器人保持原版未动；本分支为独立改进，待确认后再合并。

## 本次已修复（对应审计条目）

| 审计项 | 修复内容 | 文件 |
|--------|----------|------|
| #9 测试写死 `18` 个工具 | 改为动态校验 `set(TOOL_IMPL) == set(TOOL_SCHEMA)`，不再写死数量；CI 恢复全绿 | `tests/test_tools.py` |
| #10 lark-cli 无超时 | `subprocess.run` 增加 `timeout`（默认 60s，可经 `LARK_CLI_TIMEOUT` 调整）；超时返回结构化错误而非永久阻塞 | `cli.py` |
| #11 未充分检查返回码 | 解析失败时优先看 `proc.returncode != 0` 判失败，避免「非 0 退出但被当成功」 | `cli.py` |
| #12 未知响应默认成功 | `_succeeded` 在响应既无 `ok` 也无 `code` 时判**失败**，不再默认成功 | `cli.py` |
| #13 stdout/stderr 处理 | 优先解析 `stdout` 的 JSON，回退 `stderr`；均无 JSON 时以错误文本返回，不再隐藏真实错误 | `cli.py` |
| #14 重试依赖关键词 | 明确排除确定性失败：4xx（除 429）、权限/参数/范围类错误不重试 | `cli.py` |
| #26 状态非原子写入 | `save_state` 改为「临时文件 + fsync + `os.replace`」原子替换，避免半截 JSON | `storage.py` |
| #27 状态损坏静默清空 | `load_state` 损坏时复制为 `.corrupt-<时间戳>` 备份并打印告警，不再静默当空 | `storage.py` |
| #33 配置异常静默 | `load_env_file` 解析异常改为打印 `[config] 警告`，不再 `pass` 吞掉 | `config.py` |
| #34 非法配置崩溃 | `INTERVAL`/`HISTORY_MAX`/`HISTORY_TOKEN_BUDGET`/`MAX_TOOL_ROUNDS` 改用 `_safe_int` 安全解析，非法值回退默认值并告警（同时让轮数可经环境变量调整，部分回应 #19） | `config.py` |

## 验证

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -t .   # 36 passed
PYTHONPATH=src python3 -m feishu_bot --selftest            # 工具连通 OK
```

## 暂未做（属架构级大改，需另立项，避免破坏现有可用版本）

以下项改动会触及消息处理主流程、权限模型或整体架构，风险较高，不在本分支处理：

- #1 程序级写操作确认（预览→用户确认→执行）
- #4 工具级 / 用户级 / 群聊级权限
- #5 发送消息收件人白名单与二次确认
- #6 写操作幂等键
- #7 消息处理状态机（received/processing/sent/failed…）
- #16/#17 工具参数统一校验与解析失败回传模型
- #22 事件订阅 / WebSocket 替代轮询
- #29/#30 工具上下文与裁剪结构完整性
- #31 token 估算精度（需真实 tokenizer）
- #36 凭证文件权限自动检查
- #39 完整审计日志、#41 速率限制、#42 错误信息脱敏
- #50/#51/#52/#53 单一工具来源、Tool 对象化、Provider 抽象、lark-cli 版本约束
- #62/#63 多租户 / 分层架构

> 说明：审计中提到的 Prompt Injection 防护、敏感数据脱敏、数据出境提示等，根因在于「将飞书数据发给外部 LLM」这一设计选择。若要彻底解决需引入本地模型模式与数据脱敏层，建议作为后续独立方向评估。

## 合并方式

确认无问题后：

```bash
git checkout main
git merge audit-hardening
git push origin main
# 重启机器人：pkill -f feishu_bot && bash scripts/launch.command
```
