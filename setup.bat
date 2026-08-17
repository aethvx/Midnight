@echo off
cd /d "%~dp0"
py -3 -m venv .venv
if errorlevel 1 goto :error
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 goto :error
if not exist .env copy .env.example .env
echo.
echo Installation complete. Fill in the .env file, then run start.bat.
pause
exit /b 0

:error
echo.
echo Installation failed. Make sure Python 3.11 or newer is installed.
pause
exit /b 1

