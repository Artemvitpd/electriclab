$ErrorActionPreference = 'Stop'

Write-Host "[1/6] Creating Python venv..." -ForegroundColor Cyan
if (-not (Test-Path .venv)) {
  python -m venv .venv
}

Write-Host "[2/6] Activating venv and installing requirements..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
try {
  & .\.venv\Scripts\pip.exe install -r requirements.txt
} catch {
  Write-Warning "Package install encountered errors: $_"
}
# Ensure FastAPI present for perf_test imports
& .\.venv\Scripts\pip.exe install fastapi uvicorn cryptography

Write-Host "[3/6] Preparing test data directories..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path .\data\gov\cache | Out-Null
New-Item -ItemType Directory -Force -Path .\data\gov\source | Out-Null
New-Item -ItemType Directory -Force -Path .\data\commercial\cache | Out-Null
New-Item -ItemType Directory -Force -Path .\data\commercial\source | Out-Null

Write-Host "[4/6] Generating AES key for commercial service..." -ForegroundColor Cyan
$rng = New-Object System.Security.Cryptography.RNGCryptoServiceProvider
$bytes = New-Object byte[] 32
$rng.GetBytes($bytes)
$aesB64 = [Convert]::ToBase64String($bytes)
Write-Host "AES key (Base64): $aesB64" -ForegroundColor Yellow

Write-Host "[5/6] Running performance tests (gov)..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe perf_test.py --service gov --iterations 30 --size_mb 8

Write-Host "[6/6] Running performance tests (commercial)..." -ForegroundColor Cyan
$env:HYBRIDCACHE_AES_KEY = $aesB64
& .\.venv\Scripts\python.exe perf_test.py --service commercial --iterations 30 --size_mb 8

Write-Host "All tests completed." -ForegroundColor Green


