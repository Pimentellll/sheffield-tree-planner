import type { Job, Result, Scenario } from '../api/types'
import { TERMINAL_JOB_STATES } from '../api/client'
import { objectiveView } from './alternatives'
import { EXECUTION_MODE_LABEL, formatPence, type Currentness, type FieldChange } from './evaluation'

/**
 * Presentation helpers for the Vision v2 application shell (header status, scenario strip,
 * draft banner, provenance strip). Every value comes from the accepted Scenario, the active Job or
 * a stored Result; nothing here invents a figure.
 */

export type ShellTone = 'ok' | 'warn' | 'progress' | 'muted'

export interface HeaderStatus { readonly label: string; readonly tone: ShellTone }

export interface HeaderStatusInput {
  readonly connected: boolean
  /** Revision of the accepted head scenario, or null when none is loaded. */
  readonly revision: number | null
  readonly draftDirty: boolean
  readonly activeJob: Pick<Job, 'status' | 'operation'> | null
  /** Currentness of the latest stored evaluation result, or null when there is none. */
  readonly evaluationCurrentness: Currentness | null
}

const OPERATION_WORD: Record<Job['operation'], string> = {
  evaluate_layout: 'EVALUATION',
  search_layouts: 'SEARCH',
  compare_locations: 'COMPARISON',
  compare_scenarios: 'COMPARISON',
}

/** The one status pill in the header. A running job wins, then an unaccepted draft. */
export function headerStatus({ connected, revision, draftDirty, activeJob, evaluationCurrentness }: HeaderStatusInput): HeaderStatus {
  if (!connected || revision === null) return { label: 'NO ACCEPTED SCENARIO', tone: 'muted' }
  const rev = `REV ${revision}`
  if (activeJob && !TERMINAL_JOB_STATES.has(activeJob.status)) {
    return { label: `${rev} · ${OPERATION_WORD[activeJob.operation] ?? 'JOB'} ${activeJob.status.toUpperCase()}`, tone: 'progress' }
  }
  if (draftDirty) return { label: `${rev} + DRAFT · NOT ACCEPTED`, tone: 'warn' }
  if (evaluationCurrentness === 'current') return { label: `${rev} · RESULT CURRENT`, tone: 'ok' }
  return { label: `${rev} · ACCEPTED`, tone: 'ok' }
}

/** Whole pounds without a ".00"; anything else keeps its exact pence. */
export function formatPounds(pence: number): string {
  const text = formatPence(pence)
  return Number.isSafeInteger(pence) && pence % 100 === 0 ? text.replace(/\.00$/, '') : text
}

export interface ScenarioSummary {
  readonly budget: string
  readonly basis: string
  readonly objective: string
  readonly maxTrees: string
  readonly exclusions: number
}

/** What the scenario strip shows: the accepted scenario's own fields, never a draft. */
export function scenarioSummary(scenario: Pick<Scenario, 'input'>): ScenarioSummary {
  const c = scenario.input.constraints
  return {
    budget: formatPounds(c.budget_pence),
    basis: c.budget_basis,
    objective: objectiveView(scenario).text,
    maxTrees: c.max_tree_count === null ? 'no limit' : String(c.max_tree_count),
    exclusions: c.excluded_region_ids.length,
  }
}

/** Banner text while the draft differs from the accepted revision (C02). */
export function draftBannerText(revision: number, changes: readonly FieldChange[]): { title: string; detail: string } {
  const n = changes.length
  const what = n === 0 ? 'unaccepted edits' : `${n} unaccepted change${n === 1 ? '' : 's'} (${changes.map(c => c.path).join(', ')})`
  return {
    title: `Results describe accepted revision ${revision}, not your draft.`,
    detail: `Your draft has ${what}. Nothing is saved or computed until you choose "Accept changes & evaluate", which saves a new revision and then evaluates it.`,
  }
}

type RunLike = { readonly job: Pick<Job, 'operation'>; readonly result: Result | null }

/** The newest stored evaluation that has a result (the one the result card shows). */
export function latestEvaluation<T extends RunLike>(runs: readonly T[]): T | null {
  return runs.find(r => r.job.operation === 'evaluate_layout' && r.result !== null) ?? null
}

/**
 * Provenance strip items for one stored Result. Scene and catalogue revisions come from the
 * scenario snapshot the run was computed from, not from whatever site is loaded now.
 */
export function provenanceItems(
  result: Pick<Result, 'operation' | 'provenance'>,
  inputScenario: Pick<Scenario, 'input'> | null,
): string[] {
  const p = result.provenance
  const items = [`evaluator ${p.evaluator_version}`, `solar ${p.solar_version}`]
  if (result.operation === 'search_layouts') items.push(`search ${p.search_version}`, `seed ${p.seed}`)
  if (inputScenario) items.push(`scene r${inputScenario.input.scene_revision}`, `catalogue r${inputScenario.input.candidate_catalogue_revision}`)
  items.push(EXECUTION_MODE_LABEL[p.execution_mode].toLowerCase())
  return items
}
