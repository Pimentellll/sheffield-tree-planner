import type { Delivery, Job, Result, Scenario, SiteBundle } from '../api/types'
import { TERMINAL_JOB_STATES } from '../api/client'
import { objectiveView } from './alternatives'
import { EXECUTION_MODE_LABEL, formatPence, type Currentness, type FieldChange } from './evaluation'

/**
 * Presentation helpers for the Vision v2 application shell (header status, scenario strip,
 * draft banner, provenance strip). Every value comes from the accepted Scenario, the active Job or
 * a stored Result; nothing here invents a figure or upgrades a state.
 */

export type ShellTone = 'ok' | 'warn' | 'progress' | 'muted'

export interface HeaderStatus { readonly label: string; readonly tone: ShellTone }

export interface HeaderStatusInput {
  readonly connected: boolean
  /** The connection is being (re)established; a previously loaded scenario may still be shown. */
  readonly connecting: boolean
  /** Revision of the accepted head scenario, or null when none is loaded. */
  readonly revision: number | null
  readonly draftDirty: boolean
  readonly activeJob: Pick<Job, 'status' | 'operation' | 'scenario_revision'> | null
  /** True when polling the active job failed, so its real status is unknown. */
  readonly jobStatusLost: boolean
  /** Currentness of the latest stored evaluation result, or null when there is none. */
  readonly evaluationCurrentness: Currentness | null
}

const OPERATION_WORD: Record<Job['operation'], string> = {
  evaluate_layout: 'EVALUATION',
  search_layouts: 'SEARCH',
  compare_locations: 'COMPARISON',
  compare_scenarios: 'COMPARISON',
}

/**
 * The one status pill in the header, in priority order: a job whose status is unknown, a running
 * job (labelled with ITS revision), an unaccepted draft, then the state of the shown result. Only a
 * CURRENT result earns the green tone.
 */
export function headerStatus({ connected, connecting, revision, draftDirty, activeJob, jobStatusLost, evaluationCurrentness }: HeaderStatusInput): HeaderStatus {
  if (connecting) return { label: revision === null ? 'CONNECTING' : `REV ${revision} · CONNECTING`, tone: 'muted' }
  if (!connected || revision === null) return { label: 'NO ACCEPTED SCENARIO', tone: 'muted' }
  const rev = `REV ${revision}`
  if (activeJob && !TERMINAL_JOB_STATES.has(activeJob.status)) {
    const word = OPERATION_WORD[activeJob.operation] ?? 'JOB'
    if (jobStatusLost) return { label: `REV ${activeJob.scenario_revision} ${word} · STATUS UNKNOWN`, tone: 'warn' }
    const work = `${word} ${activeJob.status.toUpperCase()}`
    return activeJob.scenario_revision === revision
      ? { label: `${rev} · ${work}`, tone: 'progress' }
      : { label: `REV ${activeJob.scenario_revision} ${work} · HEAD IS REV ${revision}`, tone: 'warn' }
  }
  if (draftDirty) return { label: `${rev} + DRAFT · NOT ACCEPTED`, tone: 'warn' }
  if (evaluationCurrentness === 'current') return { label: `${rev} · RESULT CURRENT`, tone: 'ok' }
  if (evaluationCurrentness === null) return { label: `${rev} · NO RESULT YET`, tone: 'muted' }
  return { label: `${rev} · NO CURRENT RESULT`, tone: 'warn' }
}

/** The data-kind pill. Never claims a site is real or field-verified. */
export function dataPillLabel(connected: boolean, siteKind: SiteBundle['site_kind'] | null, connecting = false): { label: string; synthetic: boolean } {
  if (connecting) return { label: 'CONNECTING…', synthetic: siteKind !== null && siteKind === 'synthetic_test' }
  if (!connected) return { label: 'OFFLINE · NO DATA', synthetic: true }
  if (siteKind === null) return { label: 'NO SITE', synthetic: true }
  if (siteKind === 'synthetic_test') return { label: 'SYNTHETIC TEST SITE · NOT SHEFFIELD', synthetic: true }
  return { label: 'SITE DATA · SOURCE-BACKED, NOT FIELD-VERIFIED', synthetic: false }
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

/**
 * Banner text while the draft differs from the accepted revision (C02). `shownRevision` is the
 * scenario revision of the evaluation result on screen, or null when there is none; the banner
 * never claims a result exists for a revision that has none.
 */
export function draftBannerText(revision: number, changes: readonly FieldChange[], shownRevision: number | null): { title: string; detail: string } {
  const n = changes.length
  const what = n === 0 ? 'unaccepted edits' : `${n} unaccepted change${n === 1 ? '' : 's'} (${changes.map(c => c.path).join(', ')})`
  const title = shownRevision === null
    ? `No result describes your draft; accepted revision ${revision} has no evaluation yet.`
    : shownRevision === revision
      ? `The result shown is for accepted revision ${revision}, not your draft.`
      : `The result shown is for revision ${shownRevision}, not your draft or accepted revision ${revision}.`
  return {
    title,
    detail: `Your draft has ${what}. Nothing is saved or computed until you choose "Accept changes & evaluate", which saves a new revision and then evaluates it.`,
  }
}

type RunLike = { readonly job: Pick<Job, 'operation'>; readonly result: Result | null }

/**
 * The evaluation the result card shows, and every shell element describes: the run the backend
 * selected for the head revision when it is stored, otherwise the newest stored evaluation with a
 * result. Runs are kept in arrival order, so an older job that finishes late must not displace the
 * selected run.
 */
export function latestEvaluation<T extends RunLike>(runs: readonly T[], selectedRunId: string | null = null): T | null {
  const evaluations = runs.filter(r => r.job.operation === 'evaluate_layout' && r.result !== null)
  return (selectedRunId ? evaluations.find(r => r.result?.run_id === selectedRunId) : undefined) ?? evaluations[0] ?? null
}

/** Status label for the provenance strip; it describes the same run as the result card. */
export function provenanceStatus(currentness: Currentness, scenarioRevision: number): { label: string; current: boolean } {
  switch (currentness) {
    case 'current': return { label: 'CURRENT RUN', current: true }
    case 'stale-draft': return { label: `REV ${scenarioRevision} RUN · STALE VS DRAFT`, current: false }
    case 'not-selected': return { label: `REV ${scenarioRevision} RUN · NOT CURRENT`, current: false }
    case 'superseded': return { label: `REV ${scenarioRevision} RUN · SUPERSEDED`, current: false }
  }
}

/**
 * Provenance strip items for one stored Result. The mode is how the requesting Job was DELIVERED
 * (a cache hit is "cached" even though the stored Result was originally a live computation); the
 * original mode is added when it differs. Scene and catalogue revisions come from the scenario
 * snapshot the run was computed from, not from whatever site is loaded now.
 */
export function provenanceItems(
  result: Pick<Result, 'operation' | 'provenance'>,
  inputScenario: Pick<Scenario, 'input'> | null,
  delivery: Pick<Delivery, 'execution_mode'> | null,
): string[] {
  const p = result.provenance
  const items = [`evaluator ${p.evaluator_version}`, `solar ${p.solar_version}`]
  if (result.operation === 'search_layouts') items.push(`search ${p.search_version}`, `seed ${p.seed}`)
  if (inputScenario) items.push(`scene r${inputScenario.input.scene_revision}`, `catalogue r${inputScenario.input.candidate_catalogue_revision}`)
  const delivered = delivery?.execution_mode ?? p.execution_mode
  items.push(EXECUTION_MODE_LABEL[delivered].toLowerCase())
  if (delivered !== p.execution_mode) items.push(`originally ${EXECUTION_MODE_LABEL[p.execution_mode].toLowerCase()}`)
  return items
}

/**
 * Feasibility of an evaluation from its layouts. evaluate_layout reports analytical_outcome
 * "comparison_completed" (feasibility per layout), so the outcome alone cannot say.
 * false if any layout is infeasible, true only if every layout is feasible, otherwise null.
 */
export function layoutsFeasible(layouts: ReadonlyArray<Pick<Result['layouts'][number], 'feasibility'>>): boolean | null {
  if (layouts.length === 0) return null
  if (layouts.some(l => l.feasibility === 'infeasible')) return false
  return layouts.every(l => l.feasibility === 'feasible') ? true : null
}
