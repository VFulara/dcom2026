#!/bin/bash
# Fast-path launcher for Phase 1 Agent B (Sprint Analytics)
# Run from worktrees/feature-b:  bash .claude/scripts/launch-agent-b.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
claude -p "$(cat "$SCRIPT_DIR/../prompts/phase1-agent-b.txt")" --max-turns 40
