@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
	echo Python was not found.
	echo Install Python 3.12 from https://www.python.org/downloads/windows/
	echo During setup, enable "Add python.exe to PATH", then run this file again.
	pause
	exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
	echo Creating the FlooCast test environment...
	py -3 -m venv .venv
	if errorlevel 1 goto :failed
)

echo Installing or updating FlooCast dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :failed

echo Starting FlooCast test version...
".venv\Scripts\python.exe" main.py
if errorlevel 1 goto :failed
echo.
echo FlooCast closed. Any audio-switching diagnostics are shown above.
pause
exit /b 0

:failed
echo.
echo Setup or startup failed. Keep this window open and copy its error text.
pause
exit /b 1
