@echo off
REM Start the modernised Planning Board (CDS v9 at port 4005 + React/Vite at port 5173)
REM Opens two new CMD windows so you can watch live output from both servers.
REM Run from the starter-kit directory:  start-modern.bat
REM
REM Requirements: Node.js v18+ on PATH.  No elevated (admin) access needed.

setlocal

set BACKEND_PORT=4005
set FRONTEND_PORT=5173
set SCRIPT_DIR=%~dp0
set MODERN_DIR=%SCRIPT_DIR%modern
set MODERN_UI_DIR=%MODERN_DIR%\ui

echo.
echo === Planning Board (Modernised) ===
echo.

REM ── Pre-flight checks ────────────────────────────────────────────────────
if not exist "%MODERN_DIR%\" (
    echo.
    echo  ERROR: modern\ directory not found.
    echo.
    echo  The modern\ directory is created by the Phase 2 migration agents
    echo  and only exists after the Step 12 merges. Run from starter-kit:
    echo.
    echo    git merge feature/modernisation-backend
    echo    git merge feature/modernisation-frontend
    echo.
    echo  Then retry.
    echo.
    pause
    exit /b 1
)

if not exist "%MODERN_UI_DIR%\" (
    echo.
    echo  ERROR: modern\ui\ directory not found.
    echo.
    echo  Phase 2 Agent B (frontend) did not complete or was not merged.
    echo  Run from starter-kit:
    echo.
    echo    git merge feature/modernisation-frontend
    echo.
    echo  Then retry.
    echo.
    pause
    exit /b 1
)

REM ── Free required ports (best-effort, no elevation needed for user processes) ──
for %%P in (%BACKEND_PORT% %FRONTEND_PORT%) do (
    for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":%%P .*LISTENING"') do (
        if not "%%p"=="0" (
            echo Stopping process on port %%P ^(PID %%p^)...
            taskkill /PID %%p /F >nul 2>&1
        )
    )
)

REM ── Install modern backend deps if missing ───────────────────────────────
if not exist "%MODERN_DIR%\node_modules\@sap\cds" (
    echo Installing modern backend dependencies...
    pushd "%MODERN_DIR%"
    call npm install --silent 2>nul
    if errorlevel 1 call npm install --legacy-peer-deps --silent
    popd
)

REM ── Install modern frontend deps if missing ──────────────────────────────
if not exist "%MODERN_UI_DIR%\node_modules" (
    echo Installing modern frontend dependencies...
    pushd "%MODERN_UI_DIR%"
    call npm install --silent 2>nul
    if errorlevel 1 call npm install --legacy-peer-deps --silent
    popd
)

echo.
echo Opening backend window  ^(CDS v9 at http://localhost:%BACKEND_PORT%^)...
start "CDS v9 Backend" cmd /k "title CDS v9 Backend && cd /d "%MODERN_DIR%" && npx cds watch"

REM Give backend a moment to bind before Vite proxy tries to connect
timeout /t 3 /nobreak >nul

echo Opening frontend window ^(Vite at http://localhost:%FRONTEND_PORT%^)...
start "React/Vite Frontend" cmd /k "title React/Vite Frontend && cd /d "%MODERN_UI_DIR%" && npm run dev"

echo.
echo   Modern app  --^>  http://localhost:%FRONTEND_PORT%
echo   Modern API  --^>  http://localhost:%BACKEND_PORT%/odata/v4/backlog/
echo   Legacy app  --^>  http://localhost:4004  ^(run start-legacy.bat to start it^)
echo.
echo Two new CMD windows have opened -- close them to stop the modern servers.
echo.

endlocal
