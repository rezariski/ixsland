@echo off
setlocal enabledelayedexpansion
title ixsland One-Click Setup
color 0b
cd /d "%~dp0"

echo ==============================================================
echo     ixsland Dynamic Island for Windows - Automatic Setup
echo ==============================================================
echo.

:: 1. Detect Python or Auto-Install to C:\Python312
set "PY_EXE="
if exist "C:\Python312\python.exe" set "PY_EXE=C:\Python312\python.exe"
if exist "C:\Program Files\Python312\python.exe" set "PY_EXE=C:\Program Files\Python312\python.exe"
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if exist "%APPDATA%\Programs\Python\Python312\python.exe" set "PY_EXE=%APPDATA%\Programs\Python\Python312\python.exe"

if "%PY_EXE%"=="" (
    where python >nul 2>&1
    if %ERRORLEVEL% EQU 0 set "PY_EXE=python"
)

if "%PY_EXE%"=="" (
    echo [1/4] Installing Python 3.12 to C:\Python312 ...
    if exist "%~dp0python-3.12.8-amd64.exe" (
        start /wait "" "%~dp0python-3.12.8-amd64.exe" /passive InstallAllUsers=1 PrependPath=1 TargetDir="C:\Python312" Include_pip=1
    )
    if exist "C:\Python312\python.exe" (
        set "PY_EXE=C:\Python312\python.exe"
    ) else if exist "C:\Program Files\Python312\python.exe" (
        set "PY_EXE=C:\Program Files\Python312\python.exe"
    ) else (
        color 0c
        echo [ERROR] Python 3.12 installer did not complete automatically.
        echo Please double click python-3.12.8-amd64.exe manually, check "Add Python to PATH", and click Install.
        pause
        exit /b 1
    )
)

echo [INFO] Detected Python: %PY_EXE%
"%PY_EXE%" --version

:: 2. Deploy files to C:\ixsland
echo.
echo [2/4] Deploying application files to C:\ixsland ...
if not exist "C:\ixsland" mkdir "C:\ixsland"
if not exist "C:\ixsland\assets" mkdir "C:\ixsland\assets"

copy /y "%~dp0ixsland_win.py" "C:\ixsland\" >nul
copy /y "%~dp0run_demo.py" "C:\ixsland\" >nul
copy /y "%~dp0run-demo.bat" "C:\ixsland\" >nul
copy /y "%~dp0start.bat" "C:\ixsland\" >nul
copy /y "%~dp0start-silent.vbs" "C:\ixsland\" >nul
copy /y "%~dp0config.json" "C:\ixsland\" >nul
copy /y "%~dp0assets\*" "C:\ixsland\assets\" >nul

:: 3. Install required Python packages
echo.
echo [3/4] Installing Python modules (PyQt6, pycaw, comtypes, winsdk)...
"%PY_EXE%" -m pip install --upgrade pip
"%PY_EXE%" -m pip install PyQt6 pycaw comtypes winsdk

:: 4. Create Startup Shortcut (No Desktop Shortcut)
echo.
echo [4/4] Creating Startup shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $su = [Environment]::GetFolderPath('Startup'); $s = $ws.CreateShortcut(\"$su\ixsland.lnk\"); $s.TargetPath = 'C:\ixsland\start-silent.vbs'; $s.WorkingDirectory = 'C:\ixsland'; $s.IconLocation = 'C:\ixsland\assets\icon.ico'; $s.Save()"

:: 5. Launch ixsland immediately
echo.
echo [5/5] Launching ixsland Dynamic Island...
start "" "%PY_EXE%" "C:\ixsland\ixsland_win.py"

color 0a
echo.
echo ==============================================================
echo     SUCCESS: ixsland installed and running!
echo ==============================================================
echo  - Look at the top center of your screen.
echo  - To test animations: run C:\ixsland\run-demo.bat
echo.
pause
