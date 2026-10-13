# HackQuest Arena Launcher
# Starts the Flask challenge server + a Cloudflare Tunnel, and prints the public URL.
# Double-click this file, or run:  powershell -ExecutionPolicy Bypass -File start-arena.ps1

$ErrorActionPreference = "SilentlyContinue"
$root = "C:\Users\Gagan\Documents\Default Project"
$challengeDir = Join-Path $root "challenges"
$flaskExe = "C:\Users\Gagan\AppData\Local\Programs\Python\Python312\python.exe"
$cloudflared = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
$logDir = Join-Path $root "logs"
$arenaLog = Join-Path $logDir "arena-url.txt"

New-Item -ItemType Directory -Force $logDir | Out-Null

Write-Host ""
Write-Host "  HackQuest Arena Launcher" -ForegroundColor Green
Write-Host "  -------------------------" -ForegroundColor Green
Write-Host ""

# Stop any previous instances
Get-Process python    -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# 1. Start the Flask challenge server
Write-Host "  [1/2] Starting challenge server on port 5000..." -ForegroundColor Cyan
Start-Process -FilePath $flaskExe -ArgumentList "rounds.py" `
  -WorkingDirectory $challengeDir `
  -WindowStyle Hidden `
  -RedirectStandardOutput (Join-Path $logDir "server.out.log") `
  -RedirectStandardError  (Join-Path $logDir "server.err.log")
Start-Sleep -Seconds 5

# 2. Start the public tunnel
Write-Host "  [2/2] Opening Cloudflare Tunnel..." -ForegroundColor Cyan
Start-Process -FilePath $cloudflared `
  -ArgumentList "tunnel --url http://localhost:5000 --no-autoupdate" `
  -WindowStyle Hidden `
  -RedirectStandardOutput (Join-Path $logDir "tunnel.log") `
  -RedirectStandardError  (Join-Path $logDir "tunnel.err.log")

# 3. Wait for and print the public URL
Write-Host ""
Write-Host "  Waiting for tunnel URL..." -ForegroundColor DarkGray
$url = $null
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 2
    # cloudflared writes its banner to stderr, so check both log files
    $line = (Get-Content (Join-Path $logDir "tunnel.log") -ErrorAction SilentlyContinue) +
            (Get-Content (Join-Path $logDir "tunnel.err.log") -ErrorAction SilentlyContinue) |
            Select-String -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" |
            Select-Object -Last 1
    if ($line) {
        $m = [regex]::Match($line.ToString(), "https://[a-z0-9-]+\.trycloudflare\.com")
        if ($m.Success) { $url = $m.Value; break }
    }
}

if ($url) {
    $url | Out-File -FilePath $arenaLog -Encoding utf8
    Write-Host ""
    Write-Host "  ============================================================" -ForegroundColor Green
    Write-Host "   ARENA IS LIVE" -ForegroundColor Green
    Write-Host "   $url" -ForegroundColor White
    Write-Host "  ============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "   Leaderboard : $url/leaderboard" -ForegroundColor DarkGray
    Write-Host "   Admin panel : $url/admin?token=hackquest-admin-2026" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "   URL saved to: logs\arena-url.txt" -ForegroundColor DarkGray
    Write-Host "   Keep this window's processes running. Press Ctrl+C to stop." -ForegroundColor DarkGray
}
else {
    Write-Host ""
    Write-Host "  Tunnel did not report a URL. Check logs\tunnel.err.log" -ForegroundColor Red
}

Write-Host ""
Write-Host "  Local access also works at http://localhost:5000" -ForegroundColor DarkGray
Write-Host ""
Start-Sleep -Seconds 3