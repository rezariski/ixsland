@echo off
title ixsland Demo Showcase (Windows 10 / 11 64-bit)
cd /d "%~dp0"

echo ========================================================
echo    ixsland Dynamic Island - Demo Showcase Runner
echo    Mendukung Windows 10 & Windows 11 (64-bit)
echo ========================================================
echo.

where python >nul 2>&1
if %errorlevel% equ 0 (
    python run_demo.py
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-demo.ps1"
)

echo.
pause
