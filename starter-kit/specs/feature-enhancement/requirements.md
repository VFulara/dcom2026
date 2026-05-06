# Feature Enhancement Requirements

> **Status: PROVIDED** — read and annotate before Step 1C.
> After reading, invoke: `@lead-architect review specs/feature-enhancement/requirements.md`
> The architect will challenge assumptions. Resolve any **REJECTED** items before proceeding to design.

---

## Architect Review Checklist
The lead-architect validates these before approving any feature:
- [ ] Bounded context boundaries respected (no cross-context writes)
- [ ] New services are standalone, not extensions of existing ones (unless mutating an existing aggregate)
- [ ] Domain events emitted for every significant state transition
- [ ] Invariants enforced at the service boundary, not inline
- [ ] No `$expand` chains crossing aggregate roots from the frontend (AP-8)

---

## Feature A: Release Management
**Agent A** · New standalone `ReleaseService` bounded context · File ownership: `db/schema.cds`, `srv/release-service.*`, `ui/view/Releases.*`, `ui/controller/Releases.*`

Releases are versioned delivery milestones that group Sprints for external stakeholder commitments.  
Model: `Release (version, targetDate, archived)` · `Sprint.release_ID` FK (a Sprint belongs to at most one Release).

### User Stories

| ID | As a… | I need to… | So that… |
|----|--------|-----------|----------|
| US-A1 | Project Manager | Create a Release with version and target date; archive it when shipped | Stakeholders see planned milestones; completed releases leave the active view |
| US-A2 | Team Lead | Assign a Sprint to a Release and view all stories scoped to that Release | Sprint work is traceable to a delivery commitment |

### Acceptance Criteria

**AC-A1: Create Release**
- Given POST with non-empty trimmed `version` and `targetDate`
- When no conflicting release exists
- Then Release created with `archived: false`; new record returned

**AC-A2: Assign Sprint to Release**
- Given Sprint in `Planned` or `Active` status and a non-archived Release
- When PATCH `sprint.release_ID` with valid Release ID
- Then Sprint is associated with that Release

**AC-A3: Stories by Release**
- Given valid Release ID
- When `storiesByRelease(releaseId)` is called
- Then all Stories whose Sprint belongs to that Release are returned
- And empty array is returned (not 404) when no stories exist

**AC-A4: Archive Release**
- Given Release with `archived: false`
- When `archiveRelease(releaseId)` is called
- Then `archived → true`; updated Release returned; `ReleaseArchived { releaseId, version }` event emitted
- And repeat call → 422 "Release is already archived"

**AC-A5: Archived Release guard**
- Given Release is archived
- When Sprint or Story assignment is attempted against it
- Then 422 "Cannot assign to an archived release"

### Invariants

- No hard deletes. `archived: true` is the only terminal state — no un-archiving.
- `storiesByRelease` traverses `Sprint.release_ID → Stories`; Story does NOT store `release_ID` directly (AP-8).
- A Release with no Sprints is valid (pre-populated future milestone).
- `version` must be non-empty and trimmed; reject blank strings.

### Protected Behaviours

- Stories CRUD, Sprints CRUD, and `totalPoints` must not break.

### Architectural Constraints

- `ReleaseService` is a **new standalone service** — does NOT extend `BacklogService` or `SprintService`.
- `Sprint.release_ID` FK is added to `db/schema.cds` only; Release entity lives in `db/schema.cds`.
- Cross-context reads via `@readonly` projection are permitted; **cross-context writes are forbidden**.

---

## Feature B: Sprint Analytics
**Agent B** · `completeSprint` extends `SprintService` · New standalone `AnalyticsService` · File ownership: `srv/sprint-actions.*`, `srv/analytics-service.*`, `ui/view/SprintAnalytics.*`, `ui/controller/SprintAnalytics.*`

Sprint completion safely moves unfinished work to the next sprint without data loss. Velocity (sum of completed story points) is the primary performance metric exposed via a read-only analytics service.

### User Stories

| ID | As a… | I need to… | So that… |
|----|--------|-----------|----------|
| US-B1 | Scrum Master | Complete a sprint, auto-moving unfinished stories to the next sprint | No work is lost at sprint boundary |
| US-B2 | Scrum Master | Query sprint velocity and view a per-sprint velocity dashboard | Team performance trends are visible at a glance |

### Acceptance Criteria

**AC-B1: Sprint Velocity**
- Given a Sprint with stories, some `Completed`
- When `sprintVelocity(sprintId)` is called
- Then sum of `storyPoints` for `status: Completed` stories only is returned
- And 0 is a valid result — not an error

**AC-B2: Complete Sprint**
- Given Sprint in `Active` status with ≥1 story
- When `completeSprint(sprintId, nextSprintId)` is called
- Then sprint `status → Completed`; stories with `New / In Progress / Blocked` move to `nextSprintId`; `Completed` stories remain in original sprint
- And `SprintCompleted { sprintId, movedCount }` event emitted

**AC-B3: Complete Sprint — Guards**
- Sprint already `Completed` → 422
- Sprint in `Planned` status → 422
- Sprint has no stories → 422
- `nextSprintId` not found → 404; `nextSprintId` already `Completed` → 422
- `sprintId === nextSprintId` → 422 "Target sprint must differ from current sprint"

**AC-B4: Analytics View**
- Given sprints with velocity data
- When Sprint Analytics view loads
- Then each sprint displays velocity score with a visual comparison (bar or progress indicator)

### Invariants

- Story move is atomic — all move or none move (use a transaction).
- `completeSprint` belongs to the Sprint aggregate → extends `SprintService` via `extend service`.
- `sprintVelocity` is read-only → lives in the new standalone `AnalyticsService`.

### Protected Behaviours

- Sprint CRUD and independent story updates must not break.
- `totalPoints` must not be duplicated — `sprintVelocity` is the new named function (AP-6).

### Architectural Constraints

- `completeSprint` mutates the Sprint aggregate → correct pattern is `extend service SprintService` in `srv/sprint-actions.cds/.js`.
- `AnalyticsService` is read-only; it must never mutate any entity.
- Each guard condition must be a separate named pure function — not inline if-chain (AP-6).

---

## Feature C: Backlog Enhancements
**Pre-built in starter kit — review only; do not re-implement.**

Adds text search, Status / Priority / Sprint dropdown filters, inline row editing (status + sprint), and sprint pre-assignment at story creation. Filter logic is centralised in `ui/util/FilterHelper.js` (SRP, AP-3). Agent A may extend `FilterHelper.js` if the design spec requires it.

### User Stories

| ID | As a… | I need to… | So that… |
|----|--------|-----------|----------|
| US-C1 | Developer | Search and filter the backlog by keyword, status, priority, or sprint; clear all filters in one action | I locate work items without scrolling; full list is one click away |
| US-C2 | Developer | Change story status and sprint assignment inline from the backlog row | I skip the detail view for routine updates |
| US-C3 | Scrum Master | Assign a sprint when creating a story | Stories enter the board already slotted into a sprint |

### Acceptance Criteria

**AC-C1: Text search** — filters title OR description; no page reload; empty input = no filter

**AC-C2: Dropdown filters** — Status / Priority / Sprint dropdowns apply AND logic; "All" removes that filter

**AC-C3: Combined filters** — text + dropdowns combine with AND logic

**AC-C4: Clear Filters** — resets search input and all dropdowns; full backlog reloads

**AC-C5: Inline status change** — row status dropdown fires PATCH immediately; row updates without reload; `StoryStatusChanged` event emitted on transition to `Completed`

**AC-C6: Inline sprint assignment** — row sprint dropdown fires PATCH; "None" sends `sprint_ID: null`; row updates without reload

**AC-C7: Sprint in Add Story dialog** — sprint selector pre-assigns sprint at creation

### Invariants

- Filter state is client-side only — no OData `$filter` queries required (local filtering acceptable for session data volumes).
- Inline sprint → "None" must send `sprint_ID: null` in PATCH payload (not omit the field).

### Protected Behaviours

- Existing Add Story fields (title, description, assignee, status, priority, storyPoints) must remain.
- Backlog OData binding must still `$expand=sprint`.
- No page reload or navigation on inline changes — only the affected row refreshes.

### Architectural Constraints

- All filter logic in `FilterHelper.js`; controllers call only `FilterHelper.buildFilters(...)` (AP-3).
- No inline ternary chains in XML view bindings — use `Formatters.js` (AP-1).
- No hardcoded user-visible strings in controllers — use `i18n` keys (AP-2).
