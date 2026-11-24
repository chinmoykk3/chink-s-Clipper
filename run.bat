@echo off
title Chink's Clipper
cd /d "%~dp0"
echo Starting Chink's Clipper...
".venv\Scripts\streamlit.exe" run app.py
pause
