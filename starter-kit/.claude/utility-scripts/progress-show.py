#!/usr/bin/env python3
"""
Auto-refreshing progress report viewer for Windows.
Pure Python — no PowerShell required, works for all user types including
standard/guest accounts with no elevated or script-execution rights.
Press Ctrl+C to close.
"""
import os
import re
import sys
import time
from pathlib import Path

SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
REPORT_FILE  = PROJECT_ROOT / ".progress-report.txt"

# Enable ANSI colour output on Windows 10 1511+ / Windows 11.
# SetConsoleMode does not require elevated rights.
_ansi_ok = False
try:
    import ctypes
    _h = ctypes.windll.kernel32.GetStdHandle(-11)   # STD_OUTPUT_HANDLE
    ctypes.windll.kernel32.SetConsoleMode(_h, 7)
    _ansi_ok = True
except Exception:
    pass


def _strip_ansi(text: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*[mABCDEFGHJKSTfinsulhp]', '', text)


def _clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


if __name__ == "__main__":
    while True:
        _clear()
        if REPORT_FILE.exists():
            try:
                content = REPORT_FILE.read_text(encoding="utf-8")
                if not _ansi_ok:
                    content = _strip_ansi(content)
            except OSError:
                content = "Error reading progress file — will retry.\n"
        else:
            content = (
                "Progress report not found yet.\n"
                "It will appear here after the first Claude Code response.\n"
            )
        print(content, end="")
        print()
        print("[auto-refresh: 2s]  Ctrl+C to close")
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            break
