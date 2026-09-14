@echo off
REM ============================================================
REM 飞书办公小助手 - 前台运行（用于测试 / 调试）
REM 运行后会在当前窗口打印日志，按 Ctrl+C 停止。
REM ============================================================
cd /d "%~dp0\.."
set PYTHONPATH=%CD%\src

where py >nul 2>nul && set PY=py -3 || set PY=python
echo 使用 Python：%PY%
echo 项目目录：%CD%
echo 按 Ctrl+C 停止。
echo ============================================================
%PY% -m feishu_bot
pause
