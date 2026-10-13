@echo off
title OmniTools Studio Pro — Windows Setup & Shortcut Installer
echo ==============================================================
echo       ⚡ OmniTools Studio Pro — Windows Setup Installer ⚡
echo ==============================================================
echo.
echo Installing OmniTools Desktop and Terminal shortcuts to your PC...

powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop') + '\OmniTools Studio Pro.lnk'); $s.TargetPath='%~dp0run_gui.bat'; $s.WorkingDirectory='%~dp0'; $s.IconLocation='%SystemRoot%\System32\shell32.dll,14'; $s.Description='OmniTools Studio Pro Desktop App'; $s.Save()"

powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop') + '\OmniTools Moviebox-TUI.lnk'); $s.TargetPath='%~dp0run_cli.bat'; $s.WorkingDirectory='%~dp0'; $s.IconLocation='%SystemRoot%\System32\cmd.exe,0'; $s.Description='OmniTools Moviebox-TUI Terminal App'; $s.Save()"

echo.
echo [SUCCESS] Created shortcuts on your Desktop:
echo   1. 'OmniTools Studio Pro' (Desktop Graphical App)
echo   2. 'OmniTools Moviebox-TUI' (Terminal TUI App)
echo.
echo Setup is complete! Press any key to launch OmniTools Studio Pro...
pause >nul
start "" "%~dp0run_gui.bat"
