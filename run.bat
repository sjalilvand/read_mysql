@echo off
rem Rah Zendegi Reports - launcher (ASCII only)
cd /d "%~dp0"
title Rah Zendegi Reports - http://127.0.0.1:5000

where python >nul 2>nul
if errorlevel 1 (
  echo [!] Python not found. Install it with:
  echo     winget install -e --id Python.Python.3.12
  pause
  exit /b 1
)

python -c "import flask" >nul 2>nul
if errorlevel 1 (
  echo [...] installing flask and openpyxl ...
  python -m pip install --disable-pip-version-check -q flask openpyxl
)

start "" "http://127.0.0.1:5000"
python "%~dp0app.py"
pause
