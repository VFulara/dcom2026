# Auto-refreshing progress report viewer for Windows.
# Windows equivalent of progress-show.sh.
# Press Q to close.

# Resolve PROJECT_ROOT robustly whether run via -File, dot-sourced, or direct path.
if ($MyInvocation.MyCommand.Path) {
    $SCRIPT_DIR   = Split-Path -Parent $MyInvocation.MyCommand.Path
    $PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $SCRIPT_DIR)
} else {
    # Fallback: assume CWD is the project root (e.g. run from starter-kit/)
    $PROJECT_ROOT = $PWD.Path
}

$REPORT_FILE = Join-Path $PROJECT_ROOT ".progress-report.txt"

# Enable ANSI colour support on Windows 10 1511+ / Windows 11.
# Add-Type compiles to %TEMP% — works for standard users but may be blocked by
# AppLocker on highly locked-down enterprise machines. If it fails we strip the
# ANSI escape codes so the report renders as clean plain text instead of garbage.
$ansiEnabled = $false
try {
    $kernel32 = Add-Type -MemberDefinition @'
[DllImport("kernel32.dll", SetLastError=true)]
public static extern bool SetConsoleMode(IntPtr hConsoleHandle, uint dwMode);
[DllImport("kernel32.dll", SetLastError=true)]
public static extern IntPtr GetStdHandle(int nStdHandle);
'@ -Name 'Kernel32' -Namespace 'Win32' -PassThru
    $handle = [Win32.Kernel32]::GetStdHandle(-11)  # STD_OUTPUT_HANDLE
    [Win32.Kernel32]::SetConsoleMode($handle, 7) | Out-Null
    $ansiEnabled = $true
} catch { }

while ($true) {
    Clear-Host
    if (Test-Path $REPORT_FILE) {
        $content = Get-Content $REPORT_FILE -Raw
        if (-not $ansiEnabled) {
            # Strip ANSI escape sequences — plain text is better than raw codes
            $content = $content -replace '\x1b\[[0-9;]*[mABCDEFGHJKSTfinsulhp]', ''
        }
        Write-Host $content -NoNewline
    } else {
        Write-Host "Progress report not found yet — Claude hasn't completed a prompt." -ForegroundColor Yellow
        Write-Host "It will appear here after the first Claude Code response."
    }
    Write-Host ""
    Write-Host "[auto-refresh: 1s]  Press Q to close" -ForegroundColor DarkGray

    # Non-blocking key check: consume all queued keys, act on Q
    $quit = $false
    while ([Console]::KeyAvailable) {
        $key = [Console]::ReadKey($true)
        if ($key.KeyChar -eq 'q' -or $key.KeyChar -eq 'Q') {
            $quit = $true
        }
    }
    if ($quit) { break }

    Start-Sleep -Milliseconds 1000
}
