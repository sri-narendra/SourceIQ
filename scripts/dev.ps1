$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
& "$root\backend\.venv\Scripts\python.exe" -m uvicorn backend.main:app --app-dir backend --host 0.0.0.0 --port 8000