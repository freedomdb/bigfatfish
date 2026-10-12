@echo off
title BigFatFish Desktop
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.8+ from https://www.python.org/downloads/
    echo Remember to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
start "" /min pythonw "%~dp0app.py"
