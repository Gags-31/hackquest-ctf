# QuantBuild one-click setup + launch (Windows PowerShell)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "==> Installing backend dependencies" -ForegroundColor Cyan
pip install -r "$root\backend\requirements.txt"

if (-not (Test-Path "$root\frontend\dist")) {
    Write-Host "==> Building frontend (first run only)" -ForegroundColor Cyan
    Push-Location "$root\frontend"
    npm install --no-audit --no-fund
    node node_modules\esbuild\install.js 2>$null
    npm run build
    Pop-Location
}

Write-Host "==> Starting QuantBuild at http://localhost:8000" -ForegroundColor Green
python "$root\run.py"
