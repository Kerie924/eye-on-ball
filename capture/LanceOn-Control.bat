@echo off
REM Open Lance On control panel (edit IPs / watermark, start/stop).
setlocal EnableExtensions
cd /d "%~dp0"

if exist "C:\LanceOn\LanceOn.bat" (
  call "C:\LanceOn\LanceOn.bat"
  exit /b %ERRORLEVEL%
)

if defined LANCEON_HOME if exist "%LANCEON_HOME%\LanceOn.bat" (
  call "%LANCEON_HOME%\LanceOn.bat"
  exit /b %ERRORLEVEL%
)

REM Fallback: run from this capture folder (USB / before install finishes)
call "%~dp0LanceOn.bat"
exit /b %ERRORLEVEL%
