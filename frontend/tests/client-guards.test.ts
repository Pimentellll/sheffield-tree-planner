import { test } from 'node:test'
import assert from 'node:assert/strict'
import { currentMetric, sessionIdentity } from '../src/api/guards.ts'

// Synthetic identity-only inputs exercise the guard; these are not runtime result fixtures.
const ref = { scenario_id: 'scenario', revision: 1, scope: 'accepted' }
const session = { scenario: { ...ref }, layout: { layout_id: 'layout' } }
const delivery = { job_id: 'job', run_id: 'run', source_job_id: 'source', input_fingerprint: 'fingerprint', scenario_id: 'scenario', scenario_revision: 1, scope: 'accepted', selection_seq: 1, view_slot: 'evaluation' }
const job = { job_id: 'job', run_id: 'run', input_fingerprint: 'fingerprint', scenario_id: 'scenario', scenario_revision: 1, scope: 'accepted', selection_seq: 1, view_slot: 'evaluation', operation: 'evaluate_layout', status: 'completed', superseded_by_revision: null, delivery }
const result = { run_id: 'run', source_job_id: 'source', input_fingerprint: 'fingerprint', input_snapshot_ref: ref, scenario_id: 'scenario', scenario_revision: 1, scope: 'accepted', operation: 'evaluate_layout', metrics: [{ metric_id: 'additional_shade', quantity_kind: 'geometric', unit: 'm2_h', scenario_ref: ref, layout_id: 'layout', value: 0 }] }
const selections = { evaluation: { selection: { accepted_job_id: 'job', scenario_ref: ref, selection_seq: 1, view_slot: 'evaluation' }, current_job: job } }
test('finite zero remains a current value and cached source identity is allowed', () => assert.equal(currentMetric(session, job, result, selections), 0))
test('new selection, stale revision, bad fingerprint and non-finite values are rejected', () => {
  assert.equal(currentMetric(session, job, result, { evaluation: { ...selections.evaluation, selection: { ...selections.evaluation.selection, selection_seq: 2 } } }), null)
  assert.equal(currentMetric({ ...session, scenario: { ...ref, revision: 2 } }, job, result, selections), null)
  assert.equal(currentMetric(session, job, { ...result, input_fingerprint: 'other' }, selections), null)
  assert.equal(currentMetric(session, job, { ...result, metrics: [{ ...result.metrics[0], value: NaN }] }, selections), null)
  assert.notEqual(sessionIdentity(session), sessionIdentity({ ...session, scenario: { ...ref, revision: 3 } }))
})
