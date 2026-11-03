@echo off
title Launch ixsland
cd /d "%~dp0"
set "PYW_EXE="
if exist "C:\Python312\pythonw.exe" set "PYW_EXE=C:\Python312\pythonw.exe"
if exist "C:\Program Files\Python312\pythonw.exe" set "PYW_EXE=C:\Program Files\Python312\pythonw.exe"
if exist "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" set "PYW_EXE=%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"
if "%PYW_EXE%"=="" where pythonw >nul 2>&1 && set "PYW_EXE=pythonw"
if "%PYW_EXE%"=="" set "PYW_EXE=python"

start "" "%PYW_EXE%" ixsland_win.py
exit
