Set up two git worktrees for parallel development, then print launch instructions.

**Step 1 — Detect phase and check prerequisites:**

Check which phase to run:
- If `specs/modernisation/design.md` exists → **Phase 2 (Modernisation)**
- Else if `specs/feature-enhancement/design.md` exists → **Phase 1 (Feature Enhancement)**
- Else → stop and print:
  `ERROR: No design spec found. Complete spec writing (Steps 1A–1C for Phase 1, or Steps 2B–2C for Phase 2) before running parallel agents.`

Also verify:
- `git` is initialised (`.git` directory exists). If not, run `git init && git add -A && git commit -m "initial"` first.
- `worktrees/` is in `.gitignore`. If not, run `echo "worktrees/" >> .gitignore && git add .gitignore && git commit -m "chore: ignore worktrees"`.

**Step 2 — Commit specs (if not already committed):**
```bash
git add specs/ && git status
# If specs/ has changes, commit with the appropriate message:
# Phase 1: git commit -m "add Phase 1 specs"
# Phase 2: git commit -m "add Phase 2 specs"
git commit -m "add specs" 2>/dev/null || true
```

**Step 3 — Create worktrees (names depend on phase):**

For **Phase 1**:
```bash
git worktree add worktrees/feature-a -b feature/release-management
git worktree add worktrees/feature-b -b feature/sprint-analytics
```

For **Phase 2**:
```bash
git worktree add worktrees/modernisation-a -b feature/modernisation-backend
git worktree add worktrees/modernisation-b -b feature/modernisation-frontend
```

**Step 4 — Copy shared context into each worktree:**

For Phase 1 (worktree-a = `feature-a`, worktree-b = `feature-b`):
```bash
cp CLAUDE.md worktrees/feature-a/ && cp -r .claude worktrees/feature-a/
cp CLAUDE.md worktrees/feature-b/ && cp -r .claude worktrees/feature-b/
```

For Phase 2 (worktree-a = `modernisation-a`, worktree-b = `modernisation-b`):
```bash
cp CLAUDE.md worktrees/modernisation-a/ && cp -r .claude worktrees/modernisation-a/
cp CLAUDE.md worktrees/modernisation-b/ && cp -r .claude worktrees/modernisation-b/
```

**Step 5 — Install node_modules in each worktree:**

For Phase 1:
```bash
npm install --prefix worktrees/feature-a --silent 2>&1 | tail -2
npm install --prefix worktrees/feature-b --silent 2>&1 | tail -2
```

For Phase 2:
```bash
npm install --prefix worktrees/modernisation-a --silent 2>&1 | tail -2
npm install --prefix worktrees/modernisation-b --silent 2>&1 | tail -2
```

**Step 6 — Print launch instructions:**

For **Phase 1**, print exactly this block:

```
═══════════════════════════════════════════════════════════════
  PHASE 1 AGENTS READY — Open two terminal windows
═══════════════════════════════════════════════════════════════

TERMINAL 1 — Release Management + Backlog Enhancements (Agent A):
  cd worktrees/feature-a && claude

  Paste Prompt 05 from HANDSON.md

TERMINAL 2 — Sprint Analytics (Agent B):
  cd worktrees/feature-b && claude

  Paste Prompt 06 from HANDSON.md

While agents are running:
  Read specs/feature-enhancement/design.md — know what each agent should produce.
  Come back here to merge when both agents report completion.

AFTER BOTH AGENTS COMPLETE AND COMMIT — Merge (branch names, not paths):
  git merge feature/release-management
  git merge feature/sprint-analytics

  No merge conflicts expected — agents create distinct files.
  If you see a conflict, an agent modified a file outside its ownership scope.
  Resolve by keeping both sets of additions.

═══════════════════════════════════════════════════════════════
```

For **Phase 2**, print exactly this block:

```
═══════════════════════════════════════════════════════════════
  PHASE 2 AGENTS READY — Open two terminal windows
═══════════════════════════════════════════════════════════════

TERMINAL 1 — Backend Migration (Agent A):
  cd worktrees/modernisation-a && claude

  Paste Prompt 13 from HANDSON.md

TERMINAL 2 — Frontend Rewrite (Agent B):
  cd worktrees/modernisation-b && claude

  Paste Prompt 14 from HANDSON.md

While agents are running:
  Read specs/modernisation/design.md — know what each agent should produce.
  Come back here to merge when both agents report completion.

AFTER BOTH AGENTS COMPLETE AND COMMIT — Merge (branch names, not paths):
  git merge feature/modernisation-backend
  git merge feature/modernisation-frontend

  No merge conflicts expected — Agent A owns srv/, Agent B owns ui/.

═══════════════════════════════════════════════════════════════
```
