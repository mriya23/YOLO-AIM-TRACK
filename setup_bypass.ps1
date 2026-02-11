# Check for Administrator privileges
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Requesting Administrator privileges..." -ForegroundColor Yellow
    Start-Process powershell.exe "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

$currentDir = $PSScriptRoot
Write-Host "[-] Adding Exclusion for: $currentDir" -ForegroundColor Cyan

try {
    # 1. Add Defender Exclusion for Project Folder
    Add-MpPreference -ExclusionPath $currentDir -ErrorAction Stop
    Write-Host "[+] Defender Exclusion Added!" -ForegroundColor Green
} catch {
    Write-Host "[!] Failed to add exclusion: $_" -ForegroundColor Red
}

try {
    # 2. Unblock Executor (Remove 'Mark of the Web')
    $exePath = Join-Path $currentDir "cpp\executor.exe"
    if (Test-Path $exePath) {
        Unblock-File -Path $exePath -ErrorAction Stop
        Write-Host "[+] executor.exe Unblocked!" -ForegroundColor Green
    } else {
        Write-Host "[!] executor.exe not found at $exePath" -ForegroundColor Red
    }
} catch {
    Write-Host "[!] Failed to unblock file: $_" -ForegroundColor Red
}

Write-Host "`n[+] SETUP COMPLETE. You can now run 'python gui.py' freely." -ForegroundColor Green
Read-Host "Press Enter to exit..."
