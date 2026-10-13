@echo off
title OmniTools Offline Desktop App
echo Starting OmniTools Desktop Application...
python "%~dp0main.py" --gui
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred while launching OmniTools.
    pause
)
