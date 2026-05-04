const cds = require('@sap/cds');
const log = cds.log('sprint');

module.exports = cds.service.impl(async function () {

  // ── Sprint Invariants ─────────────────────────────────────────────────────
  // SRP: each hook registers one responsibility via a named helper.

  this.before('CREATE', 'Sprints', (req) => {
    _requireSprintName(req);
  });

  this.before('UPDATE', 'Sprints', (req) => {
    _requireSprintName(req);
  });

  // ── totalPoints Analytics Function ────────────────────────────────────────
  // Read-only: counts storyPoints of Completed stories in a sprint.
  // OCP: sprint completion logic (completeSprint action) lives in sprint-actions.js
  // added via extend service in Phase 1 — never modify this file for that.

  this.on('totalPoints', async (req) => {
    const { sprintId } = req.data;
    if (!sprintId) return req.error(400, 'sprintId is required');
    const { Stories } = this.entities;
    const stories = await SELECT.from(Stories)
      .where({ sprint_ID: sprintId, status: 'Completed' });
    const total = stories.reduce((sum, s) => sum + (s.storyPoints || 0), 0);
    log.info('totalPoints', { sprintId, total });
    return total;
  });

});

// ── Domain Helpers ────────────────────────────────────────────────────────

function _requireSprintName(req) {
  const { name } = req.data;
  if (name !== undefined && (!name || !name.trim())) {
    return req.error(400, 'name is required');
  }
}
