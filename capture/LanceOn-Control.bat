@echo off
REM Open Lance On control panel (edit IPs / watermark, start/stop).
cd /d "%~dp0"

if exist "C:\LanceOn\LanceOn.bat" (
  call "C:\LanceOn\LanceOn.bat"
  exit /b %ERRORLEVEL%
)

where python >nul 2>&1
if errorlevel 1 (
  echo Python not found. Install Python 3.11+ from python.org
  pause
  exit /b 1
)

python "%~dp0control_app.py"
if errorlevel 1 pause
