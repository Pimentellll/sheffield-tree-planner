import type { Health, Job, Metric, Result } from '../api/types'
import { CURRENTNESS_LABEL, EXECUTION_MODE_LABEL, formatPence, formatValue, unitLabel, type Currentness } from './evaluation'

/**
 * Presentation helpers for planning-agent evidence (#74), written BEFORE Ben's agent-run API (#73).
 *
 * Deliberately defines NO agent-run wire types (run, status or event shapes). Those come only from
 * the backend-generated contract once #73 is agreed. Everything here works on the existing,
 * authoritative Job/Result/Health types, so it stays valid whatever the agent-run surface becomes:
 *
 * - `agentPanelState`: the explicit "agent unavailable" state required while no agent API exists.
 * - `evidenceChain`: the backend-only half of model → tool → Job → Result, with linkage checks.
 * - `narrativeView`: keeps model text as interpretation and flags every figure in it, so no
 *   model-generated number can be presented as a computed metric.
 */

// ---------------------------------------------------------------------------------------------
// Availability

export const AGENT_API_UNAVAILABLE_REASON =
  'This backend exposes no planning-agent API yet, so no agent history can be shown. Nothing on this panel is a model transcript. Manual evaluation is unaffected.'

/** Only one state exists until #73 lands; the union is extended from the generated contract, not here. */
export type AgentPanelState = {
  readonly kind: 'unavailable'
  readonly reason: string
  /** Whether the manual evaluate path the user can fall back to is offered by this backend. */
  readonly manualEvaluateAvailable: boolean
}

export function agentPanelState(health: Pick<Health, 'available_operations'> | null): AgentPanelState {
  return {
    kind: 'unavailable',
    reason: AGENT_API_UNAVAILABLE_REASON,
    manualEvaluateAvailable: health?.available_operations.includes('evaluate_layout') ?? false,
  }
}

// ---------------------------------------------------------------------------------------------
// Evidence chain (backend values only)

export type ChainJob = Pick<Job, 'job_id' | 'status' | 'run_id' | 'input_fingerprint' | 'scenario_id' | 'scenario_revision' | 'scope' | 'operation'>
export type ChainResult = Pick<Result, 'run_id' | 'source_job_id' | 'input_fingerprint' | 'scenario_id' | 'scenario_revision' | 'scope' | 'operation' | 'metrics' | 'limitations'> & {
  readonly provenance: Pick<Result['provenance'], 'execution_mode'>
  readonly layouts: ReadonlyArray<Pick<Result['layouts'][number], 'cost_pence' | 'selected'>>
  readonly missing_metrics: ReadonlyArray<Pick<Result['missing_metrics'][number], 'metric_id' | 'case_id' | 'reason'>>
}

export interface EvidenceStep {
  readonly kind: 'scenario' | 'operation' | 'job' | 'result' | 'currentness' | 'metric' | 'missing-metric' | 'cost' | 'limitation'
  readonly label: string
  readonly value: string
}

export type EvidenceChain =
  | { readonly ok: true; readonly currentness: Currentness; readonly steps: readonly EvidenceStep[] }
  | { readonly ok: false; readonly problems: readonly string[] }

/** Why a Job and Result cannot be shown as one evidence chain. Empty when they are linked. */
export function linkageProblems(job: ChainJob, result: ChainResult): string[] {
  const problems: string[] = []
  if (job.status !== 'completed') problems.push(`Job ${job.job_id} is ${job.status}, not completed.`)
  if (job.run_id !== result.run_id) problems.push(`Job ${job.job_id} names run ${job.run_id ?? 'none'}, not ${result.run_id}.`)
  if (result.source_job_id !== job.job_id) problems.push(`Result ${result.run_id} was produced by job ${result.source_job_id}, not ${job.job_id}.`)
  if (result.input_fingerprint !== job.input_fingerprint) problems.push(`Result ${result.run_id} input fingerprint differs from job ${job.job_id}.`)
  if (result.operation !== job.operation) problems.push(`Result operation ${result.operation} differs from job operation ${job.operation}.`)
  if (result.scenario_id !== job.scenario_id || result.scenario_revision !== job.scenario_revision || result.scope !== job.scope) {
    problems.push(`Result ${result.run_id} describes a different scenario revision than job ${job.job_id}.`)
  }
  return problems
}

/** A metric value in its unit. Money is converted from integer pence exactly once, here. */
export function metricText(metric: Pick<Metric, 'value' | 'unit'>): string {
  if (metric.unit === 'GBP_pence') return Number.isSafeInteger(metric.value) ? formatPence(metric.value) : `${formatValue(metric.value)} ${unitLabel(metric.unit)}`
  return `${formatValue(metric.value)} ${unitLabel(metric.unit)}`
}

/**
 * The backend-only evidence chain for one Job and its Result. `currentness` must come from the
 * workspace's existing guard (`Workspace.currentness`), so this never decides CURRENT on its own.
 * Returns problems instead of steps when the Result does not belong to the Job; the caller must
 * then show nothing from the Result.
 */
export function evidenceChain(job: ChainJob, result: ChainResult, currentness: Currentness): EvidenceChain {
  const problems = linkageProblems(job, result)
  if (problems.length) return { ok: false, problems }
  const steps: EvidenceStep[] = [
    { kind: 'scenario', label: 'Scenario', value: `${result.scope} ${result.scenario_id} revision ${result.scenario_revision}` },
    { kind: 'operation', label: 'Operation', value: result.operation },
    { kind: 'job', label: 'Job', value: job.job_id },
    { kind: 'result', label: 'Result', value: `${result.run_id} · ${EXECUTION_MODE_LABEL[result.provenance.execution_mode]}` },
    { kind: 'currentness', label: 'Status', value: CURRENTNESS_LABEL[currentness].label },
    ...result.metrics.map((m): EvidenceStep => ({ kind: 'metric', label: `${m.metric_id} (${m.case_id})`, value: metricText(m) })),
    ...result.missing_metrics.map((m): EvidenceStep => ({ kind: 'missing-metric', label: `${m.metric_id} (${m.case_id})`, value: `Not computed: ${m.reason}` })),
    ...result.layouts.filter(l => l.selected).map((l): EvidenceStep => ({ kind: 'cost', label: 'Cost of selected layout', value: formatPence(l.cost_pence) })),
    ...result.limitations.map((text): EvidenceStep => ({ kind: 'limitation', label: 'Limitation', value: text })),
  ]
  return { ok: true, currentness, steps }
}

// ---------------------------------------------------------------------------------------------
// Untrusted model narrative

export const MODEL_INTERPRETATION_LABEL = 'Model interpretation, not a computed result'

export type FigureKind = 'temperature' | 'percent' | 'money' | 'shade_m2_h' | 'energy_kWh' | 'area_m2'

/**
 * - `unsupported`: no registered operation computes this kind of quantity (for example °C).
 * - `unverified`: the kind is computable, but the figure equals no value in the given Result.
 * - `matches-result`: equals (to the precision written) a value in the given Result. It is still
 *   model text; the authoritative number is the metric card, never the narrative.
 */
export type FigureStatus = 'unsupported' | 'unverified' | 'matches-result'

export interface NarrativeFigure {
  readonly text: string
  readonly index: number
  readonly kind: FigureKind
  readonly status: FigureStatus
}

export interface NarrativeView {
  readonly label: typeof MODEL_INTERPRETATION_LABEL
  readonly text: string
  readonly figures: readonly NarrativeFigure[]
  /** True when any figure is not traceable to the given Result; the UI should warn. */
  readonly needsWarning: boolean
}

type NarrativeEvidence = Pick<ChainResult, 'metrics' | 'layouts'>

const NUMBER = String.raw`[-−]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?`
const UNIT = String.raw`°\s?[CF]\b|degrees?\s+(?:celsius|fahrenheit|C|F)\b|%|per\s?cent\b|m²·h|m2·h|m²\s?h\b|m2\s?h\b|m2_h\b|square[- ]metre[- ]hours?\b|kWh\b|m²|m2\b|pounds?\b|GBP\b|pence\b`
const FIGURE = new RegExp(String.raw`(£\s?)?(${NUMBER})\s?(${UNIT})?`, 'gi')

const decimals = (numberText: string) => numberText.split('.')[1]?.length ?? 0
const parseNumber = (numberText: string) => Number(numberText.replace(/−/g, '-').replace(/,/g, ''))
/** Half a unit in the last written decimal place: "12.3" may round any value in [12.25, 12.35]. */
const writtenTolerance = (numberText: string) => 0.5 * 10 ** -decimals(numberText)

function kindOf(pound: boolean, unit: string): { kind: FigureKind; pence: boolean } | null {
  const u = unit.toLowerCase().replace(/\s+/g, ' ')
  if (pound || u.startsWith('pound') || u === 'gbp') return { kind: 'money', pence: false }
  if (u === 'pence') return { kind: 'money', pence: true }
  if (u.startsWith('°') || u.startsWith('degree')) return { kind: 'temperature', pence: false }
  if (u === '%' || u.startsWith('per')) return { kind: 'percent', pence: false }
  if (u === 'kwh') return { kind: 'energy_kWh', pence: false }
  if (u === 'm²' || u === 'm2') return { kind: 'area_m2', pence: false }
  if (u) return { kind: 'shade_m2_h', pence: false }
  return null
}

const near = (a: number, b: number, tolerance: number) => Math.abs(a - b) <= tolerance + 1e-9

function statusOf(kind: FigureKind, value: number, tolerance: number, inPence: boolean, evidence: NarrativeEvidence | null): FigureStatus {
  // No registered operation computes air/surface temperature or a percentage.
  if (kind === 'temperature' || kind === 'percent') return 'unsupported'
  if (!evidence) return 'unverified'
  if (kind === 'money') {
    const pence = inPence ? value : value * 100
    const penceTolerance = inPence ? tolerance : tolerance * 100
    const candidates = [...evidence.layouts.map(l => l.cost_pence), ...evidence.metrics.filter(m => m.unit === 'GBP_pence').map(m => m.value)]
    return candidates.some(c => near(pence, c, penceTolerance)) ? 'matches-result' : 'unverified'
  }
  const unit: Metric['unit'] = kind === 'shade_m2_h' ? 'm2_h' : kind === 'energy_kWh' ? 'kWh' : 'm2'
  return evidence.metrics.some(m => m.unit === unit && near(value, m.value, tolerance)) ? 'matches-result' : 'unverified'
}

/**
 * Find every quantity with a unit or £ sign in model text and say whether the given Result backs
 * it. Bare numbers ("3 trees", "revision 2") are not quantities and are left alone. Pass `null`
 * evidence when no validated Result is attached: every computable figure is then unverified.
 */
export function narrativeFigures(text: string, evidence: NarrativeEvidence | null): NarrativeFigure[] {
  const figures: NarrativeFigure[] = []
  for (const match of text.matchAll(FIGURE)) {
    const [whole, pound, numberText, unit] = match
    const kind = kindOf(Boolean(pound), unit ?? '')
    if (!kind) continue
    const value = parseNumber(numberText)
    if (!Number.isFinite(value)) continue
    figures.push({
      text: whole.trim(),
      index: match.index ?? 0,
      kind: kind.kind,
      status: statusOf(kind.kind, value, writtenTolerance(numberText), kind.pence, evidence),
    })
  }
  return figures
}

/** Model prose packaged for display as interpretation, with its figures checked against the Result. */
export function narrativeView(text: string, evidence: NarrativeEvidence | null): NarrativeView {
  const figures = narrativeFigures(text, evidence)
  return { label: MODEL_INTERPRETATION_LABEL, text, figures, needsWarning: figures.some(f => f.status !== 'matches-result') }
}
