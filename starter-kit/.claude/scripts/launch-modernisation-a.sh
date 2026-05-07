#!/bin/bash
# Fast-path launcher for Phase 2 Agent A (CDS v9 backend migration)
# Run from worktrees/modernisation-a:  bash .claude/scripts/launch-modernisation-a.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
claude -p "$(cat "$SCRIPT_DIR/../prompts/phase2-agent-a.txt")" --max-turns 40
