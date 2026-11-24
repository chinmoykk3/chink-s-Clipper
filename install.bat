@echo off
title Installing Chink's Clipper Dependencies
cd /d "%~dp0"
echo ====================================================
echo  Setting up Chink's Clipper Environment...
echo ====================================================

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Installing required Python packages...
".venv\Scripts\pip.exe" install -r requirements.txt

echo.
echo ====================================================
echo  All dependencies installed successfully!
echo  You can now launch the app using run.bat
echo ====================================================
pause
