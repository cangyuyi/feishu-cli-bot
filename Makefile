# feishu-cli-bot 常用命令
# 用法：make <target>

PY ?= python3
SRC := src/feishu_bot

.PHONY: help install dev test run once selftest clear lint format

help:  ## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install:  ## 安装（可编辑模式）
	$(PY) -m pip install -e .

dev:  ## 安装开发依赖
	$(PY) -m pip install -e ".[dev]"

test:  ## 运行单元测试（标准库 unittest，无需第三方依赖）
	$(PY) -m unittest discover -s tests -t . -v

run:  ## 持续运行机器人
	$(PY) -m feishu_bot

once:  ## 只跑一轮轮询
	$(PY) -m feishu_bot --once

selftest:  ## 环境/授权/工具自检
	$(PY) -m feishu_bot --selftest

clear:  ## 清空对话记忆
	$(PY) -m feishu_bot --clear

lint:  ## 语法检查（无需第三方依赖）
	$(PY) -m py_compile $(SRC)/*.py tests/*.py

format:  ## 代码格式化（需 black，可选）
	$(PY) -m black $(SRC) tests
