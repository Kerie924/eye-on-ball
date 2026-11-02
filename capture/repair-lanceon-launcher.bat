@echo off
REM Fix a flash-closing C:\LanceOn\LanceOn.bat without a full reinstall.
REM Also refreshes control_app.py from this USB/capture folder.
setlocal EnableExtensions
title Lance On — reparar launcher

set "ROOT=C:\LanceOn"
if defined LANCEON_HOME set "ROOT=%LANCEON_HOME%"
set "CAPTURE=%ROOT%\capture"
set "TARGET=%ROOT%\LanceOn.bat"

echo Root:    %ROOT%
echo Capture: %CAPTURE%
echo Target:  %TARGET%
echo.

if not exist "%CAPTURE%\control_app.py" (
  echo Pasta instalada nao encontrada. Rode LanceOn-Setup.bat primeiro.
  pause
  exit /b 1
)

if not exist "%CAPTURE%\.venv\Scripts\python.exe" (
  if not exist "%CAPTURE%\.venv\Scripts\pythonw.exe" (
    echo Ambiente Python .venv ausente em:
    echo   %CAPTURE%\.venv
    echo Rode LanceOn-Setup.bat novamente.
    pause
    exit /b 1
  )
)

if not exist "%ROOT%\logs" mkdir "%ROOT%\logs"

copy /Y "%~dp0LanceOn.bat" "%TARGET%" >nul
if errorlevel 1 (
  echo Nao foi possivel escrever %TARGET%
  echo Tente Executar como administrador.
  pause
  exit /b 1
)

copy /Y "%~dp0control_app.py" "%CAPTURE%\control_app.py" >nul
if exist "%~dp0agent" xcopy /E /I /Y "%~dp0agent" "%CAPTURE%\agent\" >nul
if exist "%~dp0windows_pins.py" copy /Y "%~dp0windows_pins.py" "%CAPTURE%\windows_pins.py" >nul
if exist "%~dp0install_windows.py" copy /Y "%~dp0install_windows.py" "%CAPTURE%\install_windows.py" >nul

REM stop-capture.bat: replace removed wmic with PowerShell
(
echo @echo off
echo setlocal EnableExtensions
echo echo Stopping Lance On capture...
echo taskkill /F /FI "WINDOWTITLE eq LanceOnCapture*" 2^>nul
echo powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process -ErrorAction SilentlyContinue ^| Where-Object { $_.CommandLine -and $_.CommandLine -like '*LanceOn*run.py*' } ^| ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" 2^>nul
echo schtasks /End /TN LanceOnCapture 2^>nul
echo echo Done.
) > "%ROOT%\stop-capture.bat"

echo Launcher atualizado: %TARGET%
echo control_app.py atualizado ^(sem wmic^)
echo.
echo Abrindo Lance On...
call "%TARGET%"
exit /b %ERRORLEVEL%
