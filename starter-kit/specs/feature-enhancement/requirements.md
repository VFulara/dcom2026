# Feature Enhancement Requirements

> Status: PROVIDED — review and annotate before Step 1C.
> Invoke `@lead-architect review specs/feature-enhancement/requirements.md` after reading.
> The architect will challenge assumptions. Address any REJECTED items, then proceed to design.

---

## Feature A: Release Management

### Context
Teams need to group work for external delivery. A Release is a versioned delivery milestone.
Sprints are the internal cadence; Releases are the external commitment.
A Release may contain multiple Sprints. A Sprint belongs to at most one Release.

### User Stories

1. As a **project manager**, I want to create a Release with a version label and target date so that I can communicate planned delivery milestones to stakeholders.

2. As a **team lead**, I want to assign a Sprint to a Release so that I know which sprint's work counts toward an upcoming delivery.

3. As a **developer**, I want to see which Release a story's sprint belongs to so that I can understand the delivery context of my work.

4. As a **project manager**, I want to archive a Release that has shipped so that it no longer appears in the active planning view but remains accessible for historical reference.

5. As a **team lead**, I want to list all stories associated with a Release so that I can assess release readiness.

### Acceptance Criteria

**AC-A1: Create Release**
- Given I submit a POST with `version` and `targetDate`
- When the release does not already exist
- Then a Release record is created with `archived: false` by default
- And the new Release is returned in the response

**AC-A2: Sprint assignment to Release**
- Given a Sprint exists in `Planned` or `Active` status
- When I PATCH `sprint.release_ID` with a valid Release ID
- Then the Sprint is associated with that Release
- And the story board can show which release a sprint belongs to

**AC-A3: Stories by Release**
- Given a valid Release ID
- When `storiesByRelease(releaseId)` is called
- Then all Stories whose sprint belongs to that Release are returned
- And if no stories exist, an empty array is returned (not 404)

**AC-A4: Archive Release**
- Given a Release exists with `archived: false`
- When `archiveRelease(releaseId)` is called
- Then `archived` is set to `true` and the updated Release is returned
- And a `ReleaseArchived` domain event is emitted with `{ releaseId, version }`
- And calling `archiveRelease` again returns 422 ("Release is already archived")

**AC-A5: Archived Release guard**
- Given a Release is archived
- When a Story or Sprint tries to be assigned to that Release
- Then the assignment is rejected with 422 ("Cannot assign to an archived release")

### Edge Cases and Invariants

- Releases are NEVER hard-deleted. `archived: true` is the only terminal state.
- `archived: false` cannot be set once `archived: true` — no un-archiving.
- A Release with no Sprints is valid (pre-populated for future planning).
- Version string must be non-empty and trimmed.
- `storiesByRelease` must traverse Sprint→Story, not store `release_ID` directly on Story.

### Protected Behaviours

- Existing Stories CRUD must not break.
- Existing Sprints CRUD must not break.
- `totalPoints` function remains unchanged.

---

## Feature B: Sprint Analytics

### Context
Teams need visibility into sprint performance to improve planning. Velocity is the primary metric.
Sprint completion must safely move unfinished work to the next sprint without losing any stories.

### User Stories

1. As a **scrum master**, I want to see the velocity (completed story points) for a sprint so that I can track team performance over time.

2. As a **scrum master**, I want to complete a sprint and automatically move unfinished stories to the next sprint so that no work is lost at sprint boundary.

3. As a **team lead**, I want a Sprint Analytics view that shows velocity per sprint as a visual comparison so that I can spot trends at a glance.

4. As a **developer**, I want the system to prevent completing a sprint that has no stories so that empty sprints cannot pollute velocity data.

### Acceptance Criteria

**AC-B1: Sprint Velocity**
- Given a Sprint with completed stories having storyPoints assigned
- When `sprintVelocity(sprintId)` is called
- Then the sum of `storyPoints` for stories with `status: Completed` is returned
- And stories with other statuses are excluded from the sum

**AC-B2: Complete Sprint**
- Given a Sprint in `Active` status with at least one story
- When `completeSprint(sprintId, nextSprintId)` is called
- Then the sprint's `status` is set to `Completed`
- And all stories with status `New`, `In Progress`, or `Blocked` are moved to `nextSprintId`
- And `Completed` stories remain in the original sprint
- And a `SprintCompleted` domain event is emitted with `{ sprintId, movedCount }`

**AC-B3: Complete Sprint — Guard Conditions**
- Cannot complete a sprint that is already `Completed` → 422
- Cannot complete a sprint in `Planned` status (not yet active) → 422
- Cannot complete a sprint with no stories → 422
- `nextSprintId` must exist and must not be `Completed` → 404 or 422 respectively
- `sprintId === nextSprintId` is forbidden → 422 ("Target sprint must differ from current sprint")

**AC-B4: Analytics View**
- Given multiple sprints with velocity data
- When the Sprint Analytics view loads
- Then each sprint is displayed with its velocity score
- And a visual comparison (bar or progress indicator) shows relative velocity across sprints

### Edge Cases and Invariants

- A sprint with zero completed stories has velocity = 0 (not an error).
- Moving stories is atomic — all move or none move (use a transaction).
- `completeSprint` on a sprint in the same transaction as the story move must be consistent.

### Protected Behaviours

- Sprint CRUD (create, list, update) must not break.
- Stories can still be updated independently of sprint completion.
- `totalPoints` function already in the service must not be duplicated.

---

## Feature C: Backlog Enhancements

### Context
The current backlog shows all stories in a flat list with no way to filter, narrow, or reassign.
As the backlog grows, developers waste time scrolling. The team wants to stay in flow without switching to a separate search tool.

**Important design note:** Do NOT prescribe a specific filter implementation in requirements.
The design phase will evaluate options and the architect will challenge the chosen approach.
Requirements describe user *needs*, not the technical solution.

### User Stories

1. As a **developer**, I want to quickly find stories matching a keyword or phrase so that I can locate my work item without scrolling the entire backlog.

2. As a **developer**, I want to filter the backlog by status so that I can see only stories in a specific workflow state.

3. As a **developer**, I want to filter by priority so that I can focus on what matters most right now.

4. As a **developer**, I want to filter by sprint so that I can see the work planned for a specific time-box.

5. As a **developer**, I want to change a story's status directly from the backlog row so that I do not need to open a detail view for routine status transitions.

6. As a **developer**, I want to assign or reassign a story to a sprint from the backlog row so that sprint planning stays in one place.

7. As a **developer**, I want to clear all active filters in one action so that I can return to the full backlog immediately.

8. As a **scrum master**, I want to assign a sprint to a new story at creation time so that stories enter the board already slotted into a sprint.

### Acceptance Criteria

**AC-C1: Text search**
- Given stories are loaded in the backlog
- When I type a word or phrase in the search input
- Then only stories whose title OR description contains that text are shown
- And the filter applies without a page reload

**AC-C2: Dropdown filters**
- Given filter dropdowns are visible
- When I select a Status, Priority, or Sprint value
- Then the story list narrows to match all selected criteria simultaneously (AND logic)
- And selecting "All" (empty/default) removes that filter

**AC-C3: Combined filters**
- Given a text search and a Status filter are both active
- When the list renders
- Then only stories matching BOTH conditions are shown

**AC-C4: Clear all filters**
- Given one or more filters are active
- When I click "Clear Filters"
- Then the search input is cleared and all dropdowns reset to "All"
- And the full backlog reloads

**AC-C5: Inline status change**
- Given a story row is visible
- When I change the status dropdown on the row
- Then a PATCH is sent immediately (no save button)
- And the row updates without a page reload

**AC-C6: Inline sprint assignment**
- Given a story row is visible
- When I select a sprint from the sprint dropdown on the row (or select "None")
- Then a PATCH is sent to update `sprint_ID` (or clear it)
- And the row updates without a page reload

**AC-C7: Sprint in Add Story dialog**
- Given the "Add Story" dialog is open
- When I fill in title, status, priority and optionally select a sprint
- Then the story is created with the selected sprint pre-assigned

### Edge Cases and Invariants

- Empty search returns all stories (no filter applied).
- Filter state is client-side only — no OData $filter queries are required (local filtering is acceptable for session data volumes).
- Inline sprint change to "None" must send `sprint_ID: null` in the PATCH payload.
- Inline status change must emit a `StoryStatusChanged` domain event when transitioning to `Completed`.

### Protected Behaviours

- Existing "Add Story" dialog fields (title, description, assignee, status, priority, storyPoints) must remain.
- Backlog OData binding must still load stories with `$expand=sprint`.
- No page reload or navigation on inline changes — only the affected row refreshes.
