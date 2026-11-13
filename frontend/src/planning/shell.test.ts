import { describe, expect, it } from 'vitest'
import type { Result, Scenario } from '../api/types'
import {
  dataPillLabel, draftBannerText, formatPounds, headerStatus, headlineMetric, latestEvaluation, layoutsFeasible, provenanceItems, provenanceStatus, resultSummary, scenarioSummary,
} from './shell'

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
  const base = { connected: true, connecting: false, revision: 4, draftDirty: false, activeJob: null, jobStatusLost: false, evaluationCurrentness: 'current' as const }
  it('says there is no accepted scenario when offline', () => {
    expect(headerStatus({ ...base, connected: false })).toEqual({ label: 'NO ACCEPTED SCENARIO', tone: 'muted' })
  })
  it('says CONNECTING, not "no accepted scenario", while (re)connecting (-51 C)', () => {
    expect(headerStatus({ ...base, connected: false, connecting: true })).toEqual({ label: 'REV 4 · CONNECTING', tone: 'muted' })
    expect(headerStatus({ ...base, connected: false, connecting: true, revision: null })).toEqual({ label: 'CONNECTING', tone: 'muted' })
    expect(dataPillLabel(false, 'synthetic_test', true).label).toBe('CONNECTING…')
  })
  it('names a running job before anything else', () => {
    expect(headerStatus({ ...base, draftDirty: true, activeJob: { status: 'running', operation: 'search_layouts', scenario_revision: 4 } }).label).toBe('REV 4 · SEARCH RUNNING')
    expect(headerStatus({ ...base, activeJob: { status: 'queued', operation: 'evaluate_layout', scenario_revision: 4 } }).label).toBe('REV 4 · EVALUATION QUEUED')
  })
  it('labels a job with its own revision when the head has moved on', () => {
    expect(headerStatus({ ...base, revision: 6, activeJob: { status: 'running', operation: 'evaluate_layout', scenario_revision: 4 } }))
      .toEqual({ label: 'REV 4 EVALUATION RUNNING · HEAD IS REV 6', tone: 'warn' })
  })
  it('never shows a job as running once polling it failed (-51 #3)', () => {
    expect(headerStatus({ ...base, jobStatusLost: true, activeJob: { status: 'running', operation: 'evaluate_layout', scenario_revision: 4 } }))
      .toEqual({ label: 'REV 4 EVALUATION · STATUS UNKNOWN', tone: 'warn' })
  })
  it('ignores a finished job', () => {
    expect(headerStatus({ ...base, activeJob: { status: 'cancelled', operation: 'search_layouts', scenario_revision: 4 } }).label).toBe('REV 4 · RESULT CURRENT')
  })
  it('flags an unaccepted draft as a warning', () => {
    expect(headerStatus({ ...base, draftDirty: true })).toEqual({ label: 'REV 4 + DRAFT · NOT ACCEPTED', tone: 'warn' })
  })
  it('is green only for a CURRENT result; otherwise it says there is none (-51 #4)', () => {
    expect(headerStatus(base)).toEqual({ label: 'REV 4 · RESULT CURRENT', tone: 'ok' })
    expect(headerStatus({ ...base, evaluationCurrentness: 'superseded' })).toEqual({ label: 'REV 4 · NO CURRENT RESULT', tone: 'warn' })
    expect(headerStatus({ ...base, evaluationCurrentness: 'not-selected' })).toEqual({ label: 'REV 4 · NO CURRENT RESULT', tone: 'warn' })
    expect(headerStatus({ ...base, evaluationCurrentness: null })).toEqual({ label: 'REV 4 · NO RESULT YET', tone: 'muted' })
  })
})

describe('dataPillLabel (-51 #5)', () => {
  it('never renders a raw enum or claims a real or field-verified site', () => {
    expect(dataPillLabel(true, 'synthetic_test')).toEqual({ label: 'SYNTHETIC TEST SITE · NOT SHEFFIELD', synthetic: true })
    const other = dataPillLabel(true, 'real_site' as never)
    expect(other).toEqual({ label: 'SITE DATA · SOURCE-BACKED, NOT FIELD-VERIFIED', synthetic: false })
    expect(other.label).not.toMatch(/REAL|VERIFIED ·|_/)
    expect(dataPillLabel(false, null).label).toBe('OFFLINE · NO DATA')
    expect(dataPillLabel(true, null).label).toBe('NO SITE')
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
  const budget = [{ path: 'constraints.budget_pence', before: 6_400_000, after: 7_500_000 }]
  it('lists the changed paths from the real diff', () => {
    const text = draftBannerText(3, budget, 3)
    expect(text.title).toBe('The result shown is for accepted revision 3, not your draft.')
    expect(text.detail).toContain('1 unaccepted change (constraints.budget_pence)')
  })
  it('never claims a result exists when there is none', () => {
    expect(draftBannerText(3, budget, null).title).toBe('No result describes your draft; accepted revision 3 has no evaluation yet.')
  })
  it('names the result\'s own revision when it is older than the head', () => {
    expect(draftBannerText(6, budget, 4).title).toBe('The result shown is for revision 4, not your draft or accepted revision 6.')
  })
  it('still warns when the change set cannot be built (invalid fields)', () => {
    expect(draftBannerText(3, [], 3).detail).toContain('unaccepted edits')
  })
})

describe('latestEvaluation', () => {
  const run = (op: 'evaluate_layout' | 'search_layouts', runId: string | null) => ({ job: { operation: op }, result: runId ? ({ run_id: runId } as Result) : null })
  it('skips failed jobs and other operations', () => {
    const runs = [run('evaluate_layout', null), run('search_layouts', 's'), run('evaluate_layout', 'r1')]
    expect(latestEvaluation(runs)?.result?.run_id).toBe('r1')
    expect(latestEvaluation([])).toBeNull()
  })
  it('prefers the backend-selected run over a late-arriving older one', () => {
    const runs = [run('evaluate_layout', 'old-late'), run('evaluate_layout', 'selected')]
    expect(latestEvaluation(runs, 'selected')?.result?.run_id).toBe('selected')
    expect(latestEvaluation(runs, 'not-stored')?.result?.run_id).toBe('old-late')
  })
})

describe('provenanceStatus (-51 #1)', () => {
  it('labels the strip with the same currentness as the card', () => {
    expect(provenanceStatus('current', 4)).toEqual({ label: 'CURRENT RUN', current: true })
    expect(provenanceStatus('superseded', 3)).toEqual({ label: 'REV 3 RUN · SUPERSEDED', current: false })
    expect(provenanceStatus('not-selected', 4)).toEqual({ label: 'REV 4 RUN · NOT CURRENT', current: false })
    expect(provenanceStatus('stale-draft', 4)).toEqual({ label: 'REV 4 RUN · STALE VS DRAFT', current: false })
  })
})

describe('provenanceItems', () => {
  it('uses the run snapshot revisions and adds search version and seed only for searches', () => {
    expect(provenanceItems({ operation: 'evaluate_layout', provenance } as unknown as Result, scenario, null))
      .toEqual(['evaluator ev-1', 'solar sol-1', 'scene r3', 'catalogue r2', 'live computation'])
    expect(provenanceItems({ operation: 'search_layouts', provenance: { ...provenance, execution_mode: 'cached' } } as unknown as Result, null, null))
      .toEqual(['evaluator ev-1', 'solar sol-1', 'search greedy-1', 'seed 7', 'cached result (exact same inputs)'])
  })
  it('reports how the job was delivered, not the stored run\'s original mode (-51 #2)', () => {
    const items = provenanceItems({ operation: 'evaluate_layout', provenance } as unknown as Result, null, { execution_mode: 'cached' })
    expect(items).toContain('cached result (exact same inputs)')
    expect(items).toContain('originally live computation')
    expect(items).not.toContain('live computation')
  })
})

describe('resultSummary (compact card)', () => {
  const m = (metric_id: string, case_id: string, value: number, target_id: string | null = null) => ({ metric_id, case_id, value, target_id, unit: 'm2_h' })
  const result = {
    layouts: [{ tree_count: 2, cost_pence: 20_000 }],
    metrics: [m('additional_shade', 'summer', 23, 't1'), m('additional_shade', 'summer', 4.75, 't2'), m('winter_sun_loss', 'winter', 4.35)],
    constraints: [{ rule: 'winter loss:aggregate', case_id: 'winter', status: 'pass' }],
  } as unknown as Result
  const snapshot = { input: { constraints: { budget_pence: 20_000, winter_limits: [{ case_id: 'winter', maximum_loss_m2_h: 100, target_id: null }, { case_id: 'winter', maximum_loss_m2_h: 7, target_id: 't1' }] } } } as unknown as Scenario
  it('takes every figure from the stored result and the run\'s own snapshot', () => {
    expect(resultSummary(result, snapshot, { metric_id: 'additional_shade', case_id: 'summer' })).toEqual({
      treeCount: 2, costPence: 20_000, budgetPence: 20_000,
      winter: { value: 4.35, unit: 'm2_h', caseId: 'winter', limit: 100, status: 'pass' },
      targets: [{ targetId: 't1', value: 23 }, { targetId: 't2', value: 4.75 }],
    })
  })
  it('reports no winter verdict without a backend constraint record, and no budget without a snapshot', () => {
    const s = resultSummary({ ...result, constraints: [] } as unknown as Result, null, null)
    expect(s.winter?.status).toBeNull()
    expect(s.winter?.limit).toBeNull()
    expect(s.budgetPence).toBeNull()
    expect(s.targets).toEqual([])
  })
  it('shows no per-target bars for a single target', () => {
    const one = { ...result, metrics: [m('additional_shade', 'summer', 23, 't1')] } as unknown as Result
    expect(resultSummary(one, snapshot, { metric_id: 'additional_shade', case_id: 'summer' }).targets).toEqual([])
  })
})

describe('resultSummary winter matching (-51 review of #88, item 3)', () => {
  const m = (case_id: string, value: number, target_id: string | null) => ({ metric_id: 'winter_sun_loss', case_id, value, target_id, unit: 'm2_h' })
  const snapshot = { input: { constraints: { budget_pence: 1, winter_limits: [{ case_id: 'w', maximum_loss_m2_h: 100, target_id: null }, { case_id: 'w', maximum_loss_m2_h: 7, target_id: 't1' }] } } } as unknown as Scenario
  it('uses the aggregate limit and the backend rule id for the aggregate metric, not a per-target record', () => {
    const r = { layouts: [], metrics: [m('w', 9, 't1'), m('w', 4, null)], constraints: [{ rule: 'winter loss:t1', case_id: 'w', status: 'fail' }, { rule: 'winter loss:aggregate', case_id: 'w', status: 'pass' }] } as unknown as Result
    expect(resultSummary(r, snapshot, null).winter).toEqual({ value: 4, unit: 'm2_h', caseId: 'w', limit: 100, status: 'pass' })
  })
  it('matches a single per-target metric to its own target limit and record', () => {
    const r = { layouts: [], metrics: [m('w', 9, 't1')], constraints: [{ rule: 'winter loss:t1', case_id: 'w', status: 'fail' }] } as unknown as Result
    expect(resultSummary(r, snapshot, null).winter).toEqual({ value: 9, unit: 'm2_h', caseId: 'w', limit: 7, status: 'fail' })
  })
  it('ignores a record whose rule merely mentions winter', () => {
    const r = { layouts: [], metrics: [m('w', 4, null)], constraints: [{ rule: 'winter_something_else', case_id: 'w', status: 'pass' }] } as unknown as Result
    expect(resultSummary(r, snapshot, null).winter?.status).toBeNull()
  })
})

describe('headlineMetric (-51 review of #88, item 1)', () => {
  const shade = (case_id: string, value: number, target_id: string | null = null) => ({ metric_id: 'additional_shade', case_id, value, target_id, unit: 'm2_h' })
  const snap = (primary: string) => ({ input: { objective: { primary_case_id: primary } } }) as unknown as Scenario
  it("takes the aggregate for the primary case of the run's own snapshot", () => {
    const r = { metrics: [shade('summer', 9, 't1'), shade('summer', 16)], missing_metrics: [] } as unknown as Result
    expect(headlineMetric(r, snap('summer')).metric?.value).toBe(16)
  })
  it("follows the run's snapshot when the head's primary case has changed since", () => {
    const r = { metrics: [shade('summer', 16), shade('winter', 4)], missing_metrics: [] } as unknown as Result
    expect(headlineMetric(r, snap('winter')).metric?.value).toBe(4)
  })
  it('reports "not computed" with the backend reasons instead of substituting another case or metric', () => {
    const r = { metrics: [shade('winter', 4), { ...shade('summer', 32), metric_id: 'weighted_shade_utility' }], missing_metrics: [{ metric_id: 'additional_shade', case_id: 'summer', reason: 'no receiver' }] } as unknown as Result
    const h = headlineMetric(r, snap('summer'))
    expect(h.metric).toBeNull()
    expect(h.missingReasons).toEqual(['additional_shade: no receiver'])
  })
  it('uses a lone per-target value, but not when several targets make it ambiguous', () => {
    expect(headlineMetric({ metrics: [shade('s', 2, 'only')], missing_metrics: [] } as unknown as Result, snap('s')).metric?.value).toBe(2)
    expect(headlineMetric({ metrics: [shade('s', 2, 'a'), shade('s', 3, 'b')], missing_metrics: [] } as unknown as Result, snap('s')).metric).toBeNull()
  })
  it("has no headline when the run's snapshot is unknown", () => {
    expect(headlineMetric({ metrics: [shade('s', 2)], missing_metrics: [] } as unknown as Result, null)).toEqual({ metric: null, primaryCaseId: null, missingReasons: [] })
  })
})

describe('layoutsFeasible (-51 #6)', () => {
  it('derives evaluation feasibility from the layouts, since evaluate_layout reports comparison_completed', () => {
    expect(layoutsFeasible([{ feasibility: 'feasible' }])).toBe(true)
    expect(layoutsFeasible([{ feasibility: 'feasible' }, { feasibility: 'infeasible' }])).toBe(false)
    expect(layoutsFeasible([{ feasibility: 'not_evaluated' }] as never)).toBeNull()
    expect(layoutsFeasible([])).toBeNull()
  })
})
