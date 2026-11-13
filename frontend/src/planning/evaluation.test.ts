import { describe, expect, it } from 'vitest'
import type { Job, Layout, Result, Scenario } from '../api/types'
import {
  DEADLINE_MARGIN_MS, buildCommit, clampPosition, classifyResult, describeJob, evaluateRequest, formatPence, formatValue,
  nudge, primaryMetric, samePosition, unitLabel,
} from './evaluation'

// Labelled synthetic test inputs shaped like the backend wire types. Not runtime results.
const head = { scenario_id: 's1', revision: 3, scope: 'accepted' as const }
const res = (over: Partial<Pick<Result, 'run_id' | 'scenario_id' | 'scenario_revision' | 'scope'>> = {}) =>
  ({ run_id: 'run-a', scenario_id: 's1', scenario_revision: 3, scope: 'accepted' as const, ...over })

describe('classifyResult (stale-result guard)', () => {
  it('is current only for the selected run of the head revision with no draft edits', () => {
    expect(classifyResult({ result: res(), head, currentRunId: 'run-a', draftDirty: false })).toBe('current')
  })
  it('marks unsaved draft edits stale immediately', () => {
    expect(classifyResult({ result: res(), head, currentRunId: 'run-a', draftDirty: true })).toBe('stale-draft')
  })
  it('never lets an older revision become current, even if it finishes late', () => {
    expect(classifyResult({ result: res({ scenario_revision: 2 }), head, currentRunId: 'run-a', draftDirty: false })).toBe('superseded')
  })
  it('respects a newer same-revision selection', () => {
    expect(classifyResult({ result: res(), head, currentRunId: 'run-b', draftDirty: false })).toBe('not-selected')
  })
  it('does not treat a run as current after a failure cleared the selection', () => {
    expect(classifyResult({ result: res(), head, currentRunId: null, draftDirty: false })).toBe('not-selected')
  })
  it('separates scenarios and scopes', () => {
    expect(classifyResult({ result: res({ scenario_id: 's2' }), head, currentRunId: 'run-a', draftDirty: false })).toBe('superseded')
    expect(classifyResult({ result: res({ scope: 'hypothetical' }), head, currentRunId: 'run-a', draftDirty: false })).toBe('superseded')
  })
})

describe('formatting', () => {
  it('shows the unit for m2_h and keeps a valid zero as zero', () => {
    expect(unitLabel('m2_h')).toBe('m²·h')
    expect(formatValue(0)).toBe('0')
    expect(formatValue(2)).toBe('2')
    expect(formatValue(0.1 + 0.2)).toBe('0.3')
  })
  it('formats pence exactly', () => {
    expect(formatPence(1234)).toBe('£12.34')
    expect(formatPence(5)).toBe('£0.05')
    expect(formatPence(123456789)).toBe('£1,234,567.89')
  })
})

describe('position editing', () => {
  it('nudges in ENU and rounds to the millimetre', () => {
    expect(nudge([0, -1, 0], 0.1, 0)).toEqual([0.1, -1, 0])
    expect(nudge([0.1, 0.2, 0], 0.2, 0.1)).toEqual([0.3, 0.3, 0])
    expect(samePosition([0.3, 0.3, 0], nudge([0.1, 0.2, 0], 0.2, 0.1))).toBe(true)
  })
  it('clamps to the edit limit and rejects non-finite input', () => {
    expect(clampPosition([999, -999, 0])).toEqual([50, -50, 0])
    expect(clampPosition([Number.NaN, 1, 0])).toEqual([0, 1, 0])
  })
})

const layout: Layout = {
  schema_version: '0.1.0', layout_id: 'L', revision: 1, kind: 'proposed',
  placements: [{ placement_id: 'tree-1', location_id: 'loc', position_enu_m: [0, -1, 0], profile_id: 'p', candidate_id: null, pinned: false }],
}

const scenario = (deadline: string) => ({
  schema_version: '0.1.0', scenario_id: 's1', revision: 3, scope: 'accepted', base_scenario_ref: null, created_at_utc: '2026-11-13T00:00:00Z',
  input: {
    proposed_layout_ref: { layout_id: 'L', revision: 1 },
    search: { algorithm: 'a', version: 'v', seed: 0, comparison_policy: 'c', reference_policy: 'r', deadline_utc: deadline },
    objective: { kind: 'maximise_shade_under_budget', primary_case_id: 'case', quantity_kind: 'geometric' },
  },
}) as unknown as Scenario

describe('buildCommit', () => {
  const now = Date.parse('2026-11-13T09:00:00Z')
  it('creates the next layout revision with only the moved placement changed', () => {
    const plan = buildCommit(scenario('2026-11-13T12:00:00Z'), layout, 'tree-1', [20, -1, 0], now)
    expect(plan.layout.revision).toBe(2)
    expect(plan.layout.placements[0].position_enu_m).toEqual([20, -1, 0])
    expect(plan.input.proposed_layout_ref).toEqual({ layout_id: 'L', revision: 2 })
    expect(plan.ifMatch).toBe(3)
    expect(plan.deadlineRenewedTo).toBeNull()
    expect(plan.input.search.deadline_utc).toBe('2026-11-13T12:00:00Z')
    expect(layout.placements[0].position_enu_m).toEqual([0, -1, 0]) // input not mutated
  })
  it('renews a job deadline that is about to expire, and says so', () => {
    const soon = new Date(now + DEADLINE_MARGIN_MS - 1000).toISOString()
    const plan = buildCommit(scenario(soon), layout, 'tree-1', [1, 1, 0], now)
    expect(plan.deadlineRenewedTo).toBe('2026-11-13T11:00:00Z')
    expect(plan.input.search.deadline_utc).toBe('2026-11-13T11:00:00Z')
  })
  it('refuses to edit a layout the scenario does not reference', () => {
    expect(() => buildCommit(scenario('2026-11-13T12:00:00Z'), { ...layout, revision: 9 }, 'tree-1', [0, 0, 0], now)).toThrow()
    expect(() => buildCommit(scenario('2026-11-13T12:00:00Z'), layout, 'nope', [0, 0, 0], now)).toThrow()
  })
  it('builds an evaluate_layout request bound to the exact scenario revision and layout', () => {
    expect(evaluateRequest(scenario('2026-11-13T12:00:00Z'), 'ui-1')).toEqual({
      request_id: 'ui-1', operation: 'evaluate_layout',
      scenario_ref: { scenario_id: 's1', revision: 3, scope: 'accepted' },
      arguments: { layout_ref: { layout_id: 'L', revision: 1 } },
    })
  })
})

const job = (over: Partial<Job>): Job => ({
  cancel_requested: false, created_at_utc: '', delivery: null, error: null, finished_at_utc: null, input_fingerprint: 'f',
  job_id: 'j', operation: 'evaluate_layout', progress: null, request_id: 'r', run_id: null, scenario_id: 's1', scenario_revision: 3,
  schema_version: '0.1.0', scope: 'accepted', selection_seq: 1, started_at_utc: null, status: 'queued', superseded_by_revision: null,
  view_slot: 'evaluation', ...over,
})

describe('describeJob', () => {
  it('covers every job state without inventing a result', () => {
    expect(describeJob(job({ status: 'queued' })).tone).toBe('progress')
    expect(describeJob(job({ status: 'running', progress: { phase: 'rays', completed: 1, total: 4, unit: 'bins' } })).detail).toContain('rays: 1/4 bins')
    expect(describeJob(job({ status: 'running', cancel_requested: true })).label).toBe('Cancelling…')
    expect(describeJob(job({ status: 'cancelled' })).detail).toContain('No result')
    const failed = describeJob(job({ status: 'failed', error: { code: 'NUMERICAL_FAILURE', message: 'boom', details: {}, field_errors: [], retryable: false } }))
    expect(failed.tone).toBe('danger')
    expect(failed.detail).toContain('NUMERICAL_FAILURE')
    expect(describeJob(job({ status: 'completed', run_id: 'r1', superseded_by_revision: 4 })).detail).toContain('Superseded by revision 4')
  })
})

describe('primaryMetric', () => {
  it('prefers additional_shade for the primary case', () => {
    const m = (metric_id: string, case_id: string, value: number) => ({ metric_id, case_id, value }) as unknown as Result['metrics'][number]
    const result = { metrics: [m('winter_sun_loss', 'case', 9), m('additional_shade', 'other', 1), m('additional_shade', 'case', 2)] } as unknown as Result
    expect(primaryMetric(result, 'case')?.value).toBe(2)
    expect(primaryMetric(result, 'missing')?.value).toBe(1)
    expect(primaryMetric({ metrics: [] } as unknown as Result, 'case')).toBeNull()
  })
})
