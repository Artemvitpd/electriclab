$ErrorActionPreference = 'Stop'

# Disable encryption for this run
$env:HYBRIDCACHE_ENCRYPTION = '0'
Write-Host ("HYBRIDCACHE_ENCRYPTION=" + $env:HYBRIDCACHE_ENCRYPTION)

# Run improved benchmark
& .\.venv\Scripts\python.exe bench_improved.py


