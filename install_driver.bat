
@echo off
cd /d "%~dp0"
echo [*] Installing Interception Driver...
cpp\interception\install-interception.exe /install
echo.
echo [*] Checking Installation...
sc query interception
echo.
pause
