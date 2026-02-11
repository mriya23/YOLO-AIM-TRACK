@echo off
set "VS_PATH=C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"

if not exist "%VS_PATH%" (
    echo [ERROR] Visual Studio 2022 not found at expected path!
    pause
    exit /b
)

echo [INFO] Setting up VS Environment...
call "%VS_PATH%"

echo [INFO] Building Lunar Aimbot DLL...
cd cpp\aimbot
if not exist build mkdir build
cd build

cmake .. -A x64
cmake --build . --config Release

echo.
if exist Release\lunar_aimbot.dll (
    echo [SUCCESS] Built: cpp/aimbot/build/Release/lunar_aimbot.dll
) else (
    echo [ERROR] Build failed! Check errors above.
)
pause
