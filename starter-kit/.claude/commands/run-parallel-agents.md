Set up two git worktrees for parallel development, then print launch instructions.

**Step 1 — Detect phase and check prerequisites:**

Check which phase to run:
- If `specs/modernisation/design.md` exists → **Phase 2 (Modernisation)**
- Else if `specs/feature-enhancement/design.md` exists → **Phase 1 (Feature Enhancement)**
- Else → stop and print:
  `ERROR: No design spec found. Complete spec writing (Steps 1A–1C for Phase 1, or Steps 2B–2C for Phase 2) before running parallel agents.`

Also verify:
- `git` is initialised (`.git` directory exists). If not, run `git init && git add -A && git commit -m "initial"` first.
- `worktrees/` is in `.gitignore`. If not, add it using Node:
  ```
  node -e "const fs=require('fs'),p='.gitignore'; const c=fs.existsSync(p)?fs.readFileSync(p,'utf8'):''; if(!c.includes('worktrees/'))fs.writeFileSync(p,c+(c.endsWith('\n')?'':'\n')+'worktrees/\n')"
  git add .gitignore
  git commit -m "chore: ignore worktrees"
  ```

**Step 2 — Commit specs (if not already committed):**
```
git add specs/
git status
git commit -m "add Phase 1 specs"
```
(Skip the commit if there is nothing to commit — that is not an error.)

**Step 3 — Create worktrees (names depend on phase):**

For **Phase 1**:
```
git worktree add worktrees/feature-a -b feature/release-management
git worktree add worktrees/feature-b -b feature/sprint-analytics
```

For **Phase 2**:
```
git worktree add worktrees/modernisation-a -b feature/modernisation-backend
git worktree add worktrees/modernisation-b -b feature/modernisation-frontend
```

**Step 4 — Copy shared context into each worktree:**

Use Node.js for the copy — it is always available on Windows, macOS, and Linux regardless of which shell Claude Code is using:

For Phase 1:
```
node -e "const fs=require('fs'); ['worktrees/feature-a','worktrees/feature-b'].forEach(d=>{fs.copyFileSync('CLAUDE.md',d+'/CLAUDE.md'); fs.cpSync('.claude',d+'/.claude',{recursive:true});})"
```

For Phase 2:
```
node -e "const fs=require('fs'); ['worktrees/modernisation-a','worktrees/modernisation-b'].forEach(d=>{fs.copyFileSync('CLAUDE.md',d+'/CLAUDE.md'); fs.cpSync('.claude',d+'/.claude',{recursive:true});})"
```

Note: `fs.cpSync` requires Node 16.7 or later. Run `node --version` to confirm. Node 18+ is a session prerequisite so this is always available.

**Step 5 — Install node_modules in each worktree:**

For Phase 1:
```
npm install --prefix worktrees/feature-a --silent
npm install --prefix worktrees/feature-b --silent
```

For Phase 2:
```
npm install --prefix worktrees/modernisation-a --silent
npm install --prefix worktrees/modernisation-b --silent
```

**Step 6 — Print launch instructions:**

For **Phase 1**, print exactly this block:

```
═══════════════════════════════════════════════════════════════
  PHASE 1 AGENTS READY — Open two terminal windows
═══════════════════════════════════════════════════════════════

TERMINAL 1 — Release Management + Backlog Enhancements (Agent A):
  cd worktrees/feature-a
  claude

  Paste Prompt 05 from HANDSON.md

TERMINAL 2 — Sprint Analytics (Agent B):
  cd worktrees/feature-b
  claude

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
  cd worktrees/modernisation-a
  claude

  Paste Prompt 13 from HANDSON.md

TERMINAL 2 — Frontend Rewrite (Agent B):
  cd worktrees/modernisation-b
  claude

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
