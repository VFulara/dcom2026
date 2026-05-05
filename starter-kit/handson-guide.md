# Hands-On Guide — Claude Code Session Assistant

> This file is referenced by CLAUDE.md to give Claude Code precise, tested instructions for guiding participants through the AI-Augmented Development session. Every item here reflects the current restructured starter kit (last validated 2026-05-04).

---

## Session State at a Glance

| What exists in the starter kit | What agents add |
|-------------------------------|-----------------|
| `specs/feature-enhancement/requirements.md` — pre-written | `specs/feature-enhancement/design.md` — generated in Step 1C |
| `ui/manifest.json` — all 4 routes pre-populated | `specs/feature-enhancement/todo.md` — generated in Step 1D |
| `ui/util/FilterHelper.js` — full filter implementation | `srv/release-service.cds/.js` — Agent A |
| `ui/util/Formatters.js` — priority/status formatters | `srv/analytics-service.cds/.js` — Agent B |
| `ui/view/Backlog.view.xml` — with search/filter bar | `ui/view/Releases.view.xml` — Agent A |
| `ui/controller/Backlog.controller.js` — inline editing | `ui/view/SprintAnalytics.view.xml` — Agent B |
| `ui/view/SprintBoard.view.xml` — with Create Sprint | `db/schema.cds` — Release entity added by Agent A |
| Seed data with proper UUIDs | |

---

## Pre-Session Checklist (Claude verifies on first message)

When the participant opens Claude Code in the planning-board directory, Claude should silently verify:

```bash
# 1. Check node version
node --version   # must be v18+

# 2. Check node_modules installed
ls node_modules/@sap/cds 2>/dev/null || echo "NEEDS_INSTALL"

# 3. Check git is initialised
ls .git 2>/dev/null || echo "NEEDS_GIT_INIT"

# 4. Check seed data has proper UUIDs
head -2 db/data/planning-Sprints.csv
```

If any check fails, fix it proactively before the participant notices.

---

## Setup Phase

### Starting the App

Preferred method — run the start script (kills port 4004 first):
```bash
./start-legacy.sh
```

Manual fallback:
```bash
npm install
npx cds watch
```

Expected output: `server listening on { url: 'http://localhost:4004' }` with Stories, Sprints entities visible.

### Git init (required before Step 1E)

If `.git` does not exist, run immediately:
```bash
git init && git add -A && git commit -m "initial starter kit"
```

Ensure `worktrees/` is in `.gitignore`:
```bash
grep -q "worktrees/" .gitignore || echo "worktrees/" >> .gitignore
git add .gitignore && git commit -m "chore: ignore worktrees" 2>/dev/null || true
```

---

## Phase 1 — Feature Enhancement

### Step 1B: Pre-Provided Requirements

`specs/feature-enhancement/requirements.md` is in the starter kit. Participants do NOT generate it.
Step 1B is: read it → optionally annotate → invoke `@lead-architect review specs/feature-enhancement/requirements.md`.

The architect is in **Spec Review mode** — it challenges Sprint→Release invariants and Feature C UX.
Participants must address challenges before proceeding. Budget ~5 min.

### Step 1C: Two-Agent Design Challenge

After design.md is generated, participants invoke two agents in parallel:
- `@lead-architect review specs/feature-enhancement/design.md`
- `@tech-evangelist review specs/feature-enhancement/design.md`

This is the **key pedagogical moment** for spec-driven development. Both agents challenge the Feature C filter UX approach and the Sprint→Release API design.

Expected challenges:
- `@tech-evangelist`: "Is a query syntax (JQL) discoverable for end users? Why not pure dropdowns?"
- `@lead-architect`: "Are Sprint→Release invariants stated? Domain events mandatory on archiveRelease and completeSprint?"

`@senior-app-developer` API contract review happens at Step 1F (optional), not here.

### No-Conflict Agent File Split (Current Reality)

The extend service architecture completely avoids merge conflicts:
- Agent A creates: `srv/release-service.cds`, `srv/release-service.js`, `ui/view/Releases.view.xml`, `ui/controller/Releases.controller.js`
- Agent A modifies: `db/schema.cds`, `ui/view/Backlog.view.xml`, `ui/controller/Backlog.controller.js`, `ui/i18n/i18n.properties`, `ui/util/FilterHelper.js`
- Agent B creates: `srv/sprint-actions.cds`, `srv/sprint-actions.js`, `srv/analytics-service.cds`, `srv/analytics-service.js`, `ui/view/SprintAnalytics.view.xml`, `ui/controller/SprintAnalytics.controller.js`
- **Neither agent modifies**: `srv/backlog-service.cds`, `srv/backlog-service.js`, `srv/sprint-service.cds`, `srv/sprint-service.js`, `ui/manifest.json`

Merge conflicts **should NOT occur**. If a participant sees one, an agent modified a file outside its ownership. The fix is always to keep both sides (additive changes).

### Step 1D: Commit + /clear Sequence

After writing `todo.md`:
```bash
git add specs/ && git commit -m "add Phase 1 specs"
```
Then `/clear` in Claude Code. The specs are on disk — agents read files, not chat history.

### Step 1E: Launching Parallel Agents

Run `/run-parallel-agents`. The command:
1. Detects Phase 1 (checks `specs/feature-enhancement/design.md`)
2. Creates `worktrees/feature-a` on branch `feature/release-management`
3. Creates `worktrees/feature-b` on branch `feature/sprint-analytics`
4. Copies CLAUDE.md and `.claude/` into each worktree
5. Runs `npm install` in each worktree

If participants skip the git commit step, instruct:
```bash
git -C worktrees/feature-a add -A && git -C worktrees/feature-a commit -m "feat: release management"
git -C worktrees/feature-b add -A && git -C worktrees/feature-b commit -m "feat: sprint analytics"
```

### Step 1F: Merge Commands (Correct Syntax)

After both agents commit — use branch names, not directory paths:
```bash
git merge feature/release-management
git merge feature/sprint-analytics
```

### Step 1F: Review Gate

**Required (core gate — run in parallel):**
- `@code-reviewer review all changed files` — checks SOLID/DRY/DDD compliance
- `@lead-architect review all changes` — final merge approval

**Optional (if time permits):**
- `@tech-evangelist review frontend` — i18n, AP-1, AP-2, AP-3
- `@senior-app-developer validate api contracts` — OData signatures, traversal directions

---

## Phase 2 — App Modernisation

Phase 2 is mandatory and creates a new `modern/` subdirectory alongside the legacy app. The legacy app keeps running at port 4004; the modern app runs at port 4005 (backend) and port 5173 (frontend). Both are accessible simultaneously for comparison.

### Phase 2: Launching Parallel Agents

Run `/run-parallel-agents` again. The command detects Phase 2 when `specs/modernisation/design.md` exists and the Phase 1 worktrees already exist. It creates:
- `worktrees/modernisation-a` on branch `feature/modernisation-backend`
- `worktrees/modernisation-b` on branch `feature/modernisation-frontend`

### Phase 2 Backend Migration (Agent A): CDS v9 Service Syntax

Agent A creates the `modern/` directory. The migration changes the handler wrapper for all 4 services (BacklogService, SprintService, ReleaseService, AnalyticsService):

**v6 (before — in srv/*.js):**
```js
module.exports = cds.service.impl(async function () {
  this.on('event', handler);
});
```

**v9 (after — in modern/srv/*.js):**
```js
module.exports = class BacklogService extends cds.ApplicationService {
  async init() {
    await super.init();
    this.on('event', handler);
  }
};
```

`await super.init()` is required as the first statement. Also change `cds.emit(...)` → `this.emit(...)`.

### Phase 2 Backend: SQLite Config

CDS v9 `modern/package.json` must use in-memory SQLite (not shorthand `"db": "sqlite"`):
```json
"cds": { "server": { "port": 4005 }, "requires": { "db": { "kind": "sqlite", "credentials": { "database": ":memory:" } } } }
```
The shorthand creates a file-based DB that persists stale schema across restarts.

### Phase 2 Frontend (Agent B): Create modern/ui/ — Do NOT Delete Legacy ui/

Agent B creates the `modern/ui/` React app. The legacy `ui/` directory must remain untouched.

**File plan for Agent B:**
- `modern/ui/package.json` — React 18, @ui5/webcomponents-react@2, Vite 5, react-router-dom@6, TypeScript 5
- `modern/ui/index.html` — Vite entry point
- `modern/ui/vite.config.ts` — proxy `/odata` → `http://localhost:4005` with `changeOrigin: true`
- `modern/ui/src/main.tsx` — ThemeProvider wrapping the app
- `modern/ui/src/App.tsx` — routes: `/` Backlog, `/board` SprintBoard, `/releases` Releases, `/analytics` SprintAnalytics
- `modern/ui/src/components/` — AppShell, Sidebar, PriorityBadge, StatusSelect
- `modern/ui/src/pages/` — BacklogPage, SprintBoardPage, ReleasesPage, SprintAnalyticsPage
- `modern/ui/src/utils/` — api.ts, filterHelper.ts, formatters.ts, constants.ts
- `modern/ui/src/index.css` — Liquid Glass CSS custom properties and glass surface classes

Without keeping legacy `ui/` intact, the legacy app at port 4004 breaks.

### Phase 2 Frontend: Critical Patterns That Prevent Rework

The following issues were discovered and fixed during the Phase 2 implementation review. Each took disproportionate time to debug. Pre-apply these patterns when generating the frontend — they are not obvious from the spec but are required for the implementation to be correct on the first attempt.

#### FE-1 Vite Proxy — Do NOT Use URLSearchParams for OData query params

```ts
// WRONG — URLSearchParams encodes '$' to '%24', CAP's OData router returns 404
const params = new URLSearchParams();
params.set('$filter', filter);
fetch(`/odata/v4/backlog/Stories?${params}`);

// CORRECT — append $filter= as a literal prefix, encode only the value
let url = `/odata/v4/backlog/Stories`;
if (filter) url += `?$filter=${encodeURIComponent(filter)}`;
fetch(url);
```

The same applies to `$expand`, `$orderby`, `$top`. Build the query string manually, never with URLSearchParams.

#### FE-2 OData UUID Key Quoting

CAP OData v4 requires single quotes around string/UUID key predicates. Without them, CAP returns 400.

```ts
// WRONG — unquoted key
fetch(`/odata/v4/backlog/Stories(${id})`, { method: 'PATCH', ... });

// CORRECT — single-quoted UUID
fetch(`/odata/v4/backlog/Stories('${id}')`, { method: 'PATCH', ... });
```

Apply to all `PATCH`, `DELETE`, and single-entity `GET` calls.

#### FE-3 $expand Required for Navigation Properties

OData v4 never auto-expands navigation properties. `story.sprint?.name` will always be `undefined` unless `$expand=sprint` is appended to the Stories request.

```ts
// WRONG — sprint name is always undefined
api.list('backlog', 'Stories');

// CORRECT — request expansion explicitly
api.list('backlog', 'Stories', filter, 'sprint');
// produces: /odata/v4/backlog/Stories?$filter=...&$expand=sprint
```

The `api.list()` helper signature must accept an optional `expand` parameter.

#### FE-4 useMemo for Filter State to Prevent Infinite useEffect Loops

When a filter string is computed inline (not in `useMemo`), it produces a new string reference on every render, causing the `useEffect` that depends on it to fire on every render — an infinite loop of OData fetches.

```ts
// WRONG — new string reference on every render → infinite fetch loop
const filter = toODataFilter(buildFilters(search, filterStatus, filterPriority, filterSprint));
useEffect(() => { api.list(..., filter); }, [filter]);

// CORRECT — only rebuilds when filter values actually change
const filter = useMemo(
  () => toODataFilter(buildFilters(search, filterStatus, filterPriority, filterSprint)),
  [search, filterStatus, filterPriority, filterSprint],
);
useEffect(() => { api.list(..., filter); }, [filter]);
```

Apply `useMemo` to all derived filter/query strings used as `useEffect` dependencies.

#### FE-5 OData Filter Construction — Always Use filterHelper, Never Template Literals

Inline template literals in filter strings are a security risk (OData injection) and bypass the central `filterHelper.ts` module.

```ts
// WRONG — template literal, injection surface, bypasses filterHelper
api.list('sprint', 'Stories', `sprint_ID eq '${selectedSprintId}'`);

// CORRECT — typed helper produces validated OData expression
const sprintFilter = useMemo(
  () => toODataFilter([{ field: 'sprint_ID', operator: 'eq', value: selectedSprintId }]),
  [selectedSprintId],
);
api.list('sprint', 'Stories', sprintFilter);
```

#### FE-6 DDD — Each Page Reads Only Its Own Bounded Context

Every page must fetch data from its own OData service path. Fetching from a different bounded context is a DDD violation even if the entity exists there.

| Page | Correct service | Common mistake |
|------|----------------|---------------|
| BacklogPage | `api.list('backlog', ...)` | — |
| SprintBoardPage | `api.list('sprint', ...)` | — |
| ReleasesPage | `api.list('release', ...)` | — |
| SprintAnalyticsPage | `api.list('analytics', ...)` | `api.list('sprint', 'Sprints')` ← violation |

The analytics service exposes `@readonly Sprints` and `@readonly Stories` — use those, not SprintService.

#### FE-7 @ui5/webcomponents-react v2 Dialog API

The v2 Dialog API differs from v1 in two ways that break at runtime if the v1 pattern is used:

```tsx
// WRONG (v1 patterns)
<Dialog
  aria-labelledby="dialog-title"      // NOT forwarded through shadow DOM
  onClose={() => setOpen(false)}       // fires before animation completes, causes flicker
>

// CORRECT (v2 patterns)
<Dialog
  accessibleNameRef="dialog-title"    // maps to WC accessible-name-ref attribute
  // @ts-expect-error onAfterClose is the correct v2 after-animation event (spec §3.8); types lag the runtime
  onAfterClose={() => setOpen(false)} // fires after close animation completes
>
  <div slot="header" id="dialog-title">Title</div>
```

The `// @ts-expect-error` is intentional — `@ui5/webcomponents-react` v2.21.3 types expose `onClose` but the correct runtime event is `onAfterClose`. The comment must document this so reviewers do not remove it.

#### FE-8 storiesByRelease Response Unwrap

`storiesByRelease` is an OData bound function returning `array of Stories`. CAP wraps collection function responses as `{ "value": [...] }`. The incorrect unwrap pattern discards all results.

```ts
// WRONG — may evaluate to a single object, not the array
const stories = (result as any).value ?? (result as any);

// CORRECT — destructure with default
const { value: stories = [] } = result as { value: Story[] };
```

#### FE-9 React CSSProperties Type — No React Namespace Without Import

With `"jsx": "react-jsx"` (Vite default), the `React` namespace is not available without an explicit import. Type annotations must use the named import.

```ts
// WRONG — React is not in scope with automatic JSX transform
const sidebarStyle: React.CSSProperties = { ... };

// CORRECT
import type { CSSProperties } from 'react';
const sidebarStyle: CSSProperties = { ... };
```

#### FE-10 Constants Centralisation — STATUS_OPTIONS and PRIORITY_OPTIONS

Status and priority arrays must be defined once in `src/utils/constants.ts` and imported everywhere. Defining them inline per component is an AP-4 DRY violation.

```ts
// src/utils/constants.ts — single source of truth
export const STATUS_OPTIONS = ['New', 'In Progress', 'In Review', 'Blocked', 'Completed'] as const;
export const PRIORITY_OPTIONS = ['Critical', 'High', 'Medium', 'Low'] as const;
```

The filter dropdowns render `<option value="">All Statuses</option>` separately — `STATUS_OPTIONS` must NOT contain an empty string.

#### FE-11 Accessibility — Label/Control Association in All Dialog Forms

Every `<label>` in a dialog form must have a `htmlFor` attribute matching the control's `id`. Missing associations cause screen readers to announce unlabelled fields. This applies to ALL form fields, not just the title field.

```tsx
// WRONG — orphaned label
<label style={...}>Version *</label>
<input className="form-input" value={newVersion} onChange={...} />

// CORRECT
<label htmlFor="new-release-version" style={...}>Version *</label>
<input id="new-release-version" className="form-input" value={newVersion} onChange={...} />
```

Apply `htmlFor`/`id` pairs to every `<label>`+control pair across all dialog forms: BacklogPage (Title, Priority, Points, Assignee, Sprint), SprintBoardPage (Move to sprint), ReleasesPage (Version, Target Date).

#### FE-12 Accessibility — No Interactive Elements Nested Inside role="button"

A native `<button>` inside a `role="button"` div is a WCAG 4.1.2 violation. Screen readers expose conflicting roles and keyboard focus is broken.

```tsx
// WRONG — native <button> nested inside role="button" div
<div role="button" onClick={toggleExpand}>
  ...
  <button onClick={openArchive}>Archive</button>  // violation
</div>

// CORRECT — plain div row, both interactive affordances are sibling native buttons
<div style={{ display: 'flex', alignItems: 'center' }}>
  ...
  <button aria-label={`Archive release ${release.version}`} onClick={openArchive}>Archive</button>
  <button aria-expanded={isExpanded} aria-controls={panelId}
          aria-label={`${isExpanded ? 'Collapse' : 'Expand'} release ${release.version}`}
          onClick={toggleExpand}>▼</button>
</div>
```

#### FE-13 Accessibility — focus-visible Outlines Required

`.btn`, `.status-select`, and `.form-input` must all have a `:focus-visible` outline meeting WCAG 1.4.11 Non-text Contrast 3:1. `outline: none` without a compensating high-contrast indicator is a keyboard accessibility failure.

```css
.form-input { outline: none; }                               /* suppress default ring */
.form-input:focus-visible    { outline: 2px solid var(--accent); outline-offset: 2px; }
.btn:focus-visible           { outline: 2px solid var(--accent); outline-offset: 2px; }
.status-select:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
```

### Phase 2 Frontend: node_modules Must Be Gitignored

`modern/ui/node_modules/` must not be staged. Ensure `modern/ui/.gitignore` exists before running `npm install`:

```
node_modules/
dist/
```

If `node_modules` is accidentally staged, unstage it before committing:
```bash
git reset HEAD modern/ui/node_modules/
echo "node_modules/" >> modern/ui/.gitignore
echo "dist/" >> modern/ui/.gitignore
git add modern/ui/.gitignore
```

### Phase 2 Verify: Two Apps Running Simultaneously

Use the start script (leave legacy running in another terminal):
```bash
./start-modern.sh   # starts CDS v9 at port 4005 + Vite at port 5173
```

Or manually in two terminals:
- Terminal 1: `cd modern && npx cds watch` (backend at localhost:4005)
- Terminal 2: `cd modern/ui && npm run dev` (frontend at localhost:5173)

Access modern app at `localhost:5173`. The Vite proxy forwards `/odata/*` to port 4005.
Access legacy app at `localhost:4004` for side-by-side comparison.

---

## Quick Recovery Procedures

### "npm install failed with 404"
```bash
# Most likely culprit: stale package reference
# Check package.json — remove any @sap/cds-test entry
npm install
```

### "cds watch says port in use"
```bash
./start-legacy.sh   # kills port 4004 automatically
# or manually:
lsof -i :4004 -t | xargs kill -9 && npx cds watch
```

### "git merge says Already up to date"
The agent didn't commit. Go to the worktree and commit:
```bash
git -C worktrees/feature-a add -A && git -C worktrees/feature-a commit -m "feat: release management"
git merge feature/release-management
```

### "git merge has CONFLICT"
Each agent creates distinct files — this should not happen. If it does, an agent modified a shared file. Always keep both sides (additive changes):
```bash
# Edit the conflicted file: remove <<<, ===, >>> markers, keep ALL changes
git add <conflicted-file>
git commit -m "merge: resolved additive conflict in <file>"
```

### "totalPoints/sprintVelocity returns 400 with UUID error"
Create a new sprint to get a real UUID, then use that ID:
```bash
curl -s -X POST http://localhost:4004/odata/v4/sprint/Sprints \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Sprint","status":"Active"}'
```

### "Releases page loads but is blank — no buttons, no toolbar visible"

**Root cause — two bugs, both required to fix:**

**Bug 1 — `<Dialog>` at wrong level in view XML.** The `<Dialog>` was placed as a direct sibling of `<Page>` at the `<mvc:View>` root. OpenUI5 `View` has a single default content aggregation — two controls competing for it means `<Page>` is not rendered. Fix: move `<Dialog>` inside `<Page><dependents>`.

**Bug 2 — Invalid OData `$expand` with inline `$count`, and spurious `$top`.** The table binding used `$expand: 'Sprints($count=true)'`, but CDS v6 does not support inline `$count` inside `$expand`. A `$top` parameter was also present — the UI5 OData v4 model with `autoExpandSelect: true` rejects `$top` in list binding parameters with `"System query option $top is not supported"`. Additionally, `Releases` had no back-association to `Sprints` in the service, so even `$expand=Sprints` would have returned a 400.

**Fixes applied:**

1. Moved `<Dialog>` inside `<Page><dependents>` in `ui/view/Releases.view.xml`
2. Added `Sprints` back-association to the `Releases` projection in `srv/release-service.cds`:
   ```cds
   entity Releases as projection on planning.Releases {
     *,
     Sprints : Association to many Sprints on Sprints.release = $self
   };
   ```
3. Changed table binding from `$expand: 'Sprints($count=true)', $top: 500` → `$expand: 'Sprints'` in the view
4. Changed sprint count cell from `{release>Sprints/$count}` → `formatter: '.formatter.arrayLength'` 
5. Added `arrayLength` formatter to `ui/util/Formatters.js`

No restart needed after view/JS changes — save and refresh. CDS service restart is needed after `.cds` file changes.

### "Sprint Analytics page is not reachable from the UI"

**Root cause:** No navigation button to the `sprintAnalytics` route was wired up in any view. The page existed and was routable via direct URL (`http://localhost:4004/#/analytics`) but was unreachable through normal app flow. Fix: added a "Sprint Analytics" button to both the Backlog header (`ui/view/Backlog.view.xml`) and SprintBoard header (`ui/view/SprintBoard.view.xml`), with corresponding `onNavToAnalytics` handlers in both controllers.

### "Assigning a story to a Completed sprint shows no error — change silently fails"

**Root cause:** `oContext.setProperty()` fires a PATCH and returns a Promise, but `onStatusChange` and `onSprintChange` in `Backlog.controller.js` discarded it without `.catch()`. Server-side validation errors (e.g. "Cannot assign a story to a Completed sprint") were swallowed silently. Fix: chain `.catch()` on both handlers and call `oContext.refresh()` to revert the optimistic UI update.

No restart needed — save and reproduce.

### "Creating a release fails with IllegalArgumentError: Invalid value for targetDate"

**Root cause:** `DatePicker.getValue()` returns the date in the user's locale format (e.g. `6/30/26`), but `Edm.Date` requires `YYYY-MM-DD`. Fix: use `getDateValue()` to get a JS `Date` object, then format it manually.

```js
// WRONG
var sTargetDate = this.byId("releaseTargetDate").getValue(); // "6/30/26"

// CORRECT
var oDate = this.byId("releaseTargetDate").getDateValue();   // JS Date object
var sTargetDate = oDate.getFullYear() + "-" +
  String(oDate.getMonth() + 1).padStart(2, "0") + "-" +
  String(oDate.getDate()).padStart(2, "0");                  // "2026-06-30"
```

Also reset with `setDateValue(null)` instead of `setValue("")` on cancel.



**Not an error — ignore.** OpenUI5 always requests `Component-preload.js` as a load-time optimisation. When it gets a 404, it silently falls back to loading individual files. The MIME type warning is a side-effect of the 404 (CAP returns an HTML error page). The app is fully functional. No fix required; this is expected in any dev setup without a UI5 build step.

### "App shows blank page at localhost:4004"
Check `ui/index.html` CDN URL — must be `1.120` not `1.120.x`:
```html
<!-- Correct -->
src="https://sdk.openui5.org/1.120/resources/sap-ui-core.js"
```
No restart needed — save and refresh.

### "OData proxy not working on localhost:5173"
Check `modern/ui/vite.config.ts` has:
```ts
server: { proxy: { '/odata': { target: 'http://localhost:4005', changeOrigin: true } } }
```
Also ensure modern CDS backend is running on localhost:4005 (`cd modern && npx cds watch`).

### "story.sprint?.name is always undefined in BacklogPage"
The Stories fetch is missing `$expand=sprint`. Fix in `api.list` call:
```ts
api.list('backlog', 'Stories', filter || undefined, 'sprint')
```
The `api.list()` helper must accept a 4th `expand` argument that appends `&$expand=sprint` to the URL.

### "BacklogPage keeps refetching in an infinite loop"
The filter string is being rebuilt on every render. Wrap it in `useMemo`:
```ts
const filter = useMemo(
  () => toODataFilter(buildFilters(search, filterStatus, filterPriority, filterSprint)),
  [search, filterStatus, filterPriority, filterSprint],
);
```

### "PATCH / DELETE returns 400: Expected quoted string literal"
The UUID key is not single-quoted. Fix the `api.patch()` call:
```ts
// WRONG: Entity(${id})
// CORRECT: Entity('${id}')
fetch(`/odata/v4/${service}/${entity}('${id}')`, { method: 'PATCH', ... })
```

### "SprintAnalyticsPage shows no sprints / fetches from wrong service"
`api.list('sprint', 'Sprints')` is a DDD cross-context violation. Change to:
```ts
api.list('analytics', 'Sprints')
```
`AnalyticsService` exposes `@readonly Sprints` — use that, not SprintService.

### "TypeScript error: React.CSSProperties is not defined"
With Vite's automatic JSX transform (`"jsx": "react-jsx"`), the `React` namespace is not in scope. Use named import:
```ts
import type { CSSProperties } from 'react';
const myStyle: CSSProperties = { ... };
```

### "Dialog title not announced by screen reader"
`aria-labelledby` is not forwarded through the Shadow DOM of `<ui5-dialog>`. Use `accessibleNameRef` instead:
```tsx
// WRONG
<Dialog aria-labelledby="my-title">
// CORRECT
<Dialog accessibleNameRef="my-title">
  <div slot="header" id="my-title">...</div>
```

### "Dialog flickers / state resets on close"
`onClose` fires mid-animation. Use `onAfterClose` (fires after animation completes):
```tsx
// @ts-expect-error onAfterClose is the correct v2 after-animation event (spec §3.8); types lag the runtime
onAfterClose={() => setOpen(false)}
```
The `@ts-expect-error` is intentional — v2 runtime supports `onAfterClose` but the type definitions lag.

---

## Timing Guidance for Claude

Use these estimates when helping participants manage time:

| Step | Target | If running late |
|------|--------|-----------------|
| Setup | 5 min | Trust cds watch output; skip manual verification |
| 1A Explore (optional) | 0–2 min | Skip if service structure is clear from CLAUDE.md |
| 1B Review Requirements | 5 min | Read quickly; skip annotations; go straight to @lead-architect |
| 1C Design | 8 min | Allow 2 agents to challenge — key learning moment |
| 1D Task list + /clear | 2 min | Copy from design.md file list |
| 1E Agents (waiting) | 8–12 min | Read specs while agents run |
| 1F Review (core gate) | 8 min | @code-reviewer + @lead-architect in parallel |
| 1G Verify | 5 min | Test archiveRelease and sprintVelocity only |
| Phase 2 | 20 min | Required — specs 6 min, agents 8 min, verify 6 min |

**Total target: ~55–60 min.** Phase 1 demonstrates spec-driven development; Phase 2 demonstrates stack modernisation.

---

## Notes for Session Facilitator

- **Feature C is pre-built** in the starter kit (search bar, inline editing, sprint assignment). HANDSON.md correctly describes this. The design exercise in Step 1C is pedagogical — participants evaluate the JQL vs. dropdown trade-off even though the starter already chose it. Agent A will extend/adjust the existing implementation.
- **No merge conflicts expected** — the bounded context architecture gives each agent new files. If a participant sees one, an agent violated file ownership. The fix is always to keep both additions.
- **Step 1C is the design debate** — both agents challenge the spec. Budget the 8 min generously; this is the most educational step.
- **Seed data uses proper UUIDs** — `sprintVelocity(sprintId)` and `totalPoints(sprintId)` work directly with seed sprint IDs.
- **Phase 2 is mandatory** — it creates `modern/` alongside the legacy app. Both versions run simultaneously so participants can compare the OpenUI5 and React UIs side by side.
- **Pre-run `npm install`** in the starter-kit before distributing — saves 2–3 min per participant.
