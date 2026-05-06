# planning-board — Project Instructions for Claude Code

## Session Guide
Read `handson-guide.md` in this directory for step-by-step facilitation guidance, all known issues and their fixes, recovery procedures, and timing targets for the hands-on session.

**Before generating any Phase 2 React frontend code**, read the section "Phase 2 Frontend: Critical Patterns That Prevent Rework" in `handson-guide.md`. It documents 17 concrete mistakes (FE-1 through FE-17) that were discovered during implementation review and each caused rework. Applying them upfront makes the first implementation attempt reviewable without a multi-pass fix cycle. Key patterns:
- FE-1: Never use URLSearchParams for OData query params (encodes `$` → `%24`)
- FE-2: Single-quote UUID keys in all PATCH/DELETE URLs: `Entity('${id}')`
- FE-3: Always pass `$expand=sprint` when reading Stories for the Backlog view
- FE-4: Wrap filter computation in `useMemo` to prevent infinite `useEffect` loops
- FE-5: Use `filterHelper.ts` for all OData filter expressions — no template literals
- FE-6: Each page fetches only from its own bounded context service
- FE-7: Use `accessibleNameRef` + `onAfterClose` (not `aria-labelledby` + `onClose`) on Dialogs
- FE-8: Unwrap `storiesByRelease` as `const { value: stories = [] } = result`
- FE-9: Import `type { CSSProperties }` from 'react' — `React.CSSProperties` not available with automatic JSX transform
- FE-10: Define STATUS_OPTIONS and PRIORITY_OPTIONS once in `constants.ts`, no empty-string sentinels
- FE-11: Every dialog `<label>` must have `htmlFor` matching the control's `id`
- FE-12: Never nest a `<button>` inside a `role="button"` element (WCAG 4.1.2)
- FE-13: Add `:focus-visible` outline to `.btn`, `.form-input`, `.status-select`
- FE-14: Inline sprint assignment in the Backlog row requires a `SprintSelect` component — rendering `story.sprint?.name` as static text silently drops the legacy edit capability
- FE-15: Inline assignee editing requires an `AssigneeInput` component — commit on blur/Enter, revert on Escape, guard with `committed` ref to avoid PATCH on unchanged value
- FE-16: Sprint → Release assignment on the Releases page reads sprints from `release` service (read projection) but PATCHes via `sprint` service (aggregate owner) — using `release` service for the PATCH is a DDD cross-context write violation
- FE-17: Analytics velocity chart bars overflow container when label is static in flex column — use `position:absolute; bottom: barH+4` for value labels, separate sprint-name row outside the chart height, and give Planned/zero sprints a 4px token bar not the same height as active sprints

## What This App Does
A lightweight Agile planning board for SAP development teams. Lets you create and manage backlog stories with priority, estimate, status, and assignee. Organise stories into time-boxed sprints. Track sprint progress and backlog health through an OData v4 service and a classic OpenUI5 1.120 frontend.

The starter app has Story and Sprint management working end-to-end. Three features are intentionally missing for the hands-on session: **Release Management**, **Sprint Analytics**, and **Backlog Enhancements** (search/filter/inline editing). Requirements are pre-provided in `specs/feature-enhancement/requirements.md`.

## Architecture Decisions

### Bounded Context Service Split — Non-Negotiable
This app uses **one service per bounded context**. A single monolithic service handling all entities violates SRP and DDD. There are currently two services; Phase 1 adds two more.

| Service | OData Path | Aggregate Owned | What It Must NOT Do |
|---------|-----------|----------------|---------------------|
| `BacklogService` | `/odata/v4/backlog/` | `Story` | Mutate Sprints |
| `SprintService` | `/odata/v4/sprint/` | `Sprint` | Mutate Stories |
| `ReleaseService` _(Phase 1 Agent A)_ | `/odata/v4/release/` | `Release` | Mutate Stories or Sprints |
| `AnalyticsService` _(Phase 1 Agent B)_ | `/odata/v4/analytics/` | _(none — read-only)_ | Mutate any entity |

**Cross-context reads are allowed via `@readonly` projections.** For example, BacklogService exposes `@readonly Sprints` so the backlog sprint dropdown works without coupling to SprintService. This is intentional and documented.

**Cross-context writes are forbidden.** If a handler in ReleaseService calls `UPDATE Sprints`, that is a DDD violation. Sprint mutations belong to SprintService (or extensions of SprintService added via `extend service SprintService`).

### Service File Structure
- `srv/backlog-service.cds` + `srv/backlog-service.js` → BacklogService
- `srv/sprint-service.cds` + `srv/sprint-service.js` → SprintService
- New Phase 1 services are standalone (NOT extend service) unless adding actions to an existing bounded context
- `manifest.json` pre-declares all 4 data sources — agents do NOT touch manifest.json

### OData Model Binding (UI Layer)
Each OpenUI5 view binds to its own bounded context model:
- Backlog view → default model `""` = BacklogService
- Sprint Board view → named model `"sprint"` = SprintService
- Releases view → named model `"release"` = ReleaseService _(Phase 1)_
- Sprint Analytics view → named model `"analytics"` = AnalyticsService _(Phase 1)_

Controllers use `this.getOwnerComponent().getModel("sprint")` (not the default model) for cross-context reference reads. This is not a violation — it is explicit cross-context reference data access.

### Other Decisions
- SAP CAP-JS (v6) handles all data persistence — no direct DB access from frontend
- Frontend: OpenUI5 1.120 XMLViews served by CAP static serving (`ui/` → `app/`)
- No XSUAA for local dev — auth is disabled for the hands-on session
- Service handlers in `srv/*.js` — one file per service, using `cds.service.impl`
- UI components in `ui/view/` + `ui/controller/` — one XML view + controller per screen

### Current Data Model
- **Story**: title, description, assignee (free text), status (New/In Progress/In Review/Blocked/Completed), priority (Critical/High/Medium/Low, default Medium), storyPoints (Integer), estimateHours (Decimal), sprint (FK to Sprint)
- **Sprint**: name, startDate, endDate, status (Planned/Active/Completed)

### Features to Add (Phase 1 — Hands-On Session)

**Feature A — Release Management (Agent A → new `ReleaseService` bounded context):**
- **Release** entity: version (String), targetDate (Date), archived (Boolean default false)
- **Sprint** gets a `release` FK to Release (a sprint belongs to at most one release)
- `archiveRelease` action: set archived = true, return updated Release — emit `ReleaseArchived` event
- `storiesByRelease` function: return all stories whose sprint belongs to the given release
- Releases UI view (XMLView + controller) bound to `release` model (`/odata/v4/release/`)
- This is a **new standalone service** — does NOT extend BacklogService or SprintService

**Feature B — Sprint Analytics (Agent B → `completeSprint` extends SprintService + new `AnalyticsService`):**
- `completeSprint` action: mark sprint Completed, move unfinished stories to nextSprint — emit `SprintCompleted` event
  - This is a Sprint aggregate operation → extends `SprintService` in new files (`srv/sprint-actions.cds/.js`)
  - Uses `extend service SprintService` because it mutates the Sprint aggregate
- `sprintVelocity` function: return total storyPoints of Completed stories in a sprint
  - This is a read-only analytics query → new standalone `AnalyticsService` (`srv/analytics-service.cds/.js`)
- Sprint Analytics UI view bound to `analytics` model (`/odata/v4/analytics/`)

**Feature C — Backlog Enhancements (pre-built in starter kit — review, do not re-implement):**
- Inline status change, inline sprint assignment, sprint selector in Add Story dialog
- Text search + Status/Priority/Sprint dropdown filters with Clear Filters button
- All filter logic in `ui/util/FilterHelper.js` (SRP, AP-3). Agent A may extend it if the design spec requires changes.

### Parallel Agent File Ownership (Critical — prevents merge conflicts)

Phase 1 uses two parallel agents. Each agent creates ONLY new files or modifies ONLY its designated files.
`manifest.json` is pre-populated with all 4 routes and all 4 data sources — **neither agent modifies manifest.json**.

**Agent A (Release Management) owns:**
- `db/schema.cds` — add Release entity and Sprint.release FK
- `srv/release-service.cds` — NEW standalone ReleaseService (`service ReleaseService @(path: '/odata/v4/release')`)
- `srv/release-service.js` — NEW file, `cds.service.impl` for ReleaseService
- `ui/view/Releases.view.xml` — NEW file, bound to `release` model
- `ui/controller/Releases.controller.js` — NEW file, uses `getOwnerComponent().getModel("release")`
- `ui/util/FilterHelper.js` — modify only if design spec requires filter logic changes
- `ui/i18n/i18n.properties` — modify (add release-related i18n keys)

**Agent B (Sprint Analytics + Sprint Completion) owns:**
- `srv/sprint-actions.cds` — NEW file, `extend service SprintService` to add completeSprint
- `srv/sprint-actions.js` — NEW file, `cds.service.impl('SprintService', ...)` for completeSprint
- `srv/analytics-service.cds` — NEW standalone AnalyticsService (`service AnalyticsService @(path: '/odata/v4/analytics')`)
- `srv/analytics-service.js` — NEW file, `cds.service.impl` for AnalyticsService
- `ui/view/SprintAnalytics.view.xml` — NEW file, bound to `analytics` model
- `ui/controller/SprintAnalytics.controller.js` — NEW file, uses `getOwnerComponent().getModel("analytics")`
- `ui/i18n/i18n.properties` — modify (add analytics-related i18n keys)

**Neither agent modifies:** `srv/backlog-service.cds`, `srv/backlog-service.js`, `srv/sprint-service.cds`, `srv/sprint-service.js`, `ui/manifest.json`

### Extend Service Pattern (CDS v6) — Only for Adding to an Existing Bounded Context

Use `extend service` ONLY when adding an action/function that belongs to an existing bounded context's aggregate. For entirely new aggregates, create a new standalone service.

**Example: Agent B adding completeSprint to SprintService (correct use):**
```cds
// srv/sprint-actions.cds
using { SprintService } from './sprint-service';
extend service SprintService with {
  action completeSprint(sprintId: UUID, nextSprintId: UUID) returns {};
};
```
```js
// srv/sprint-actions.js
const cds = require('@sap/cds');
module.exports = cds.service.impl('SprintService', async function() {
  this.on('completeSprint', async (req) => { ... });
});
```

**Example: Agent A creating ReleaseService (correct — new standalone bounded context):**
```cds
// srv/release-service.cds
using { planning } from '../db/schema';
service ReleaseService @(path: '/odata/v4/release') {
  entity Releases as projection on planning.Releases;
  action archiveRelease(releaseId: UUID) returns Releases;
  function storiesByRelease(releaseId: UUID) returns array of Stories;
};
```

**WRONG — do NOT do this:**
```cds
// WRONG: creating one god service that owns everything
service PlanningService {
  entity Stories ...; entity Sprints ...; entity Releases ...;  // violation of SRP + DDD
}
```

### Phase 2 — Modernisation Target
Phase 2 creates a new `modern/` subdirectory. The legacy app remains fully functional at port 4004.
The modern app runs alongside it: CDS v9 backend at port 4005, React/Vite frontend at port 5173.
Both versions are accessible simultaneously for comparison.

Reference wireframes are in `modernisation/` — open them in a browser before writing Phase 2 code.

## Code Patterns to Follow
- CDS entities use UUID keys with `@cds.on.insert: $uuid`
- Service handlers use `cds.service.impl` — not class extension syntax (that is CDS v9 only)
- Input validation at service boundaries — never trust user input in handlers
- Use `cds.log('<service-name>')` for all logging in `srv/` — never `console.log()`
- Tests in `test/` using `jest` — integration tests only, no DB mocks
- OpenUI5: use `this.byId()` and `this.getOwnerComponent().getModel("modelName")` for named models
- All API calls in OpenUI5 controllers go through the OData v4 model binding — no raw fetch()

---

## SOLID Principles — Applied to This Project

### Single Responsibility
- Each CDS entity captures one domain concept. Do not add fields from another aggregate.
- Each service handler function handles one action. Complex logic splits into named helper functions.
- Each OpenUI5 controller method handles one user action. A method that fetches AND renders AND validates is three methods.

### Open / Closed
- Extend service behaviour by adding new actions or functions — never by modifying existing handlers.
- New UI views are new XMLView + controller pairs. Do not modify existing controllers to support new views via flags.

### Liskov Substitution
- All CDS projections honour the full contract of the base entity. No projection may hide a required field.
- OpenUI5 controllers that handle the same OData entity must support the same binding paths.

### Interface Segregation
- Do not expose service operations that a consumer does not need. Separate read-heavy functions from write-heavy actions.
- Controller event handlers receive only the event object — no "pass everything" context objects.

### Dependency Inversion
- Service handlers depend on CDS abstractions (`this.entities`, `SELECT`, `INSERT`) — never on sqlite3 directly.
- OpenUI5 controllers depend on the OData model binding — never on hardcoded endpoint URLs.

---

## DRY — Don't Repeat Yourself

- Status and priority constant lists are defined once (in CLAUDE.md as the reference) — never redefined per handler.
- Input validation logic shared across similar actions is extracted into a named helper — not copy-pasted.
- If a CDS fragment (e.g. audit fields) appears on more than one entity, extract it as an `aspect`.
- OpenUI5: shared formatting functions (status → state, priority → badge text) go in a helper module — not in every controller.

---

## DDD — Domain-Driven Design

### Bounded Context
The `planning` namespace is the shared domain model (entities in `db/`). Each service represents one bounded context with its own OData path. This is the fundamental SRP application at the service layer.

**Bounded Contexts:**
- `BacklogService` (`/odata/v4/backlog/`) — Story aggregate. The only context that writes Stories.
- `SprintService` (`/odata/v4/sprint/`) — Sprint aggregate. The only context that writes Sprints.
- `ReleaseService` (`/odata/v4/release/`) — Release aggregate. Added in Phase 1 Agent A.
- `AnalyticsService` (`/odata/v4/analytics/`) — Read-only reporting. Added in Phase 1 Agent B.

**Cross-context reads** are fine via `@readonly` projections. **Cross-context writes are forbidden.**

No cross-context imports. External systems integrate via service APIs, not entity references.

### Aggregates
- **Story** is an aggregate. Its lifecycle (New → Completed) is managed entirely through PlanningService.
- **Sprint** is an aggregate. Status transitions (Planned → Active → Completed) are enforced in service handlers. A Sprint optionally belongs to one Release via `sprint.release_ID`.
- **Release** is an aggregate. Archived flag is the only allowed state transition post-creation. A Release is composed of zero or more Sprints.

Cross-aggregate navigation (story.sprint, sprint.release) is by foreign key only — never by deep join across aggregate roots in a single query from the frontend.

### Domain Events
Significant state transitions emit domain events via `cds.emit()`:
- `SprintCompleted` — when completeSprint action fires
- `ReleaseArchived` — when archiveRelease action fires
- `StoryStatusChanged` — when story status transitions to Completed

Events carry only IDs and the new state — no PII, no request body data.

### Invariants
- A Story can belong to at most one Sprint at a time.
- A Sprint can belong to at most one Release at a time.
- A Sprint cannot be Completed if it has no Stories.
- A Release cannot be un-archived once archived.
- `storiesByRelease` traverses via Sprint (Sprint.release_ID) — Story does NOT store release_ID directly.
- Hard deletes are never performed on any entity.

### Domain Events — Mandatory, Not Optional
Every significant state transition **must** emit a domain event via `cds.emit()`. This is not a nice-to-have.
Without events, downstream consumers (analytics, audit, notifications) must poll or couple directly to the aggregate.

```js
// WRONG — silent state change, no event
this.after('UPDATE', 'Stories', async (result, req) => {
  // nothing emitted — analytics has no way to react
});

// CORRECT — emit after every status transition to Completed (BacklogService)
this.after('UPDATE', 'Stories', async (result, req) => {
  if (req.data.status === 'Completed') {
    await cds.emit('StoryStatusChanged', { storyId: result.ID, newStatus: 'Completed' });
  }
});
```

Events carry only IDs and new state — no request body data, no PII.

---

## Anti-Patterns — What Not to Do

These are the most common SOLID/DDD violations in this codebase. Every agent must check their output against this list before declaring done.

### AP-1 Inline Ternary Chains in View Bindings (violates DRY + DIP)

Views should depend on a named formatter abstraction, not embed logic directly.

```xml
<!-- WRONG — logic duplicated across every view that shows priority -->
<ObjectStatus state="{= ${priority} === 'Critical' ? 'Error' :
  (${priority} === 'High' ? 'Warning' :
  (${priority} === 'Medium' ? 'Information' : 'Success'))}"/>

<!-- CORRECT — depends on shared Formatters module -->
<ObjectStatus state="{path: 'priority', formatter: '.formatter.priorityToState'}"/>
```

Controller must expose `formatter: Formatters` from `ui/util/Formatters.js`. Never repeat the mapping table.

### AP-2 Hardcoded Strings in Controllers (violates DRY + i18n)

All user-visible strings go in `i18n/i18n.properties`. Controllers use `this._t(key)`.

```js
// WRONG — untranslatable, duplicated across files
MessageBox.error("Sprint name is required.");
MessageToast.show("Sprint created successfully.");

// CORRECT
MessageBox.error(this._t("errorSprintNameRequired"));
MessageToast.show(this._t("sprintCreated"));
```

### AP-3 Filter Logic in the Controller (violates SRP)

A controller that parses query strings AND applies filters AND handles navigation has three responsibilities.

```js
// WRONG — controller owns JQL parsing + filter building + UI state
onSearch: function() {
  var sQuery = this.byId("searchField").getValue();
  var aFilters = [];
  var re = /(\w+):("([^"]+)"|(\S+))/g, m;
  while ((m = re.exec(sQuery)) !== null) {
    // ... parsing logic ...
  }
  this.byId("storiesTable").getBinding("items").filter(aFilters);
}

// CORRECT — delegate to FilterHelper; controller only reads UI state
onSearch: function() {
  this._applyFilters();
},
_applyFilters: function() {
  var oCombined = FilterHelper.buildFilters(
    this.byId("searchField").getValue(),
    this.byId("filterStatus").getSelectedKey(),
    this.byId("filterPriority").getSelectedKey(),
    this.byId("filterSprint").getSelectedKey()
  );
  this.byId("storiesTable").getBinding("items").filter(oCombined);
}
```

`FilterHelper.js` is the single place to add new filterable fields (OCP via `FIELD_FILTER_MAP`).

### AP-4 Enum Values Duplicated Across Files (violates DRY)

Status and priority values are defined once as CDS `type` in `db/schema.cds`. Do not redefine them in service handlers, controller constants, or XML item keys.

```cds
// CORRECT — single source of truth in schema.cds
type StoryStatus : String(20) enum { New; InProgress = 'In Progress'; Blocked; Completed; }
type Priority    : String(20) enum { Critical; High; Medium; Low; }
```

```js
// WRONG — re-declaring the same set in a handler
const VALID_STATUSES = ['New', 'In Progress', 'Blocked', 'Completed']; // don't do this
```

### AP-5 Audit Fields Copy-Pasted Across Entities (violates DRY)

Use the `Auditable` CDS aspect defined in `db/schema.cds`. Do not add `createdAt`/`modifiedAt` fields inline.

```cds
// WRONG — duplicated on every entity
entity Stories { ...; createdAt : Timestamp @cds.on.insert: $now; }
entity Sprints  { ...; createdAt : Timestamp @cds.on.insert: $now; }

// CORRECT — compose the aspect once
entity Stories : Auditable { ... }
entity Sprints : Auditable { ... }
```

### AP-6 Invariants Enforced Inside a Single Handler (violates OCP + SRP)

Adding a second validation rule to a handler that already contains one produces a function with two responsibilities. Extract each invariant as a named pure function.

```js
// WRONG — one function, two invariants, impossible to test independently
this.before('CREATE', 'Stories', async (req) => {
  if (!req.data.title?.trim()) return req.error(400, 'title required');
  if (req.data.storyPoints < 0) return req.error(400, 'points negative');
});

// CORRECT — one function per invariant; add new ones by adding a line
this.before('CREATE', 'Stories', async (req) => {
  _requireTitle(req);
  _requireNonNegativePoints(req);
  await _requireAssignableSprint(req, this);
});
function _requireTitle(req) { ... }           // pure, testable
function _requireNonNegativePoints(req) { ... } // pure, testable
```

### AP-7 False-Positive Success on Async OData Create (race condition)

Showing a success toast before the server confirms the create can mislead users when the request fails silently.

```js
// WRONG — toast fires before server round-trip; failure is invisible
this.getOwnerComponent().getModel().bindList("/Stories").create(oPayload);
MessageToast.show("Story created.");  // fires immediately

// CORRECT — wait for server confirmation
var oContext = this.getOwnerComponent().getModel().bindList("/Stories").create(oPayload);
oContext.created()
  .then(function() { MessageToast.show(this._t("storyCreated")); }.bind(this))
  .catch(function(oErr) { MessageBox.error(this._t("errorCreateFailed") + ": " + oErr.message); }.bind(this));
```

### AP-8 Cross-Aggregate Deep Join From the Frontend (violates DDD)

The frontend must not compose multi-aggregate queries. Story→Sprint→Release navigation happens in a service function, not in a UI binding path.

```js
// WRONG — frontend driving a cross-aggregate JOIN
items="{path: '/Stories', parameters: { $expand: 'sprint/release' }}"

// CORRECT — call the service function; it resolves the traversal
this.on('storiesByRelease', async (req) => {
  const { releaseId } = req.data;
  const { Stories, Sprints } = this.entities;
  const sprints = await SELECT.from(Sprints).where({ release_ID: releaseId });
  const sprintIds = sprints.map(s => s.ID);
  return SELECT.from(Stories).where({ sprint_ID: { in: sprintIds } });
});
```

---

## Spec-Driven Development Workflow

Every feature and every migration follows this sequence. Do not skip phases.

```
Phase 1: Requirements
  Artifact: specs/<feature>/requirements.md
  Contains: user stories, acceptance criteria (Given/When/Then), edge cases, protected behaviours
  Review: @lead-architect must approve before proceeding

Phase 2: Design
  Artifact: specs/<feature>/design.md
  Contains: entity definitions, service contracts (method, params, return type), component specs, file list
  Review: @lead-architect must approve before proceeding

Phase 3: Task Breakdown
  Artifact: specs/<feature>/todo.md
  Contains: ordered task list, agent assignments (Agent A / Agent B), integration contracts
  Action: /clear context after todo.md is written — plan is on disk

Phase 4: Implementation
  Pre-flight: invoke @lead-architect and @senior-app-developer in advisory mode first
    → @lead-architect reads design.md → outputs architectural decision + 2 principles + 1 boundary (max 200 words)
    → @senior-app-developer reads design.md → outputs 3 CAP patterns + 1 pitfall + 1 contract check (max 150 words)
    These advisories run before /run-parallel-agents so the first implementation attempt is correct.
  Action: /run-parallel-agents — agents read specs as their brief
  Rule: agents never implement anything not in specs/<feature>/design.md

Phase 5: Review Gate
  Order: @code-reviewer + @tech-evangelist (parallel) → @senior-app-developer → @lead-architect
  Rule: no merge before @lead-architect approves
  Convergence: each reviewer tracks the pass number (Pass 1/2/3). Pass 3 forces approval
    unless a security BLOCKER (code-reviewer), accessibility/data-binding BLOCKER (tech-evangelist),
    hard contract mismatch (senior-app-developer), or DDD cross-context write (lead-architect) remains.
  Fixing: each finding lists OPTION A (simplest) and OPTION B (idiomatic) — pick one and re-review.
```

---

## Sub-Agent Hierarchy

Agents are invoked via `@` typeahead. Invoke review agents before every merge.

| Agent | Invocation | Authority |
|-------|-----------|-----------|
| `@lead-architect` | **Advisory (Phase 4 start):** `@lead-architect review design.md for implementation advisory` | Architectural decision + principles + boundary (max 200 words) |
| `@lead-architect` | **Spec review:** `@lead-architect review specs/` | Final say on design — may interview user (max 2 questions) |
| `@lead-architect` | **Code review:** `@lead-architect review all changes` | Final say — can reject merge; converges in 3 passes |
| `@senior-app-developer` | **Advisory (Phase 4 start):** `@senior-app-developer review design.md for implementation advisory` | CAP patterns + pitfall + contract check (max 150 words) |
| `@senior-app-developer` | **Code review:** `@senior-app-developer validate api contracts` | API contract authority; converges in 3 passes |
| `@code-reviewer` | `@code-reviewer review all changed files` | Code quality gate; converges in 3 passes |
| `@tech-evangelist` | `@tech-evangelist review frontend` | Frontend/UI5 quality gate; converges in 3 passes |

**Phase 4 advisory invocation order:** `@lead-architect` and `@senior-app-developer` in advisory mode → `/run-parallel-agents`

**Phase 5 review order:** `@code-reviewer` + `@tech-evangelist` in parallel → `@senior-app-developer` → `@lead-architect`

Always run `@code-reviewer` and `@tech-evangelist` in parallel (separate terminals or `/run-parallel-agents`).
Always run `@senior-app-developer` after those two.
Always run `@lead-architect` last.

---

## Security Rules — Non-Negotiable

- **NO** hardcoded secrets, credentials, API keys, or tokens in any file
- **NO** string concatenation to build SQL, CQL, OData query strings, or URLs containing user input
- **NO** calls to `eval()`, `Function()`, or `dynamic require()` with runtime values
- **NO** logging of request bodies, passwords, tokens, session IDs, or PII
- **ALL** user input must be validated at the service boundary before use
- **DEPENDENCIES** must be installed from the approved npm registry only

## Telemetry and Observability
- Use `cds.log('<service-name>')` for structured logging in all service handlers
- Log: entity created (type, ID), action called (name), errors (message only)
- Do NOT log: assignee names, request body content, PII

## What Claude Must Not Do Without Explicit Human Instruction
- Run `git push`, `git push --force`, or any remote operation
- Run `cf deploy`, `cf push`, or any Cloud Foundry deployment command
- Modify `.env`, `.env.*`, `*.pem`, `*.key`, or any credential file
- Modify `CLAUDE.md` or `.claude/settings.json`
- Install packages not already in `package.json` without asking first

## Definition of Done (for every task)
- [ ] Code follows patterns in this file
- [ ] No security rule violations (run `@security-reviewer` before merge)
- [ ] Service starts cleanly with `cds watch`
- [ ] UI renders without console errors
- [ ] Specs written and approved before implementation (SDD workflow)
