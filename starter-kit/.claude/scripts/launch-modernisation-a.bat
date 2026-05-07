@echo off
REM Fast-path launcher for Phase 2 Agent A (CDS v9 backend migration)
REM Run from worktrees\modernisation-a:  .claude\scripts\launch-modernisation-a.bat
powershell -NoLogo -ExecutionPolicy Bypass -Command "$p = Get-Content '%~dp0..\prompts\phase2-agent-a.txt' -Raw -Encoding UTF8; & claude -p $p --max-turns 40"
