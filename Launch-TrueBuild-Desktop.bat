@echo off
title TrueBuild Dual-Engine Desktop Launcher
cd /d "%~dp0"

echo ====================================================
echo   Launching TrueBuild Desktop Suite...
echo ====================================================

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at .\venv
    pause
    exit /b 1
)

venv\Scripts\python.exe desktop_app.py
