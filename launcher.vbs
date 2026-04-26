' ============================================================
' Hidden Launcher for Jarvis Voice Assistant
' Runs Launch_Jarvis.bat without showing a terminal window
' 
' Double-click this to launch Jarvis silently
' ============================================================

Set objShell = CreateObject("WScript.Shell")
currentDir = CreateObject("WScript.Shell").CurrentDirectory
batPath = currentDir & "\Launch_Jarvis.bat"

' Run the batch file hidden (0 = hidden window)
objShell.Run """" & batPath & """", 0, False
