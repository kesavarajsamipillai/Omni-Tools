@echo off
title OmniTools — Terminal UI
echo Launching OmniTools Terminal UI...
python "%~dp0main.py" --tui
if %ERRORLEVEL% NEQ 0 (
    pause
)

