const cds = require('@sap/cds');
const log = cds.log('backlog');

// Sprints a story may be assigned to — enforced at every CREATE/UPDATE boundary.
// OCP: add new valid statuses here without modifying any handler function.
const ASSIGNABLE_SPRINT_STATUSES = Object.freeze(new Set(['Planned', 'Active']));

module.exports = cds.service.impl(async function () {

  // ── Story Invariants ──────────────────────────────────────────────────────
  // SRP: each before-hook registers one responsibility via a named helper.
  // Helpers live outside this closure — pure functions, fully testable.

  this.before('CREATE', 'Stories', async (req) => {
    _requireTitle(req);
    _requireNonNegativePoints(req);
    await _requireAssignableSprint(req, this);
  });

  this.before('UPDATE', 'Stories', async (req) => {
    _requireNonNegativePoints(req);
    await _requireAssignableSprint(req, this);
  });

  // ── Story Domain Events ───────────────────────────────────────────────────
  // DDD: significant state transitions emit domain events so downstream
  // consumers (analytics, audit, notifications) can react without coupling.
  // Events carry only IDs and new state — never request body data or PII.

  this.after('UPDATE', 'Stories', async (result, req) => {
    if (req.data.status === 'Completed') {
      await cds.emit('StoryStatusChanged', { storyId: result.ID, newStatus: 'Completed' });
      log.info('StoryStatusChanged', { storyId: result.ID });
    }
  });

});

// ── Domain Helpers ────────────────────────────────────────────────────────
// Each function enforces exactly ONE invariant (SRP).
// Pure and stateless — no side effects, no service references except where
// explicitly passed (DIP: depends on the CDS srv abstraction, not sqlite).

function _requireTitle(req) {
  const { title } = req.data;
  if (title !== undefined && (!title || !title.trim())) {
    return req.error(400, 'title is required');
  }
}

function _requireNonNegativePoints(req) {
  const { storyPoints } = req.data;
  if (storyPoints !== undefined && storyPoints < 0) {
    return req.error(400, 'storyPoints must be 0 or greater');
  }
}

// Invariant: a Story may only belong to a Planned or Active sprint.
// Completed sprints are closed — assigning to them would corrupt velocity data.
async function _requireAssignableSprint(req, srv) {
  const { sprint_ID } = req.data;
  if (!sprint_ID) return;
  const { Sprints } = srv.entities;
  const sprint = await SELECT.one.from(Sprints).where({ ID: sprint_ID });
  if (sprint && !ASSIGNABLE_SPRINT_STATUSES.has(sprint.status)) {
    return req.error(422, 'Cannot assign a story to a Completed sprint');
  }
}
