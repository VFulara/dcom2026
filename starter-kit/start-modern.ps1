# Start the modernised Planning Board (CDS v9 at port 4005 + React/Vite at port 5173)
# Opens two new PowerShell windows so you can see live output from both servers.
# The legacy app continues running on port 4004 — both versions can run simultaneously.
# Run .\start-legacy.ps1 first if you want to compare both side by side.
#
# Run from the starter-kit directory:
#   .\start-modern.ps1

$BACKEND_PORT  = 4005
$FRONTEND_PORT = 5173
$SCRIPT_DIR    = Split-Path -Parent $MyInvocation.MyCommand.Path
$MODERN_DIR    = Join-Path $SCRIPT_DIR "modern"
$MODERN_UI_DIR = Join-Path $MODERN_DIR "ui"

Write-Host ""
Write-Host "=== Planning Board (Modernised) ===" -ForegroundColor Cyan
Write-Host ""

# ── Pre-flight checks ────────────────────────────────────────────────────
if (-not (Test-Path $MODERN_DIR)) {
    Write-Host "Error: modern/ directory not found. Complete Phase 2 first." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $MODERN_UI_DIR)) {
    Write-Host "Error: modern/ui/ directory not found. Ensure Phase 2 Agent B has completed." -ForegroundColor Red
    exit 1
}

# ── Kill whatever is on the required ports ───────────────────────────────
foreach ($PORT in @($BACKEND_PORT, $FRONTEND_PORT)) {
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
}
Start-Sleep -Seconds 1

# ── Install modern backend deps if missing ───────────────────────────────
if (-not (Test-Path (Join-Path $MODERN_DIR "node_modules\@sap\cds"))) {
    Write-Host "Installing modern backend dependencies..." -ForegroundColor Yellow
    Push-Location $MODERN_DIR
    npm install --silent
    if ($LASTEXITCODE -ne 0) { npm install --legacy-peer-deps --silent }
    Pop-Location
}

# ── Install modern frontend deps if missing ──────────────────────────────
if (-not (Test-Path (Join-Path $MODERN_UI_DIR "node_modules"))) {
    Write-Host "Installing modern frontend dependencies..." -ForegroundColor Yellow
    Push-Location $MODERN_UI_DIR
    npm install --silent
    if ($LASTEXITCODE -ne 0) { npm install --legacy-peer-deps --silent }
    Pop-Location
}

Write-Host ""
Write-Host "Opening backend terminal  (CDS v9 at http://localhost:$BACKEND_PORT)..." -ForegroundColor Green
Start-Process powershell -ArgumentList `
    "-NoExit", `
    "-ExecutionPolicy", "Bypass", `
    "-Command", "Write-Host '=== CDS v9 Backend ===' -ForegroundColor Cyan; Set-Location '$MODERN_DIR'; npx cds watch"

# Give the backend a moment to bind before Vite proxy tries to connect
Start-Sleep -Seconds 3

Write-Host "Opening frontend terminal (Vite at http://localhost:$FRONTEND_PORT)..." -ForegroundColor Green
Start-Process powershell -ArgumentList `
    "-NoExit", `
    "-ExecutionPolicy", "Bypass", `
    "-Command", "Write-Host '=== React/Vite Frontend ===' -ForegroundColor Cyan; Set-Location '$MODERN_UI_DIR'; npm run dev"

Write-Host ""
Write-Host "Modern app  ->  http://localhost:$FRONTEND_PORT" -ForegroundColor Green
Write-Host "Modern API  ->  http://localhost:$BACKEND_PORT/odata/v4/backlog/"
Write-Host "Legacy app  ->  http://localhost:4004  (run .\start-legacy.ps1 to start it)"
Write-Host ""
Write-Host "Two new PowerShell windows have opened — close them to stop the modern servers."
Write-Host ""
