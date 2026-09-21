@echo off
REM Double-click this file on Windows to install Lance On capture.
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo Python was not found.
  echo Install Python 3.12+ from https://www.python.org/downloads/
  echo IMPORTANT: check "Add python.exe to PATH" during setup.
  pause
  exit /b 1
)

python -c "import tkinter" 2>nul
if errorlevel 1 (
  echo Tkinter is missing. Reinstall Python and enable tcl/tk.
  pause
  exit /b 1
)

python "%~dp0setup_app.py"
if errorlevel 1 pause
