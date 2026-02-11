@echo off
echo [*] Launching Yolo Aimbot Hybrid Engine...

echo [*] Starting C++ Executor in new window...
start "Aimbot Executor (Muscle)" cpp/executor.exe

echo [*] Starting Python Orchestrator (Brain)...
python python/main.py

echo.
echo [!] Aimbot Stopped.
pause
