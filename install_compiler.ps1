$ErrorActionPreference = "Stop"
Write-Host "[*] Checking C++ Compiler..."

if (Get-Command g++ -ErrorAction SilentlyContinue) {
    Write-Host "[+] g++ is already installed."
    exit 0
}

Write-Host "[!] g++ not found. Installing portable MinGW (w64devkit)..."

$url = "https://github.com/skeeto/w64devkit/releases/download/v1.23.0/w64devkit-1.23.0.zip"
$zipPath = "compiler.zip"
$destDir = "compiler"

if (-not (Test-Path $destDir)) {
    Write-Host "    [-] Downloading from $url..."
    Invoke-WebRequest -Uri $url -OutFile $zipPath
    
    Write-Host "    [-] Extracting..."
    Expand-Archive -Path $zipPath -DestinationPath $destDir -Force
    
    Remove-Item $zipPath
}

$binPath = Join-Path $PWD "$destDir\w64devkit\bin"
Write-Host "[+] Compiler installed at: $binPath"
Write-Host "    [!] PLEASE ADD TO PATH or RUN with env: $binPath"

# Output for Python to read
$env:PATH = "$binPath;$env:PATH"
& g++ --version
