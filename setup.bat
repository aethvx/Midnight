@echo off
setlocal
cd /d "%~dp0"

py -3.12 -c "import sys; assert sys.version_info[:2] == (3, 12)" >nul 2>&1
if not errorlevel 1 goto use_launcher

if exist "%LocalAppData%\Programs\Python\Python312\python.exe" goto use_local_install

if exist "C:\Program Files\Python312\python.exe" goto use_system_install

python -c "import sys; assert sys.version_info[:2] == (3, 12)" >nul 2>&1
if not errorlevel 1 goto use_path_install
goto no_python

:use_launcher
set "PYTHON_EXE=py"
set "PYTHON_ARGS=-3.12"
goto python_found

:use_local_install
set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
set "PYTHON_ARGS="
goto python_found

:use_system_install
set "PYTHON_EXE=C:\Program Files\Python312\python.exe"
set "PYTHON_ARGS="
goto python_found

:use_path_install
set "PYTHON_EXE=python"
set "PYTHON_ARGS="
goto python_found

:python_found
if exist .venv rmdir /s /q .venv
"%PYTHON_EXE%" %PYTHON_ARGS% -m venv .venv
if errorlevel 1 goto :error
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 goto :error
if not exist .env copy .env.example .env
echo.
echo Installation complete.
echo Fill API_ID and API_HASH in .env, then run discover_ids.bat.
pause
exit /b 0

:no_python
echo.
echo Python 3.12 x64 was not found.
echo Reinstall Python 3.12 and enable the Python Launcher option.
start "" "https://www.python.org/downloads/release/python-31210/"
pause
exit /b 1

:error
echo.
echo Installation failed. Send the complete error text for diagnosis.
pause
exit /b 1
