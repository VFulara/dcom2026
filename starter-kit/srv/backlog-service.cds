using { planning } from '../db/schema';

// ── Bounded Context: Backlog Management ───────────────────────────────────
// Owns the Story aggregate lifecycle — creation, status transitions,
// and sprint assignment. This is the only service that mutates Stories.
//
// Sprint reference data is exposed @readonly so controllers can populate
// sprint assignment dropdowns without coupling to SprintService directly.
// All Sprint mutations (create, update, completeSprint) go through SprintService.
//
// OData path: /odata/v4/backlog/

service BacklogService @(path: '/odata/v4/backlog') {

  entity Stories as projection on planning.Stories {
    *,
    sprint : redirected to Sprints
  };

  // Sprint reference data — read-only.
  // BacklogService is a consumer of this data, not the owner.
  // Exposed here to resolve the Stories.sprint navigation property
  // and to populate sprint assignment dropdowns in the Backlog view.
  @readonly
  entity Sprints as projection on planning.Sprints;

}
