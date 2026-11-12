@echo off
REM Launcher for C:\LanceOn\start-capture.bat
REM Runs capture in the foreground (required for Task Scheduler / reliable start).
REM Uses pythonw.exe when available = no console window, but process stays alive.
setlocal EnableExtensions
title LanceOnCapture

set "HERE=%~dp0"
if "%HERE:~-1%"=="\" set "HERE=%HERE:~0,-1%"

if exist "%HERE%\capture\run.py" (
  set "ROOT=%HERE%"
  set "CAPTURE=%HERE%\capture"
) else if exist "%HERE%\run.py" (
  for %%I in ("%HERE%\..") do set "ROOT=%%~fI"
  set "CAPTURE=%HERE%"
) else if exist "C:\LanceOn\capture\run.py" (
  set "ROOT=C:\LanceOn"
  set "CAPTURE=C:\LanceOn\capture"
) else (
  echo [Lance On] capture\run.py not found.
  timeout /t 20
  exit /b 1
)

set "PY=%CAPTURE%\.venv\Scripts\python.exe"
set "PYW=%CAPTURE%\.venv\Scripts\pythonw.exe"
set "CFG=%ROOT%\config.yaml"
set "LOGDIR=%ROOT%\logs"

if not exist "%PY%" (
  echo [Lance On] Missing venv python:
  echo   %PY%
  timeout /t 20
  exit /b 1
)

if exist "%PYW%" (set "LAUNCHER=%PYW%") else (set "LAUNCHER=%PY%")

if not exist "%LOGDIR%" mkdir "%LOGDIR%"
cd /d "%CAPTURE%"

REM IMPORTANT: do NOT use "start /B" here — that made the bat exit immediately
REM and Task Scheduler / job cleanup stopped the capture process.
"%LAUNCHER%" "%CAPTURE%\run.py" --config "%CFG%"
set ERR=%ERRORLEVEL%
if not %ERR%==0 (
  echo.
  echo [Lance On] Capture exited with error %ERR%
  echo See: %LOGDIR%\capture.log
  echo See: %LOGDIR%\capture-crash.log
  echo.
  timeout /t 30
)
exit /b %ERR%
