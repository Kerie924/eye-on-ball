@echo off
REM Works as:
REM   C:\LanceOn\LanceOn.bat          (after install)
REM   <usb>\capture\LanceOn.bat       (from the capture folder)
setlocal EnableExtensions
title Lance On
cd /d "%~dp0"

set "HERE=%~dp0"
if "%HERE:~-1%"=="\" set "HERE=%HERE:~0,-1%"

set "CAPTURE="
if exist "%HERE%\capture\control_app.py" (
  set "ROOT=%HERE%"
  set "CAPTURE=%HERE%\capture"
) else if exist "%HERE%\control_app.py" (
  for %%I in ("%HERE%\..") do set "ROOT=%%~fI"
  set "CAPTURE=%HERE%"
)

if not defined CAPTURE (
  echo [Lance On] Pasta capture nao encontrada a partir de:
  echo   %HERE%
  echo Rode LanceOn-Setup.bat, ou copie este arquivo para C:\LanceOn\
  pause
  exit /b 1
)

set "PYW=%CAPTURE%\.venv\Scripts\pythonw.exe"
set "PY=%CAPTURE%\.venv\Scripts\python.exe"
set "APP=%CAPTURE%\control_app.py"
set "ERRLOG=%ROOT%\logs\control-app-error.log"

if not exist "%ROOT%\logs" mkdir "%ROOT%\logs"

if exist "%PY%" (
  set "PYCONSOLE=%PY%"
) else (
  echo [Lance On] Python do ambiente nao encontrado:
  echo   %CAPTURE%\.venv\Scripts\python.exe
  echo Rode LanceOn-Setup.bat novamente.
  pause
  exit /b 1
)

if exist "%PYW%" (
  set "LAUNCHER=%PYW%"
) else (
  set "LAUNCHER=%PYCONSOLE%"
)

if not exist "%APP%" (
  echo [Lance On] control_app.py nao encontrado:
  echo   %APP%
  pause
  exit /b 1
)

REM Fail fast with a visible message if imports/tkinter are broken.
cd /d "%CAPTURE%"
"%PYCONSOLE%" -c "import tkinter; import control_app" 1>"%ERRLOG%" 2>&1
if errorlevel 1 (
  echo.
  echo [Lance On] Nao foi possivel iniciar o painel.
  echo Detalhes em: %ERRLOG%
  echo.
  if exist "%ERRLOG%" type "%ERRLOG%"
  echo.
  pause
  exit /b 1
)

REM Detach GUI so closing this console does not kill the app.
start "Lance On" "%LAUNCHER%" "%APP%"
exit /b 0
