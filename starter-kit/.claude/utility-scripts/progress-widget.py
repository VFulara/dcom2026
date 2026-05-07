#!/usr/bin/env python3
"""
DCOM 2026 — Session Progress Widget

Compact desktop GUI that polls .progress-state every 2 s and renders a
visual summary of session progress.

No PowerShell, no elevation required — pure Python / tkinter.
tkinter is bundled with every standard Python installation on Windows.
"""
import json
import os
import sys
import time
import tkinter as tk
from pathlib import Path

SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
STATE_FILE   = PROJECT_ROOT / ".progress-state"
PID_FILE     = PROJECT_ROOT / ".progress-widget.pid"

STEPS = [
    {"id": "setup",  "name": "Setup & Install",       "min": 5},
    {"id": "1a",     "name": "Explore App",            "min": 2},
    {"id": "1b",     "name": "Review Requirements",    "min": 5},
    {"id": "1c",     "name": "Design Spec",            "min": 7},
    {"id": "1d",     "name": "Task List + /clear",     "min": 2},
    {"id": "1e",     "name": "Parallel Agents",        "min": 9},
    {"id": "1f",     "name": "Review Gate",            "min": 7},
    {"id": "1g",     "name": "Verify & Merge",         "min": 5},
    {"id": "2a-c",   "name": "Modernisation Specs",    "min": 5},
    {"id": "2d",     "name": "Modernisation Agents",   "min": 7},
    {"id": "2e-f",   "name": "Review & Verify",        "min": 6},
]
TOTAL_STEPS   = len(STEPS)
TOTAL_MINUTES = 60

# Catppuccin Mocha palette — dark, readable, no harsh contrast
BG     = "#1e1e2e"
CRUST  = "#11111b"
SURF   = "#313244"
FG     = "#cdd6f4"
MUTED  = "#585b70"
GREEN  = "#a6e3a1"
YELLOW = "#f9e2af"
RED    = "#f38ba8"
PURPLE = "#cba6f7"
BLUE   = "#89b4fa"


class ProgressWidget(tk.Tk):
    REFRESH_MS = 2000
    BAR_W      = 230
    BAR_H      = 14

    def __init__(self):
        super().__init__()
        self.title("DCOM 2026 — Session Progress")
        self.configure(bg=BG)
        self.resizable(False, False)
        try:
            self.attributes("-topmost", True)
        except Exception:
            pass
        try:
            PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
        except OSError:
            pass
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._schedule_refresh()

    def _on_close(self):
        try:
            PID_FILE.unlink()
        except OSError:
            pass
        self.destroy()

    # ── Layout ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Title row
        tk.Label(
            self, text="📊  DCOM 2026 – Vibe Coding",
            bg=BG, fg=PURPLE, font=("Segoe UI", 11, "bold"), anchor="w",
        ).pack(fill="x", padx=14, pady=(10, 4))

        self._hsep()

        # Overview bars (steps completed, time budget)
        self._steps_bar, self._steps_lbl = self._bar_row("Steps")
        self._time_bar,  self._time_lbl  = self._bar_row("Time ")

        self._hsep(pady=6)

        # Step table — column headers
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=14)
        for txt, w, anc in [("  Step", 29, "w"), ("Exp", 4, "e"), ("Actual", 7, "e")]:
            tk.Label(hdr, text=txt, bg=BG, fg=MUTED,
                     font=("Segoe UI", 8), width=w, anchor=anc).pack(side="left")

        # Step rows
        self._rows: list[tuple] = []
        for step in STEPS:
            f    = tk.Frame(self, bg=BG)
            f.pack(fill="x", padx=14, pady=1)
            icon = tk.Label(f, text="·", bg=BG, fg=MUTED,
                            font=("Segoe UI", 10), width=2,  anchor="w")
            name = tk.Label(f, text=step["name"], bg=BG, fg=MUTED,
                            font=("Segoe UI", 9),  width=27, anchor="w")
            exp  = tk.Label(f, text=f"{step['min']}m", bg=BG, fg=MUTED,
                            font=("Segoe UI", 8),  width=4,  anchor="e")
            act  = tk.Label(f, text="", bg=BG, fg=MUTED,
                            font=("Segoe UI", 8),  width=7,  anchor="e")
            for w in (icon, name, exp, act):
                w.pack(side="left")
            self._rows.append((icon, name, exp, act))

        self._hsep(pady=6)

        # Footer status line
        self._footer = tk.Label(
            self, text="Waiting for first Claude response…",
            bg=BG, fg=MUTED, font=("Segoe UI", 8), anchor="w",
        )
        self._footer.pack(fill="x", padx=14, pady=(0, 10))

    def _hsep(self, pady: int = 2) -> None:
        tk.Frame(self, bg=MUTED, height=1).pack(fill="x", padx=14, pady=pady)

    def _bar_row(self, label: str) -> tuple:
        """Create a labelled progress bar row; return (canvas, label widget)."""
        f = tk.Frame(self, bg=BG)
        f.pack(fill="x", padx=14, pady=2)
        tk.Label(f, text=label, bg=BG, fg=MUTED,
                 font=("Segoe UI", 8), width=5, anchor="w").pack(side="left")
        c = tk.Canvas(f, bg=SURF, height=self.BAR_H, width=self.BAR_W,
                      highlightthickness=0)
        c.pack(side="left", padx=4)
        c.create_rectangle(0, 0, 2, self.BAR_H, fill=GREEN, outline="", tags="fill")
        lbl = tk.Label(f, text="", bg=BG, fg=FG,
                       font=("Segoe UI", 8), anchor="w")
        lbl.pack(side="left", padx=4)
        return c, lbl

    # ── Refresh loop ─────────────────────────────────────────────────────────

    def _schedule_refresh(self) -> None:
        try:
            self._update()
        except Exception:
            pass
        self.after(self.REFRESH_MS, self._schedule_refresh)

    # ── Data loading ─────────────────────────────────────────────────────────

    @staticmethod
    def _load_state() -> dict:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    # ── Rendering ────────────────────────────────────────────────────────────

    def _update(self) -> None:
        now   = int(time.time())
        state = self._load_state()

        statuses      = state.get("statuses", {s["id"]: "pending" for s in STEPS})
        timing        = state.get("step_timing", {})
        session_start = state.get("session_start", now)
        prompt_count  = state.get("prompt_count", 0)

        elapsed_sec = now - session_start
        elapsed_min = elapsed_sec / 60
        completed   = sum(1 for v in statuses.values() if v == "done")
        steps_pct   = int(completed * 100 / TOTAL_STEPS)
        budget_pct  = min(100, int(elapsed_min * 100 / TOTAL_MINUTES))
        budget_left = max(0.0, TOTAL_MINUTES - elapsed_min)

        # Steps progress bar
        self._draw_bar(self._steps_bar, steps_pct, GREEN)
        self._steps_lbl.config(
            text=f"{steps_pct}%   ({completed} / {TOTAL_STEPS} steps)", fg=FG)

        # Time budget bar (colour shifts yellow → red as time runs out)
        tc = self._budget_color(budget_pct)
        self._draw_bar(self._time_bar, budget_pct, tc)
        self._time_lbl.config(text=f"{elapsed_min:.0f}m / {TOTAL_MINUTES}m", fg=tc)

        # Per-step rows
        for i, step in enumerate(STEPS):
            self._render_row(
                i, statuses.get(step["id"], "pending"),
                step, timing.get(step["id"], {}), now,
            )

        # Footer
        m, s = divmod(int(elapsed_sec), 60)
        if elapsed_min > TOTAL_MINUTES:
            tail = f"  ⚠  OVER by {int(elapsed_min - TOTAL_MINUTES)}m"
            tc   = RED
        else:
            tail = f"  •  {budget_left:.0f}m remaining"
            tc   = MUTED
        self._footer.config(
            text=f"⏱  {m}m {s:02d}s elapsed   •   {prompt_count} prompts{tail}",
            fg=tc,
        )

    def _render_row(self, idx: int, status: str, step: dict,
                    rec: dict, now: int) -> None:
        icon, name_lbl, exp_lbl, act_lbl = self._rows[idx]
        if status == "done":
            actual  = rec.get("actual_minutes", "")
            over    = (actual != "" and actual > step["min"] * 1.2)
            icon.config(text="✓", fg=GREEN)
            name_lbl.config(fg=FG)
            exp_lbl.config(fg=MUTED)
            act_lbl.config(text=f"{actual}m" if actual != "" else "",
                           fg=RED if over else GREEN)
        elif status == "active":
            started = rec.get("started_at", now)
            spent   = round((now - started) / 60, 1)
            over    = spent > step["min"] * 1.2
            icon.config(text="▶", fg=YELLOW)
            name_lbl.config(fg=YELLOW)
            exp_lbl.config(fg=YELLOW)
            act_lbl.config(text=f"{spent}m…", fg=RED if over else YELLOW)
        else:
            icon.config(text="·", fg=MUTED)
            name_lbl.config(fg=MUTED)
            exp_lbl.config(fg=MUTED)
            act_lbl.config(text="", fg=MUTED)

    def _draw_bar(self, canvas: tk.Canvas, pct: int,
                  color: str, width: int = 230) -> None:
        filled = max(2, int(pct * width / 100))
        canvas.itemconfig("fill", fill=color)
        canvas.coords("fill", 0, 0, filled, self.BAR_H)

    @staticmethod
    def _budget_color(pct: int) -> str:
        if pct <= 75:
            return GREEN
        if pct <= 100:
            return YELLOW
        return RED


if __name__ == "__main__":
    app = ProgressWidget()
    app.mainloop()
