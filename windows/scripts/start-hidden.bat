@echo off
REM ============================================================
REM 飞书办公小助手 - 后台隐藏运行
REM 以「最小化窗口」方式启动，日志写入项目根目录 bot-poller.log
REM 适用于日常常驻；配合 register-autostart.bat 可实现开机自启。
REM ============================================================
cd /d "%~dp0\.."
set PYTHONPATH=%CD%\src

where py >nul 2>nul && set PY=py -3 || set PY=python
echo 使用 Python：%PY%
echo 项目目录：%CD%
echo 日志文件：%CD%\bot-poller.log

start "FeishuBot" /min cmd /c "%~dp0watchdog.bat"
echo 已后台启动（窗口已最小化，看门狗负责崩溃自愈）。查看日志：type bot-poller.log
echo 停止：结束 watchdog.bat 与 python 进程，或运行 unregister 前先关掉。
pause
