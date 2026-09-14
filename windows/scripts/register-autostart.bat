@echo off
REM ============================================================
REM 注册「开机自启」任务（Windows 任务计划程序）
REM 登录系统后自动以最小化窗口运行小助手，崩溃会自动重试。
REM 需要以当前用户身份运行（双击即可，无需管理员）。
REM ============================================================
set ROOT=%~dp0\..
set TASK=FeishuOfficeAssistant

schtasks /create /tn "%TASK%" /tr "\"%ROOT%\scripts\start-hidden.bat\"" /sc onlogon /rl highest /f
if %errorlevel%==0 (
    echo.
    echo [OK] 已创建开机自启任务：%TASK%
    echo      登录系统后小助手会自动在后台运行。
    echo      立即启动一次？运行：scripts\start-hidden.bat
) else (
    echo.
    echo [失败] 创建任务计划失败。请确认以当前用户（非 Guest）运行，
    echo        或在「任务计划程序」中手动新建：触发器=登录时，操作=启动 %ROOT%\scripts\start-hidden.bat
)
pause
