@echo off
title ixsland Windows Uninstaller
color 0e

echo ==============================================================
echo    Uninstalling ixsland Dynamic Island from Windows...
echo ==============================================================
echo.

:: 1. Stop running instance
echo [1/3] Stopping running ixsland processes...
taskkill /f /im pythonw.exe /fi "WINDOWTITLE eq ixsland*" >nul 2>&1
taskkill /f /im ixsland.exe >nul 2>&1

:: 2. Remove shortcuts
echo [2/3] Removing shortcuts...
del /f /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ixsland.lnk" >nul 2>&1
del /f /q "%USERPROFILE%\Desktop\ixsland Dynamic Island.lnk" >nul 2>&1

:: 3. Remove application files
echo [3/3] Removing application files from %LOCALAPPDATA%\ixsland ...
if exist "%LOCALAPPDATA%\ixsland" (
    rmdir /s /q "%LOCALAPPDATA%\ixsland"
)

color 0a
echo.
echo ==============================================================
echo    ixsland has been completely uninstalled from Windows.
echo ==============================================================
echo.
pause
