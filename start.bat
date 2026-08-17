@echo off
cd /d "%~dp0"
if exist .venv\Scripts\python.exe goto run
echo Run setup.bat first.
pause
exit /b 1

:run
.venv\Scripts\python.exe run.py
if errorlevel 1 pause
