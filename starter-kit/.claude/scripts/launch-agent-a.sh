#!/bin/bash
# Fast-path launcher for Phase 1 Agent A (Release Management)
# Run from worktrees/feature-a:  bash .claude/scripts/launch-agent-a.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
claude -p "$(cat "$SCRIPT_DIR/../prompts/phase1-agent-a.txt")" --max-turns 40
