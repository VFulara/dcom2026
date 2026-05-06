# Start the legacy Planning Board (CDS v6 + OpenUI5)
# Kills any process on port 4004 first, then starts cds watch.
#
# Run from the starter-kit directory:
#   .\start-legacy.ps1
#
# Requires: Node.js 18+, @sap/cds-dk (installed by npm install)

$PORT = 4004

Write-Host ""
Write-Host "=== Planning Board (Legacy) ===" -ForegroundColor Cyan
Write-Host ""

# ── Kill whatever is on the port ──────────────────────────────────────────
# Try Get-NetTCPConnection first (Windows 8+/Server 2012+, no elevation needed
# for listening ports owned by the current user).
# Fall back to netstat + taskkill for restricted enterprise environments.
$killed = $false

try {
    $conns = Get-NetTCPConnection -LocalPort $PORT -State Listen -ErrorAction Stop
    if ($conns) {
        Write-Host "Stopping process on port $PORT..." -ForegroundColor Yellow
        foreach ($c in $conns) {
            Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
        }
        $killed = $true
    }
} catch {
    # Get-NetTCPConnection unavailable or access denied — fall back to netstat
    $netstatLines = netstat -ano 2>$null | Select-String ":$PORT\s.*LISTENING"
    if ($netstatLines) {
        Write-Host "Stopping process on port $PORT (via netstat)..." -ForegroundColor Yellow
        foreach ($line in $netstatLines) {
            $parts = ($line.Line -split '\s+') | Where-Object { $_ -ne '' }
            $pid   = $parts[-1]
            if ($pid -match '^\d+$' -and $pid -ne '0') {
                taskkill /PID $pid /F 2>$null | Out-Null
            }
        }
        $killed = $true
    }
}

if ($killed) { Start-Sleep -Seconds 1 }

# ── Install dependencies if missing ──────────────────────────────────────
if (-not (Test-Path "node_modules\@sap\cds")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install --silent
    if ($LASTEXITCODE -ne 0) {
        Write-Host "npm install failed. Try: npm install --legacy-peer-deps" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Starting at http://localhost:$PORT" -ForegroundColor Green
Write-Host "Open that URL in your browser — the Planning Board loads directly."
Write-Host "(Press Ctrl+C to stop)"
Write-Host ""

npx cds watch
