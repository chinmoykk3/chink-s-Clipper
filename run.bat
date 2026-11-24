@echo off
title AI Clipper Studio
cd /d "%~dp0"
echo Starting AI Clipper Studio...
".venv\Scripts\streamlit.exe" run app.py
pause
