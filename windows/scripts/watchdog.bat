@echo off
REM ============================================================
REM 飞书办公小助手 - 看门狗（崩溃自愈，对应 macOS 的 watchdog.sh）
REM 循环启动 bot；bot 退出后等待 3 秒自动重启，连续崩溃 10 次则停止。
REM 由 start-hidden.bat 以最小化窗口方式调用。
REM ============================================================
cd /d "%~dp0\.."
set PYTHONPATH=%CD%\src
where py >nul 2>nul && set PY=py -3 || set PY=python
set LOG=%CD%\bot-poller.log
set FAIL=0

echo [%date% %time%] 看门狗启动，监控模块 feishu_bot >> "%LOG%"

:loop
%PY% -m feishu_bot >> "%LOG%" 2>&1
set CODE=%errorlevel%
echo [%date% %time%] bot 退出 (code=%CODE%)，3 秒后重启（第 %FAIL% 次）>> "%LOG%"
set /a FAIL+=1
if %FAIL% GEQ 10 (
    echo [%date% %time%] 连续崩溃 10 次，停止自愈，请检查日志：%LOG% >> "%LOG%"
    goto :end
)
REM 睡眠 3 秒（ping 比 timeout 兼容性更好）
ping -n 4 127.0.0.1 >nul
goto :loop

:end
