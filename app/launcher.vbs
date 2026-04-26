' ============================================================
' Hidden Launcher for Jarvis Voice Assistant
' Runs Launch_Jarvis.bat without showing a terminal window
' 
' You can also double-click this file or create a shortcut to it
' ============================================================

Set objShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptPath = WScript.ScriptFullName
scriptDir = fso.GetParentFolder(scriptPath)

' If in app\ folder, go up to project root
if InStr(scriptDir, "\app") > 0 Then
    batPath = fso.GetParentFolder(scriptDir) & "\Launch_Jarvis.bat"
Else
    batPath = scriptDir & "\Launch_Jarvis.bat"
End If

objShell.Run """" & batPath & """", 0, False
