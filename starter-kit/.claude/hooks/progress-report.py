#!/usr/bin/env python3
"""
Progress Report Hook — shows participant progress through the DCOM 2026 hands-on session.
Triggered on every Claude "Stop" event (after each prompt response).
"""

import json
import os
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
STATE_FILE = PROJECT_ROOT / ".progress-state"

# ─────────────────────────────────────────────────────────────────────────────
# Step definitions with normalised expected minutes (total = 60 min)
# Based on handson-test-findings timing, normalised for 60-min session
# ─────────────────────────────────────────────────────────────────────────────
STEPS = [
    {"id": "setup",  "name": "Setup & Install",           "minutes": 5},
    {"id": "1a",     "name": "1A: Explore App",           "minutes": 2},
    {"id": "1b",     "name": "1B: Review Requirements",   "minutes": 5},
    {"id": "1c",     "name": "1C: Design Spec",           "minutes": 7},
    {"id": "1d",     "name": "1D: Task List + /clear",    "minutes": 2},
    {"id": "1e",     "name": "1E: Parallel Agents",       "minutes": 9},
    {"id": "1f",     "name": "1F: Review Gate",           "minutes": 7},
    {"id": "1g",     "name": "1G: Verify & Merge",        "minutes": 5},
    {"id": "2a-c",   "name": "2A-C: Modernisation Specs", "minutes": 5},
    {"id": "2d",     "name": "2D: Modernisation Agents",  "minutes": 7},
    {"id": "2e-f",   "name": "2E-F: Review & Verify",     "minutes": 6},
]

TOTAL_STEPS = len(STEPS)
TOTAL_MINUTES = 60

# ─────────────────────────────────────────────────────────────────────────────
# ANSI colour codes
# ─────────────────────────────────────────────────────────────────────────────
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
RED = "\033[31m"
WHITE = "\033[97m"


def load_state():
    """Load or initialise the progress state file."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    state = {
        "session_start": int(time.time()),
        "prompt_count": 0,
    }
    save_state(state)
    return state


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def detect_step_status():
    """Check filesystem artifacts to determine which steps are completed."""
    p = PROJECT_ROOT

    checks = {
        "has_node_modules": (p / "node_modules").is_dir(),
        "has_git": (p / ".git").is_dir(),
        "has_requirements": (p / "specs" / "feature-enhancement" / "requirements.md").is_file(),
        "has_design": (p / "specs" / "feature-enhancement" / "design.md").is_file(),
        "has_todo": (p / "specs" / "feature-enhancement" / "todo.md").is_file(),
        "has_worktrees_p1": (p / "worktrees" / "feature-a").is_dir() or (p / "worktrees" / "feature-b").is_dir(),
        "has_merge_p1": (p / "srv" / "release-service.cds").is_file() or (p / "srv" / "analytics-service.cds").is_file(),
        "has_verify_p1": (p / "srv" / "release-service.cds").is_file() and (p / "srv" / "analytics-service.cds").is_file(),
        "has_modern_specs": (p / "specs" / "modernisation" / "design.md").is_file(),
        "has_worktrees_p2": (p / "worktrees" / "modernisation-a").is_dir() or (p / "worktrees" / "modernisation-b").is_dir(),
        "has_modern_dir": (p / "modern").is_dir(),
    }

    # Sequential detection — each step is "done" if its completion artifact exists
    # and the next step's trigger condition is met
    conditions = [
        ("setup",  lambda c: c["has_node_modules"] and c["has_git"]),
        ("1a",     lambda c: c["has_requirements"]),
        ("1b",     lambda c: c["has_design"]),
        ("1c",     lambda c: c["has_todo"]),
        ("1d",     lambda c: c["has_worktrees_p1"]),
        ("1e",     lambda c: c["has_merge_p1"]),
        ("1f",     lambda c: c["has_verify_p1"]),
        ("1g",     lambda c: c["has_modern_specs"]),
        ("2a-c",   lambda c: c["has_worktrees_p2"]),
        ("2d",     lambda c: c["has_modern_dir"]),
        ("2e-f",   lambda c: False),  # final step — always active once reached
    ]

    statuses = {}
    current_step = None

    for i, (step_id, condition) in enumerate(conditions):
        if condition(checks):
            statuses[step_id] = "done"
        else:
            statuses[step_id] = "active"
            current_step = step_id
            # Mark the rest as pending
            for j in range(i + 1, len(conditions)):
                statuses[conditions[j][0]] = "pending"
            break

    # Edge case: all done
    if current_step is None and all(v == "done" for v in statuses.values()):
        # Mark last step as active (it's the "verify" step — always in progress until session ends)
        statuses["2e-f"] = "active"
        current_step = "2e-f"

    return statuses, current_step


def render_progress_bar(completed, total, width=40):
    """Render a Unicode progress bar."""
    filled = int(completed * width / total) if total > 0 else 0
    empty = width - filled

    bar = "█" * filled
    if empty > 0:
        bar += "▓" + "░" * (empty - 1)
    return bar


def format_time(seconds):
    """Format seconds as Xm Ys."""
    m = seconds // 60
    s = seconds % 60
    return f"{m}m {s:02d}s"


def main():
    state = load_state()
    state["prompt_count"] = state.get("prompt_count", 0) + 1
    prompt_count = state["prompt_count"]
    session_start = state["session_start"]

    now = int(time.time())
    elapsed_seconds = now - session_start
    elapsed_minutes = elapsed_seconds // 60

    # Detect step statuses
    statuses, current_step = detect_step_status()

    # Count completed
    completed_count = sum(1 for s in statuses.values() if s == "done")
    progress_pct = int(completed_count * 100 / TOTAL_STEPS)

    # Calculate expected elapsed time
    expected_elapsed = 0
    for step in STEPS:
        status = statuses.get(step["id"], "pending")
        if status == "done":
            expected_elapsed += step["minutes"]
        elif status == "active":
            expected_elapsed += step["minutes"] // 2
            break

    # Save updated state
    state["last_check"] = now
    state["current_step"] = current_step
    state["completed_count"] = completed_count
    save_state(state)

    # ─── Render ───────────────────────────────────────────────────────────────
    bar = render_progress_bar(completed_count, TOTAL_STEPS)

    # Time status colouring
    if elapsed_minutes <= expected_elapsed:
        time_color = GREEN
        time_icon = "⏱️ "
    elif elapsed_minutes <= expected_elapsed + 5:
        time_color = YELLOW
        time_icon = "⏳"
    else:
        time_color = RED
        time_icon = "🔴"

    remaining = TOTAL_MINUTES - elapsed_minutes

    # Print report
    print()
    print(f"{BOLD}{CYAN}┌──────────────────────────────────────────────────────────────────┐{RESET}")
    print(f"{BOLD}{CYAN}│{RESET}  {BOLD}{WHITE}📊 DCOM 2026 — Session Progress Report{RESET}                          {BOLD}{CYAN}│{RESET}")
    print(f"{BOLD}{CYAN}├──────────────────────────────────────────────────────────────────┤{RESET}")
    print()

    # Progress bar
    print(f"  {BOLD}Progress:{RESET}  {GREEN}{bar}{RESET}  {BOLD}{progress_pct}%{RESET}  ({completed_count}/{TOTAL_STEPS} steps)")
    print()

    # Timing summary
    elapsed_str = format_time(elapsed_seconds)
    print(f"  {time_color}{time_icon} Time: {elapsed_str} elapsed{RESET}  │  {DIM}Expected: ~{expected_elapsed}m{RESET}  │  {DIM}Budget: {TOTAL_MINUTES}m total{RESET}")

    if remaining > 0:
        print(f"  {DIM}Time remaining: ~{remaining}m{RESET}")
    else:
        over = elapsed_minutes - TOTAL_MINUTES
        print(f"  {RED}{BOLD}⚠️  Over time by {over}m{RESET}")
    print()

    # Step breakdown
    print(f"  {BOLD}{BLUE}Step Breakdown:{RESET}")
    print(f"  {DIM}─────────────────────────────────────────────────────────────{RESET}")

    for step in STEPS:
        step_id = step["id"]
        step_name = step["name"]
        step_min = step["minutes"]
        status = statuses.get(step_id, "pending")

        if status == "done":
            icon = "✅"
            color = GREEN
            status_text = "done"
        elif status == "active":
            icon = "🔄"
            color = YELLOW
            status_text = "in progress"
        else:
            icon = "⬜"
            color = DIM
            status_text = "pending"

        print(f"  {color}{icon} {step_name:<28}  [{step_min:2d}m expected]  {status_text}{RESET}")

    print()
    print(f"  {DIM}─────────────────────────────────────────────────────────────{RESET}")

    # Current step highlight
    if current_step:
        step_info = next((s for s in STEPS if s["id"] == current_step), None)
        if step_info:
            print(f"  {BOLD}{MAGENTA}▶ Current: {step_info['name']}{RESET} {DIM}(expected: {step_info['minutes']}m){RESET}")

    # Prompt counter
    print(f"  {DIM}Prompts executed: {prompt_count}{RESET}")
    print()
    print(f"{BOLD}{CYAN}└──────────────────────────────────────────────────────────────────┘{RESET}")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Silently fail — never block the participant's workflow
        pass
