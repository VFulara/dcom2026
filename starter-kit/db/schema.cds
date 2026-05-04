namespace planning;

// ── Value Types ────────────────────────────────────────────────────────────
// Define valid values ONCE here. Never repeat them in service handlers,
// UI views, or comments. OCP: adding a new status means editing only this file.

type StoryStatus : String(20) enum {
  New        ;
  InProgress = 'In Progress';
  InReview   = 'In Review';
  Blocked    ;
  Completed  ;
}

type Priority : String(20) enum {
  Critical;
  High    ;
  Medium  ;
  Low     ;
}

type SprintStatus : String(20) enum {
  Planned  ;
  Active   ;
  Completed;
}

// ── Reusable Aspects ────────────────────────────────────────────────────────
// DRY: every aggregate gets audit fields by composing this aspect.
// Phase 1: Release entity must also use `: Auditable` — do not duplicate fields.

aspect Auditable {
  createdAt : Timestamp @cds.on.insert: $now;
}

// ── Aggregates ──────────────────────────────────────────────────────────────
// Each entity is one aggregate root. Cross-aggregate navigation is by FK only.
// DDD: Story lifecycle managed by BacklogService. Sprint lifecycle managed by SprintService.
// Neither service mutates entities owned by the other bounded context.

entity Stories : Auditable {
  key ID            : UUID         @cds.on.insert: $uuid;
  title             : String(200)  not null;
  description       : String(2000);
  assignee          : String(100);
  status            : StoryStatus  default 'New';
  priority          : Priority     default 'Medium';
  storyPoints       : Integer;
  estimateHours     : Decimal(6,2);
  sprint            : Association to Sprints;
}

entity Sprints {
  key ID        : UUID         @cds.on.insert: $uuid;
  name          : String(100)  not null;
  startDate     : Date;
  endDate       : Date;
  status        : SprintStatus default 'Planned';
}
