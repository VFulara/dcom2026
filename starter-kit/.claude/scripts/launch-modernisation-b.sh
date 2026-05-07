#!/bin/bash
# Fast-path launcher for Phase 2 Agent B (React frontend rewrite)
# Run from worktrees/modernisation-b:  bash .claude/scripts/launch-modernisation-b.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
claude -p "$(cat "$SCRIPT_DIR/../prompts/phase2-agent-b.txt")" --max-turns 40
