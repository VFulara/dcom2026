@echo off
REM Fast-path launcher for Phase 1 Agent B (Sprint Analytics)
REM Run from worktrees\feature-b:  .claude\scripts\launch-agent-b.bat
powershell -NoLogo -ExecutionPolicy Bypass -Command "$p = Get-Content '%~dp0..\prompts\phase1-agent-b.txt' -Raw -Encoding UTF8; & claude -p $p --max-turns 40"
