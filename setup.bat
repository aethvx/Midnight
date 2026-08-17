@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo Python 3.12 was not found.
    echo Install the 64-bit Python 3.12 with the Python Launcher enabled.
    echo Then run setup.bat again.
    start "" "https://www.python.org/downloads/release/python-31210/"
    pause
    exit /b 1
)
if exist .venv rmdir /s /q .venv
py -3.12 -m venv .venv
if errorlevel 1 goto :error
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 goto :error
if not exist .env copy .env.example .env
echo.
echo Установка завершена. Заполни API_ID и API_HASH в .env, затем запусти discover_ids.bat.
pause
exit /b 0

:error
echo.
echo Installation failed. Send the complete error text for diagnosis.
pause
exit /b 1
