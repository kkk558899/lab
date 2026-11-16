@echo off
title 智能实验室预约系统 V1.0
chcp 65001 >nul

cd /d "%~dp0"

:: 优先以打包好的无黑框独立桌面程序启动
if exist "智能实验室预约系统.exe" (
    start "" "智能实验室预约系统.exe"
    exit /b
)

:: 兜底启动脚本
cd backend
start "" cmd /c ".venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
timeout /t 2 /nobreak >nul
start msedge --app=http://127.0.0.1:8000/
