@echo off
setlocal

title Gekko Voice List
color 0A

echo.
echo  Installed Windows speech voices
echo  -------------------------------
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
    "Add-Type -AssemblyName System.Speech; $speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speaker.GetInstalledVoices() | ForEach-Object { Write-Host ('- ' + $_.VoiceInfo.Name) }"

echo.
echo Put the voice you like in .env, for example:
echo TTS_VOICE_NAME=Microsoft Zira Desktop
echo.
pause
