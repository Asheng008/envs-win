@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在激活虚拟环境...
call .venv\Scripts\activate.bat

if errorlevel 1 (
    echo 错误：无法激活虚拟环境，请确保 .venv 文件夹存在
    pause
    exit /b 1
)

echo 虚拟环境已激活，正在运行程序...
python main.py

if errorlevel 1 (
    echo 程序执行出错
) else (
    echo 程序执行完成
)
