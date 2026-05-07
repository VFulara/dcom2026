@echo off
REM Fast-path launcher for Phase 2 Agent B (React frontend rewrite)
REM Run from worktrees\modernisation-b:  .claude\scripts\launch-modernisation-b.bat
powershell -NoLogo -ExecutionPolicy Bypass -Command "$p = Get-Content '%~dp0..\prompts\phase2-agent-b.txt' -Raw -Encoding UTF8; & claude -p $p --max-turns 40"
