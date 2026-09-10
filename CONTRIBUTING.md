# 参与贡献

欢迎提 Issue / PR。本项目刻意保持**零第三方依赖**（仅 Python 标准库），请不要让运行时引入新依赖。

## 开发环境

```bash
cd feishu-cli-bot
python3 -m venv .venv && source .venv/bin/activate   # 可选，仅隔离即可
# 无需 pip install，直接 PYTHONPATH=src 运行
```

## 本地运行与测试

```bash
make lint        # 语法检查
make test        # 单元测试（unittest，零依赖）
make selftest    # 真实环境自检（需已授权 lark-cli）
```

新增工具时，请同时更新三处，保持一致：
1. `src/feishu_bot/tools.py` 里的实现 + `TOOL_IMPL` 注册
2. `src/feishu_bot/schemas.py` 里的 function calling 声明
3. 必要时在 `docs/TOOLS.md` 更新说明

`tests/test_tools.py::TestToolRegistryConsistency` 会自动校验「19 个实现 ⇄ 19 个 schema」是否一一对应，错位会立即失败。

## 提交规范

- 用中文或英文写清晰的 commit message，建议遵循 `feat:` / `fix:` / `docs:` / `refactor:` 前缀
- 提交前确保 `make test` 通过
- 不要提交任何密钥：`~/.feishu_bot_env`、`.env`、状态文件均已被 `.gitignore` 忽略

## 代码风格

- 模块、函数、关键分支写简洁的中文 docstring（项目面向中文场景）
- 标识符用英文，保持 PEP 8
- 优先用标准库；确需第三方库请先在 Issue 里讨论
