@echo off
set "VCVARS=C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"

if not exist "%VCVARS%" (
    echo [!] vcvars64.bat not found at %VCVARS%
    echo Make sure Visual Studio 2022 Community is installed.
    pause
    exit /b 1
)

echo [+] Initializing MSVC Environment...
call "%VCVARS%"

echo [+] Compiling C++ Executor...
cl /O2 /EHsc /MT cpp/executor.cpp /Fe:cpp/executor.exe user32.lib winmm.lib

if %errorlevel% equ 0 (
    echo [+] Build Successful: cpp/executor.exe
) else (
    echo [!] Build Failed! Check the error messages above.
)
pause
