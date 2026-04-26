@echo off
title Disable Jarvis Startup
color 0C

echo.
echo ============================================
echo   Disable Jarvis Auto Start
echo ============================================
echo.

set "STARTUP_VBS=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\JarvisAutoStart.vbs"

if exist "%STARTUP_VBS%" (
    del "%STARTUP_VBS%"
    if exist "%STARTUP_VBS%" (
        echo [ERROR] Could not remove startup file.
        echo File path: %STARTUP_VBS%
        exit /b 1
    ) else (
        echo [OK] Jarvis startup disabled successfully.
        echo Removed: %STARTUP_VBS%
    )
) else (
    echo [INFO] Startup entry was already not present.
    echo Expected file: %STARTUP_VBS%
)

echo.
pause
