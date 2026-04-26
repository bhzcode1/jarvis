@echo off
title Jarvis Voice Assistant
color 0A

:: -------------------------------------------------------
:: JARVIS LAUNCHER
:: Place this file in the ROOT of your Jarvis project folder
:: (same folder that contains app\ and .env)
:: -------------------------------------------------------

:: Change to the directory where this .bat file lives
cd /d "%~dp0"

:: Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found at .venv\
    echo Please run setup first:
    echo   python -m venv .venv
    echo   .\.venv\Scripts\Activate.ps1
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

:: Check if .env exists
if not exist ".env" (
    echo [ERROR] .env file not found.
    echo Please copy .env.example to .env and fill in your API keys.
    pause
    exit /b 1
)

:: Activate virtual environment
call .venv\Scripts\activate.bat

echo.
echo  ============================================
echo      JARVIS  ^|  Voice Assistant
echo  ============================================
echo.
echo  Starting reactive voice UI mode...
echo  (Close this window or press Ctrl+C to stop)
echo.

:: Launch Jarvis with floating UI, wake detection, and command response
python main.py

:: If it exits, pause so you can read any error
echo.
echo  Jarvis has stopped. Press any key to close.
pause
