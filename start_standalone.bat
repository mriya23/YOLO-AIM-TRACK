
@echo off
title STANDALONE ENGINE LAUNCHER
cd /d "%~dp0"

echo [*] Cleaning old processes...
taskkill /F /IM executor.exe /T 2>nul

echo [*] Launching Python Backend...
start "Python Backend" python python/main.py

echo [*] Waiting 5s for Shared Memory...
timeout /t 5 /nobreak >nul

echo [*] Launching C++ Executor...
cd cpp
start "C++ Executor" executor.exe

echo.
echo [!] Check the two windows for errors!
pause
