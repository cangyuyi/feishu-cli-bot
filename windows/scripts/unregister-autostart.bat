@echo off
REM ============================================================
REM 取消「开机自启」任务（删除任务计划程序中的注册）
REM ============================================================
set TASK=FeishuOfficeAssistant

schtasks /delete /tn "%TASK%" /f
if %errorlevel%==0 (
    echo [OK] 已删除开机自启任务：%TASK%
) else (
    echo [提示] 未找到任务 %TASK%（可能本来就未注册）。
)
pause
