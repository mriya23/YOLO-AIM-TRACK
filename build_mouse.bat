@echo off
set "VS_PATH=C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"

if not exist "%VS_PATH%" (
    echo [ERROR] Visual Studio 2022 not found at expected path!
    pause
    exit /b
)

echo [INFO] Setting up VS Environment...
call "%VS_PATH%"

echo [INFO] Building Lunar Mouse DLL...
cd cpp\mouse
if not exist build mkdir build
cd build

cmake ..
cmake --build . --config Release

echo [INFO] Build Complete! Check cpp/mouse/build/Release/lunar_mouse.dll
pause
