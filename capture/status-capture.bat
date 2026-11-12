@echo off
REM Live status window for C:\LanceOn\status-capture.bat
REM Closing this window does NOT stop the capture service.
setlocal EnableExtensions
title LanceOn Status

set "HERE=%~dp0"
if "%HERE:~-1%"=="\" set "HERE=%HERE:~0,-1%"

if exist "%HERE%\logs" (
  set "ROOT=%HERE%"
) else if exist "%HERE%\..\logs" (
  for %%I in ("%HERE%\..") do set "ROOT=%%~fI"
) else if exist "C:\LanceOn\logs" (
  set "ROOT=C:\LanceOn"
) else (
  echo [Lance On] logs folder not found.
  timeout /t 20
  exit /b 1
)

set "LOG=%ROOT%\logs\capture.log"
if not exist "%ROOT%\logs" mkdir "%ROOT%\logs"
if not exist "%LOG%" type nul > "%LOG%"

echo Lance On — status ao vivo (fechar esta janela NAO para o gravador)
echo Log: %LOG%
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Content -LiteralPath '%LOG%' -Tail 80 -Wait"
echo.
pause
