#!/usr/bin/env python3
"""
PreToolUse guard — blocks console.log/error/warn inside srv/ files.

Claude Code pipes the tool input JSON to stdin.
Exit 2 to block; exit 0 to allow.
Cross-platform: no bash, no shell-specific syntax.
"""
import json
import re
import sys

try:
    data    = json.load(sys.stdin)
    path    = data.get("file_path", data.get("path", "")).replace("\\", "/")
    content = data.get("content", data.get("new_string", ""))
    is_srv  = bool(re.search(r"/srv/", path))
    has_log = bool(re.search(r"console\.(log|error|warn)", content))
    if is_srv and has_log:
        print("BLOCKED: use cds.log() instead of console.log() in srv/ files.",
              file=sys.stderr)
        sys.exit(2)
except Exception:
    pass

sys.exit(0)
