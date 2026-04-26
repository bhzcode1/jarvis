@echo off
setlocal

title Jarvis Offline Wake Setup
color 0A

set "ROOT=%~dp0"
set "MODEL_NAME=vosk-model-small-en-us-0.15"
set "MODEL_DIR=%ROOT%data\models"
set "MODEL_PATH=%MODEL_DIR%\%MODEL_NAME%"
set "MODEL_ZIP=%MODEL_DIR%\%MODEL_NAME%.zip"
set "MODEL_URL=https://alphacephei.com/vosk/models/%MODEL_NAME%.zip"

cd /d "%ROOT%"

echo.
echo  ============================================
echo      JARVIS  ^|  Offline Wake Setup
echo  ============================================
echo.

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=%ROOT%.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [1/3] Installing Vosk Python package...
"%PYTHON_EXE%" -m pip install vosk
if errorlevel 1 (
    echo.
    echo [ERROR] Could not install vosk.
    echo Make sure Python and pip work, then run this script again.
    pause
    exit /b 1
)

if exist "%MODEL_PATH%" (
    echo [2/3] Vosk model already exists:
    echo       %MODEL_PATH%
) else (
    echo [2/3] Downloading Vosk small English model...
    if not exist "%MODEL_DIR%" mkdir "%MODEL_DIR%"

    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
        "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri '%MODEL_URL%' -OutFile '%MODEL_ZIP%'"
    if errorlevel 1 (
        echo.
        echo [ERROR] Could not download model.
        echo Download manually from:
        echo %MODEL_URL%
        echo Then extract it into:
        echo %MODEL_DIR%
        pause
        exit /b 1
    )

    echo [3/3] Extracting model...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
        "Expand-Archive -LiteralPath '%MODEL_ZIP%' -DestinationPath '%MODEL_DIR%' -Force"
    if errorlevel 1 (
        echo.
        echo [ERROR] Could not extract model zip.
        pause
        exit /b 1
    )
)

echo.
echo Done. Offline wake detection is ready.
echo Model path:
echo %MODEL_PATH%
echo.
echo Now run:
echo python -u main.py
echo.
pause
