#!/usr/bin/env python3
"""
PreToolUse guard — blocks writes to credential files.

Claude Code pipes the tool input JSON to stdin.
Exit 2 to block the tool call; exit 0 to allow it.
Cross-platform: no bash, no shell-specific syntax.
"""
import json
import re
import sys

try:
    data = json.load(sys.stdin)
    path = data.get("file_path", data.get("path", ""))
    if re.search(r"(\.env|\.pem|\.key|credentials)", path):
        print(f"BLOCKED: writes to credential file '{path}' are not allowed.",
              file=sys.stderr)
        sys.exit(2)
except Exception:
    pass

sys.exit(0)
