@echo off
chcp 65001 >nul
cd /d %~dp0

echo ============================================
echo     微信AI自动回复机器人
echo ============================================
echo.
echo 请确保:
echo   1. 微信PC客户端已打开并登录
echo   2. 微信版本为 3.9.11.17
echo.
echo ============================================
echo.
echo 选择模式:
echo   1. 轮询模式 (监听所有私聊)
echo   2. 监听模式 (最多5个会话)
echo   3. 交互模式
echo   4. 测试发送
echo.

set /p mode="请输入 (1/2/3/4): "

if "%mode%"=="1" (
    .venv\Scripts\python wxauto_bot.py --run
) else if "%mode%"=="2" (
    .venv\Scripts\python wxauto_bot.py --listen
) else if "%mode%"=="3" (
    .venv\Scripts\python wxauto_bot.py --interactive
) else if "%mode%"=="4" (
    .venv\Scripts\python wxauto_bot.py --test
) else (
    echo 无效选项
)

pause