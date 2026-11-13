import { describe, expect, it } from 'vitest'
import type { Result, Scenario } from '../api/types'
import { draftBannerText, formatPounds, headerStatus, latestEvaluation, provenanceItems, scenarioSummary } from './shell'

// LABELLED SYNTHETIC TEST INPUT: shaped like the generated contracts to exercise pure view logic.
// It is not a runtime result and is never rendered by the application.
const scenario = {
  input: {
    objective: { kind: 'maximise_shade_under_budget', primary_case_id: 'summer', quantity_kind: 'geometric' },
    constraints: { budget_pence: 7_500_000, budget_basis: 'upfront', max_tree_count: null, excluded_region_ids: ['x1', 'x2'] },
    scene_revision: 3,
    candidate_catalogue_revision: 2,
  },
} as unknown as Scenario
const provenance = { evaluator_version: 'ev-1', solar_version: 'sol-1', search_version: 'greedy-1', seed: 7, execution_mode: 'live' }

describe('headerStatus', () => {
  const base = { connected: true, revision: 4, draftDirty: false, activeJob: null, evaluationCurrentness: null }
  it('says there is no accepted scenario when offline', () => {
    expect(headerStatus({ ...base, connected: false })).toEqual({ label: 'NO ACCEPTED SCENARIO', tone: 'muted' })
  })
  it('names a running job before anything else', () => {
    expect(headerStatus({ ...base, draftDirty: true, activeJob: { status: 'running', operation: 'search_layouts' } }).label).toBe('REV 4 · SEARCH RUNNING')
    expect(headerStatus({ ...base, activeJob: { status: 'queued', operation: 'evaluate_layout' } }).label).toBe('REV 4 · EVALUATION QUEUED')
  })
  it('ignores a finished job', () => {
    expect(headerStatus({ ...base, activeJob: { status: 'cancelled', operation: 'search_layouts' } }).label).toBe('REV 4 · ACCEPTED')
  })
  it('flags an unaccepted draft as a warning', () => {
    expect(headerStatus({ ...base, draftDirty: true, evaluationCurrentness: 'current' })).toEqual({ label: 'REV 4 + DRAFT · NOT ACCEPTED', tone: 'warn' })
  })
  it('says RESULT CURRENT only when the workspace guard says current', () => {
    expect(headerStatus({ ...base, evaluationCurrentness: 'current' }).label).toBe('REV 4 · RESULT CURRENT')
    expect(headerStatus({ ...base, evaluationCurrentness: 'superseded' }).label).toBe('REV 4 · ACCEPTED')
    expect(headerStatus({ ...base, evaluationCurrentness: 'not-selected' }).label).toBe('REV 4 · ACCEPTED')
  })
})

describe('formatPounds and scenarioSummary', () => {
  it('drops .00 only for whole pounds and keeps exact pence otherwise', () => {
    expect(formatPounds(7_500_000)).toBe('£75,000')
    expect(formatPounds(6_400_050)).toBe('£64,000.50')
    expect(formatPounds(0)).toBe('£0')
  })
  it('reads the accepted scenario fields without inventing a rule count', () => {
    expect(scenarioSummary(scenario)).toEqual({ budget: '£75,000', basis: 'upfront', objective: 'Most shade within budget (geometric, case summer)', maxTrees: 'no limit', exclusions: 2 })
  })
})

describe('draftBannerText', () => {
  it('lists the changed paths from the real diff', () => {
    const text = draftBannerText(3, [{ path: 'constraints.budget_pence', before: 6_400_000, after: 7_500_000 }])
    expect(text.title).toBe('Results describe accepted revision 3, not your draft.')
    expect(text.detail).toContain('1 unaccepted change (constraints.budget_pence)')
  })
  it('still warns when the change set cannot be built (invalid fields)', () => {
    expect(draftBannerText(3, []).detail).toContain('unaccepted edits')
  })
})

describe('latestEvaluation', () => {
  it('skips failed jobs and other operations', () => {
    const runs = [
      { job: { operation: 'evaluate_layout' }, result: null },
      { job: { operation: 'search_layouts' }, result: {} as Result },
      { job: { operation: 'evaluate_layout' }, result: { run_id: 'r1' } as Result },
    ] as const
    expect(latestEvaluation(runs)?.result?.run_id).toBe('r1')
    expect(latestEvaluation([])).toBeNull()
  })
})

describe('provenanceItems', () => {
  it('uses the run snapshot revisions and adds search version and seed only for searches', () => {
    expect(provenanceItems({ operation: 'evaluate_layout', provenance } as unknown as Result, scenario))
      .toEqual(['evaluator ev-1', 'solar sol-1', 'scene r3', 'catalogue r2', 'live computation'])
    expect(provenanceItems({ operation: 'search_layouts', provenance: { ...provenance, execution_mode: 'cached' } } as unknown as Result, null))
      .toEqual(['evaluator ev-1', 'solar sol-1', 'search greedy-1', 'seed 7', 'cached result (exact same inputs)'])
  })
})
