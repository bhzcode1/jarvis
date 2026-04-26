# ============================================================
# create_shortcut.ps1
# Run this ONCE to place a Jarvis shortcut on your Desktop.
# Right-click the file > "Run with PowerShell"
# ============================================================

# Fix execution policy if needed
if ((Get-ExecutionPolicy) -eq "Restricted") {
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force -ErrorAction SilentlyContinue
}

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcherVbs = Join-Path $projectRoot "launcher.vbs"
$desktop     = [Environment]::GetFolderPath("Desktop")
$shortcut    = Join-Path $desktop "Jarvis.lnk"

# Make sure the launcher exists
if (-not (Test-Path $launcherVbs)) {
    Write-Host "[ERROR] launcher.vbs not found in project root." -ForegroundColor Red
    Write-Host "Please ensure launcher.vbs exists at: $launcherVbs" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Create the shortcut (using hidden launcher for no terminal window)
$wsh  = New-Object -ComObject WScript.Shell
$lnk  = $wsh.CreateShortcut($shortcut)
$lnk.TargetPath       = $launcherVbs
$lnk.WorkingDirectory = $projectRoot
$lnk.WindowStyle      = 7          # 7 = Hidden window
$lnk.Description      = "Launch Jarvis Voice Assistant"

# Use a built-in Windows robot/terminal icon (no external file needed)
$lnk.IconLocation = "shell32.dll,21"

$lnk.Save()

Write-Host ""
Write-Host "  Shortcut created on your Desktop: Jarvis.lnk" -ForegroundColor Green
Write-Host "  Double-click it any time to launch Jarvis."    -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to close"
