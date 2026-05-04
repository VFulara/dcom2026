using { planning } from '../db/schema';

// ── Bounded Context: Sprint Management ───────────────────────────────────
// Owns the Sprint aggregate lifecycle — creation, status, and velocity.
// Stories are exposed @readonly for the sprint board display.
// All Story mutations go through BacklogService.
//
// Phase 1 Agent B extends this service in new files:
//   srv/sprint-actions.cds — adds completeSprint action
//   srv/sprint-actions.js  — implements completeSprint
//
// OData path: /odata/v4/sprint/

service SprintService @(path: '/odata/v4/sprint') {

  entity Sprints as projection on planning.Sprints;

  // Stories exposed read-only for the Sprint Board display.
  // The sprint board renders story cards grouped by sprint.
  // Story mutations (status change, sprint reassignment) go through BacklogService.
  @readonly
  entity Stories as projection on planning.Stories {
    *,
    sprint : redirected to Sprints
  };

  // Read-only velocity function: total storyPoints for Completed stories in a sprint.
  // OCP: sprint-actions.cds adds completeSprint via extend service — never modify here.
  function totalPoints(sprintId : UUID) returns Integer;

}
