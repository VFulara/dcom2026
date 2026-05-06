#!/usr/bin/env python3
"""
Progress Report Hook — DCOM 2026 Vibe Coding session tracker.

Runs on every Claude Code "Stop" event (after each prompt response).
Cross-platform: macOS, Windows, Linux — no OS-specific APIs.

Behaviour:
  Normal mode (no args):
    - Increments prompt counter
    - Detects completed guide steps via filesystem artifacts
    - Records per-step timing (start, end, actual minutes, prompts used)
    - Writes .progress-report.txt (always)
    - Prints ANSI report to stdout ONLY when a 3-step milestone is reached
      (visible in Claude Code CLI after Claude's response)

  Display mode (--display):
    - Shows the current report without modifying state
    - Used by the /display-progress slash command
"""

import argparse
import io
import json
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
STATE_FILE   = PROJECT_ROOT / ".progress-state"
REPORT_FILE  = PROJECT_ROOT / ".progress-report.txt"

STEPS = [
    {"id": "setup",  "name": "Step 1: Setup & Install",          "minutes": 5},
    {"id": "1a",     "name": "Step 2: Explore App (optional)",   "minutes": 2},
    {"id": "1b",     "name": "Step 3: Review Requirements",      "minutes": 5},
    {"id": "1c",     "name": "Step 4: Design Spec",              "minutes": 7},
    {"id": "1d",     "name": "Step 5: Task List + /clear",       "minutes": 2},
    {"id": "1e",     "name": "Step 6: Parallel Agents",          "minutes": 9},
    {"id": "1f",     "name": "Step 7: Review Gate",              "minutes": 7},
    {"id": "1g",     "name": "Step 8: Verify & Merge",           "minutes": 5},
    {"id": "2a-c",   "name": "Steps 9-10: Modernisation Specs",  "minutes": 5},
    {"id": "2d",     "name": "Step 11: Modernisation Agents",    "minutes": 7},
    {"id": "2e-f",   "name": "Steps 12-13: Review & Verify",     "minutes": 6},
]

TOTAL_STEPS   = len(STEPS)
TOTAL_MINUTES = 60
DISPLAY_EVERY = 1

RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
CYAN    = "\033[36m"
MAGENTA = "\033[35m"
RED     = "\033[31m"
WHITE   = "\033[97m"

if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass


def load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    state = {
        "session_start":           int(time.time()),
        "prompt_count":            0,
        "last_display_step_count": 0,
        "step_timing":             {},
        "current_step_started_at": int(time.time()),
        "current_step_prompts":    0,
    }
    save_state(state)
    return state


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def detect_step_status():
    p = PROJECT_ROOT
    git_ok = subprocess.run(
        ["git", "-C", str(p), "rev-parse", "--git-dir"],
        capture_output=True,
    ).returncode == 0

    checks = {
        "has_node_modules":  (p / "node_modules").is_dir(),
        "has_git":           git_ok,
        "has_requirements":  (p / "specs" / "feature-enhancement" / "requirements.md").is_file(),
        "has_design":        (p / "specs" / "feature-enhancement" / "design.md").is_file(),
        "has_todo":          (p / "specs" / "feature-enhancement" / "todo.md").is_file(),
        "has_worktrees_p1":  (p / "worktrees" / "feature-a").is_dir() or
                             (p / "worktrees" / "feature-b").is_dir(),
        "has_merge_p1":      (p / "srv" / "release-service.cds").is_file() or
                             (p / "srv" / "analytics-service.cds").is_file(),
        "has_verify_p1":     (p / "srv" / "release-service.cds").is_file() and
                             (p / "srv" / "analytics-service.cds").is_file(),
        "has_modern_specs":  (p / "specs" / "modernisation" / "design.md").is_file(),
        "has_worktrees_p2":  (p / "worktrees" / "modernisation-a").is_dir() or
                             (p / "worktrees" / "modernisation-b").is_dir(),
        "has_modern_dir":    (p / "modern").is_dir(),
    }

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
        ("2e-f",   lambda _: False),
    ]

    statuses     = {}
    current_step = None

    for i, (step_id, condition) in enumerate(conditions):
        if condition(checks):
            statuses[step_id] = "done"
        else:
            statuses[step_id] = "active"
            current_step = step_id
            for j in range(i + 1, len(conditions)):
                statuses[conditions[j][0]] = "pending"
            break

    if current_step is None and all(v == "done" for v in statuses.values()):
        statuses["2e-f"] = "active"
        current_step = "2e-f"

    return statuses, current_step


def update_step_timing(state, statuses, current_step, now):
    prev_step = state.get("current_step")
    timing    = state.setdefault("step_timing", {})

    if current_step == prev_step:
        state["current_step_prompts"] = state.get("current_step_prompts", 0) + 1
        return

    if prev_step and statuses.get(prev_step) == "done":
        rec = timing.setdefault(prev_step, {})
        rec.setdefault("started_at", state.get("current_step_started_at", now))
        rec["completed_at"]   = now
        rec["actual_minutes"] = round((now - rec["started_at"]) / 60, 1)
        rec["prompts"]        = state.get("current_step_prompts", 1)

    if current_step:
        timing.setdefault(current_step, {}).setdefault("started_at", now)

    state["current_step_started_at"] = now
    state["current_step_prompts"]    = 1


def compute_pace_and_projection(state, statuses, now):
    timing         = state.get("step_timing", {})
    actual_total   = 0.0
    expected_total = 0.0

    for step in STEPS:
        if statuses.get(step["id"]) == "done":
            rec = timing.get(step["id"], {})
            if "actual_minutes" in rec:
                actual_total   += rec["actual_minutes"]
                expected_total += step["minutes"]

    pace_ratio = (actual_total / expected_total) if expected_total > 0 else 1.0

    remaining_expected  = sum(
        s["minutes"] for s in STEPS
        if statuses.get(s["id"]) in ("active", "pending")
    )
    projected_remaining = remaining_expected * pace_ratio
    projected_finish_ts = now + projected_remaining * 60

    return pace_ratio, int(projected_finish_ts), round(projected_remaining)


def render_progress_bar(completed, total, width=36):
    filled = int(completed * width / total) if total > 0 else 0
    empty  = width - filled
    bar    = "█" * filled
    if empty > 0:
        bar += "▓" + "░" * (empty - 1)
    return bar


def render_budget_bar(elapsed_min, total_min, width=40):
    pct    = min(1.0, elapsed_min / total_min) if total_min > 0 else 0
    filled = round(pct * width)
    return "█" * filled + "░" * (width - filled), round(pct * 100)


def render_mini_bar(status, rec, expected_min, now, width=10):
    if status == "done" and "actual_minutes" in rec:
        actual = rec["actual_minutes"]
        filled = min(width, round(actual / expected_min * width)) if expected_min else 0
        bar    = "█" * filled + "░" * (width - filled)
        return bar, actual > expected_min * 1.2
    if status == "active":
        elapsed = (now - rec.get("started_at", now)) / 60
        filled  = min(width, round(elapsed / expected_min * width)) if expected_min else 0
        return "▓" * filled + "░" * (width - filled), False
    return "░" * width, False


CLOCK_EMOJIS = [
    (7,  "🕛"), (15, "🕐"), (23, "🕑"), (31, "🕒"),
    (39, "🕓"), (47, "🕔"), (55, "🕕"), (63, "🕖"),
    (71, "🕗"), (79, "🕘"), (87, "🕙"), (95, "🕚"), (100, "🕛"),
]


def clock_emoji(pct_used):
    for threshold, emoji in CLOCK_EMOJIS:
        if pct_used <= threshold:
            return emoji
    return "🕛"


def format_elapsed(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s:02d}s"


def format_hhmm(ts):
    return time.strftime("%H:%M", time.localtime(ts))


def _time_color(elapsed_min, expected_min):
    if elapsed_min <= expected_min:
        return GREEN
    if elapsed_min <= expected_min + 5:
        return YELLOW
    return RED


def _pace_color(pace_pct):
    if pace_pct <= 110:
        return GREEN
    if pace_pct <= 130:
        return YELLOW
    return RED


def _budget_color(budget_pct):
    if budget_pct <= 75:
        return GREEN
    if budget_pct <= 100:
        return YELLOW
    return RED


def _step_parts(status):
    if status == "done":
        return "✅", GREEN, "done"
    if status == "active":
        return "🔄", YELLOW, "in progress"
    return "⬜", DIM, "pending"


def _expected_elapsed_min(statuses):
    total = 0
    for step in STEPS:
        st = statuses.get(step["id"], "pending")
        if st == "done":
            total += step["minutes"]
        elif st == "active":
            total += step["minutes"] // 2
            break
    return total


def _step_act_and_prompts(status, rec, state, now):
    if status == "done" and "actual_minutes" in rec:
        return f"{rec['actual_minutes']}m", str(rec.get("prompts", "—"))
    if status == "active":
        spent = round((now - rec.get("started_at", now)) / 60, 1)
        return f"{spent}m…", str(state.get("current_step_prompts", "—"))
    return "—", "—"


def _render_timing_header(p, elapsed_sec, elapsed_min, expected_elapsed,
                          completed_count, pace_pct, proj_finish_ts, proj_remaining):
    tc = _time_color(elapsed_min, expected_elapsed)
    p(f"  {tc}⏱  Elapsed: {format_elapsed(elapsed_sec)}  │  "
      f"Expected at this point: ~{expected_elapsed}m{RESET}")

    if completed_count >= 2:
        pc = _pace_color(pace_pct)
        p(f"  {pc}📈 Pace: {pace_pct}% of expected  │  "
          f"Projected finish: ~{format_hhmm(proj_finish_ts)} "
          f"({proj_remaining}m remaining){RESET}")
    else:
        p(f"  {DIM}📈 Pace projection available after 2 completed steps{RESET}")


def _render_step_table(p, statuses, step_timing, state, now, border):
    p(f"  {BOLD}{BLUE}Step Breakdown:{RESET}")
    p(f"  {DIM}{border}{RESET}")
    p(f"  {BOLD}  {'Step':<30} {'Exp':>3}  {'Bar':<10}  {'Actual':>6}  {'Prompts':>7}{RESET}")
    p(f"  {DIM}{border}{RESET}")
    for step in STEPS:
        sid    = step["id"]
        status = statuses.get(sid, "pending")
        icon, color, _ = _step_parts(status)
        rec            = step_timing.get(sid, {})
        act, prompts_str = _step_act_and_prompts(status, rec, state, now)
        mini_bar, over  = render_mini_bar(status, rec, step["minutes"], now)
        bar_str = mini_bar + (" ⚠" if over else "  ")
        p(f"  {color}{icon} {step['name']:<30} {step['minutes']:>2}m  "
          f"{bar_str}  {act:>6}  {prompts_str:>7}{RESET}")


def build_report(state, statuses, current_step, now, prompt_count):
    session_start    = state["session_start"]
    elapsed_sec      = now - session_start
    elapsed_min      = elapsed_sec // 60
    elapsed_min_f    = elapsed_sec / 60
    completed_count  = sum(1 for s in statuses.values() if s == "done")
    progress_pct     = int(completed_count * 100 / TOTAL_STEPS)
    expected_elapsed = _expected_elapsed_min(statuses)

    pace_ratio, proj_finish_ts, proj_remaining = compute_pace_and_projection(
        state, statuses, now
    )
    pace_pct    = int(pace_ratio * 100)
    budget_left = max(0, TOTAL_MINUTES - elapsed_min)
    bar         = render_progress_bar(completed_count, TOTAL_STEPS)

    budget_bar_str, budget_pct = render_budget_bar(elapsed_min_f, TOTAL_MINUTES)
    remaining_min_f = max(0.0, TOTAL_MINUTES - elapsed_min_f)
    ck = clock_emoji(budget_pct)
    bc = _budget_color(budget_pct)

    buf = io.StringIO()

    def p(line=""):
        print(line, file=buf)

    W = 74
    border = "─" * W

    p()
    p(f"{BOLD}{CYAN}┌{border}┐{RESET}")
    p(f"{BOLD}{CYAN}│{RESET}  {BOLD}{WHITE}📊 DCOM 2026 — Vibe Coding Session Progress{RESET}"
      f"{'':28}{BOLD}{CYAN}│{RESET}")
    p(f"{BOLD}{CYAN}├{border}┤{RESET}")
    p()
    p(f"  {BOLD}Steps:{RESET}    {GREEN}{bar}{RESET}  {BOLD}{progress_pct}%{RESET}"
      f"  ({completed_count}/{TOTAL_STEPS} steps)")

    step_icons = []
    for step in STEPS:
        st = statuses.get(step["id"], "pending")
        if st == "done":
            step_icons.append("✅")
        elif st == "active":
            step_icons.append("🔄")
        else:
            step_icons.append("⬜")
    p(f"  {'  '.join(step_icons)}")
    p()

    p(f"  {BOLD}Budget:{RESET}   {ck}  {bc}{budget_bar_str}{RESET}"
      f"  {BOLD}{budget_pct}%{RESET}"
      f"  ({elapsed_min_f:.1f}m elapsed · {remaining_min_f:.1f}m left)")

    _render_timing_header(p, elapsed_sec, elapsed_min, expected_elapsed,
                          completed_count, pace_pct, proj_finish_ts, proj_remaining)

    if budget_left <= 0:
        p(f"  {RED}{BOLD}⚠  Over time by {elapsed_min - TOTAL_MINUTES}m{RESET}")
    p()

    _render_step_table(p, statuses, state.get("step_timing", {}), state, now, border)

    p()
    p(f"  {DIM}{border}{RESET}")

    if current_step:
        step_info = next((s for s in STEPS if s["id"] == current_step), None)
        if step_info:
            p(f"  {BOLD}{MAGENTA}▶ Active: {step_info['name']}{RESET} "
              f"{DIM}(budget: {step_info['minutes']}m){RESET}")

    p(f"  {DIM}Prompts this session: {prompt_count}  │  "
      f"Type /display-progress anytime to see this{RESET}")
    p()
    p(f"{BOLD}{CYAN}└{border}┘{RESET}")
    p()

    return buf.getvalue()


RUNNER_SCRIPT = SCRIPT_DIR.parent / "utility-scripts" / "progress-show.sh"


def _is_display_already_running():
    if sys.platform == "win32":
        return False

    try:
        probe = subprocess.run(
            ["pgrep", "-f", str(RUNNER_SCRIPT)],
            capture_output=True,
            text=True,
        )
        return probe.returncode == 0 and bool(probe.stdout.strip())
    except Exception:
        return False


def _spawn_darwin():
    RUNNER_SCRIPT.chmod(0o755)
    subprocess.Popen(
        ["open", "-a", "Terminal", str(RUNNER_SCRIPT)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def _spawn_win32():
    subprocess.Popen(
        ["powershell", "-NoExit", "-Command",
         f'Get-Content "{REPORT_FILE}"; Read-Host "[press Enter to close]"'],
        creationflags=0x00000010,  # CREATE_NEW_CONSOLE
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def _spawn_linux():
    cmd = f'bash -c "clear; cat \\"{REPORT_FILE}\\"; echo; read -p \\"[press Enter to close]\\" x"'
    for term, flag in [
        ("gnome-terminal", "--"),
        ("xterm",          "-e"),
        ("konsole",        "-e"),
        ("xfce4-terminal", "-e"),
    ]:
        if subprocess.run(["which", term], capture_output=True).returncode == 0:
            subprocess.Popen(
                [term, flag, cmd],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return


def spawn_terminal_display():
    if _is_display_already_running():
        return

    if sys.platform == "darwin":
        _spawn_darwin()
    elif sys.platform == "win32":
        _spawn_win32()
    else:
        _spawn_linux()


def display_mode():
    state = load_state()
    now   = int(time.time())
    statuses, current_step = detect_step_status()
    output = build_report(state, statuses, current_step, now,
                          state.get("prompt_count", 0))
    REPORT_FILE.write_text(output, encoding="utf-8")
    spawn_terminal_display()


def hook_mode():
    state = load_state()
    state["prompt_count"] = state.get("prompt_count", 0) + 1
    prompt_count = state["prompt_count"]

    now = int(time.time())
    statuses, current_step = detect_step_status()
    completed_count = sum(1 for s in statuses.values() if s == "done")

    update_step_timing(state, statuses, current_step, now)

    last_display  = state.get("last_display_step_count", 0)
    milestone_hit = completed_count > 0 and (completed_count - last_display) >= DISPLAY_EVERY

    state["last_check"]      = now
    state["current_step"]    = current_step
    state["completed_count"] = completed_count
    if milestone_hit:
        state["last_display_step_count"] = completed_count

    output = build_report(state, statuses, current_step, now, prompt_count)
    REPORT_FILE.write_text(output, encoding="utf-8")

    if milestone_hit:
        spawn_terminal_display()

    save_state(state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--display", action="store_true")
    args, _ = parser.parse_known_args()

    try:
        if args.display:
            display_mode()
        else:
            hook_mode()
    except Exception:
        pass
