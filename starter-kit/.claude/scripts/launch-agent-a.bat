@echo off
REM Fast-path launcher for Phase 1 Agent A (Release Management)
REM Run from worktrees\feature-a:  .claude\scripts\launch-agent-a.bat
powershell -NoLogo -ExecutionPolicy Bypass -Command "$p = Get-Content '%~dp0..\prompts\phase1-agent-a.txt' -Raw -Encoding UTF8; & claude -p $p --max-turns 40"
