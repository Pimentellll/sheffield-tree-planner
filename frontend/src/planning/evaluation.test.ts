import { describe, expect, it } from 'vitest'
import type { Job, Layout, Result, Scenario } from '../api/types'
import {
  DEADLINE_MARGIN_MS, candidateAt, nearestCandidate, stepCandidate, diffInputs, parsePounds, requirementsOf, sameRequirements, validateRequirements, buildCommit, clampPosition, classifyResult, describeJob, evaluateRequest, formatPence, formatValue,
  nudge, primaryMetric, samePosition, unitLabel, progressView, NO_PROGRESS_CAPTION,
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
    constraints: { budget_pence: 10000, budget_basis: 'upfront', max_tree_count: null, excluded_region_ids: [], allowed_profile_ids: ['p'] },
  },
}) as unknown as Scenario

describe('buildCommit', () => {
  const now = Date.parse('2026-11-13T09:00:00Z')
  it('creates the next layout revision with only the moved placement changed', () => {
    const plan = buildCommit(scenario('2026-11-13T12:00:00Z'), layout, 'tree-1', [20, -1, 0], now)
    expect(plan.layout?.revision).toBe(2)
    expect(plan.layout?.placements[0].position_enu_m).toEqual([20, -1, 0])
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
  it('prints no "0/0" count when the backend reports a zero total (-51 E)', () => {
    expect(describeJob(job({ status: 'running', progress: { phase: 'rays', completed: 0, total: 0, unit: 'bins' } })).detail).not.toContain('0/0')
  })
})

describe('progressView (-51 Q, brief §11 #10)', () => {
  it('shows counts only for a positive backend total', () => {
    expect(progressView(job({ status: 'running', progress: { phase: 'rays', completed: 1, total: 4, unit: 'bins' } }))).toEqual({ kind: 'counts', completed: 1, total: 4 })
  })
  it('is indeterminate, with the no-estimate caption, when no counts are reported', () => {
    for (const progress of [null, { phase: 'rays', completed: 0, total: 0, unit: 'bins' }]) {
      const view = progressView(job({ status: 'running', progress }))
      expect(view).toEqual({ kind: 'indeterminate', caption: NO_PROGRESS_CAPTION })
    }
    expect(progressView(job({ status: 'queued' })).kind).toBe('indeterminate')
    expect(NO_PROGRESS_CAPTION).toContain('no percentage or phase is estimated')
  })
  it('shows nothing for a finished job', () => {
    for (const status of ['completed', 'failed', 'cancelled'] as const) expect(progressView(job({ status })).kind).toBe('none')
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

describe('requirements drafts (STP-021)', () => {
  const now = Date.parse('2026-11-13T09:00:00Z')
  const s0 = scenario('2026-11-13T12:00:00Z')
  it('parses pounds to integer pence without floating point', () => {
    expect(parsePounds('100')).toBe(10000)
    expect(parsePounds('£1,234.5')).toBe(123450)
    expect(parsePounds('0.07')).toBe(7)
    expect(parsePounds('19.999')).toBeNull()
    expect(parsePounds('-5')).toBeNull()
    expect(parsePounds('abc')).toBeNull()
    expect(parsePounds('1e3')).toBeNull()
  })
  it('accepts thousands separators only in their proper places (-51 review of #91)', () => {
    expect(parsePounds('75,000')).toBe(7_500_000)
    expect(parsePounds('£1,234,567.89')).toBe(123_456_789)
    expect(parsePounds('75000')).toBe(7_500_000)
    expect(parsePounds('7,5,0,0,0')).toBeNull()
    expect(parsePounds('75,0x0')).toBeNull()
    expect(parsePounds('7500,00')).toBeNull()
    expect(parsePounds(',75,000')).toBeNull()
    expect(parsePounds('75,000,')).toBeNull()
    expect(parsePounds('1,23')).toBeNull()
  })
  it('validates count, budget and exclusion ids', () => {
    expect(validateRequirements({ budgetPence: 100, maxTreeCount: null, excludedRegionIds: [] }, [])).toEqual([])
    expect(validateRequirements({ budgetPence: -1, maxTreeCount: 2.5, excludedRegionIds: ['x'] }, ['y'])).toHaveLength(3)
  })
  it('compares requirements independent of exclusion order', () => {
    expect(sameRequirements({ budgetPence: 1, maxTreeCount: 2, excludedRegionIds: ['a', 'b'] }, { budgetPence: 1, maxTreeCount: 2, excludedRegionIds: ['b', 'a'] })).toBe(true)
    expect(sameRequirements({ budgetPence: 1, maxTreeCount: 2, excludedRegionIds: [] }, { budgetPence: 1, maxTreeCount: null, excludedRegionIds: [] })).toBe(false)
  })
  it('a requirement-only edit keeps the layout and changes only the named constraints', () => {
    const r = { ...requirementsOf(s0), budgetPence: 5000, maxTreeCount: 1 }
    const plan = buildCommit(s0, layout, 'tree-1', [0, -1, 0], now, r)
    expect(plan.layout).toBeNull()
    expect(plan.input.proposed_layout_ref).toEqual({ layout_id: 'L', revision: 1 })
    expect(plan.changes.map(c => c.path).sort()).toEqual(['constraints.budget_pence', 'constraints.max_tree_count'])
    expect(plan.input.constraints.allowed_profile_ids).toEqual(['p'])
  })
  it('diffs nested inputs by path, comparing arrays whole', () => {
    expect(diffInputs({ a: { b: 1, c: [1, 2] }, d: 'x' }, { a: { b: 2, c: [1, 2] }, d: 'x', e: null })).toEqual([
      { path: 'a.b', before: 1, after: 2 }, { path: 'e', before: undefined, after: null },
    ])
  })
})

describe('catalogue candidates (physical runtime)', () => {
  // Labelled synthetic catalogue in the same shape as SiteBundle.candidate_catalogue.
  const cat = [
    { candidate_id: 'c1', location_id: 'l1', position_enu_m: [0, 0, 0], profile_id: 'p' },
    { candidate_id: 'c2', location_id: 'l2', position_enu_m: [-2, 0, 0], profile_id: 'p' },
    { candidate_id: 'c3', location_id: 'l3', position_enu_m: [2, 0, 0], profile_id: 'p' },
  ]
  it('finds the candidate at an exact position only', () => {
    expect(candidateAt(cat, [2, 0, 0])?.candidate_id).toBe('c3')
    expect(candidateAt(cat, [2.1, 0, 0])).toBeNull()
  })
  it('snaps a free drag to the nearest candidate', () => {
    expect(nearestCandidate(cat, [1.4, 0.3, 0])?.candidate_id).toBe('c3')
    expect(nearestCandidate([], [0, 0, 0])).toBeNull()
  })
  it('steps to the nearest candidate in a direction and stops at the edge', () => {
    expect(stepCandidate(cat, [0, 0, 0], 1, 0)?.candidate_id).toBe('c3')
    expect(stepCandidate(cat, [0, 0, 0], -1, 0)?.candidate_id).toBe('c2')
    expect(stepCandidate(cat, [2, 0, 0], 1, 0)).toBeNull()
    expect(stepCandidate(cat, [0, 0, 0], 0, 1)).toBeNull()
  })
  it('commits candidate and location identity with a moved placement', () => {
    const s0 = scenario('2026-11-13T12:00:00Z')
    const plan = buildCommit(s0, layout, 'tree-1', [2, 0, 0], Date.parse('2026-11-13T09:00:00Z'), undefined, { candidate_id: 'c3', location_id: 'l3' })
    expect(plan.layout?.placements[0]).toMatchObject({ candidate_id: 'c3', location_id: 'l3', position_enu_m: [2, 0, 0] })
  })
})
