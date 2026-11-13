import type { EvaluatedLayout, Metric, Result, Scenario } from '../api/types'
import type { JobTone } from './evaluation'

export type ProofStatus = 'not-claimed' | 'proof-record-present' | 'claimed-without-proof'

export interface OutcomeView {
  readonly title: string
  readonly detail: string
  readonly tone: JobTone
  readonly proof: ProofStatus
}

/**
 * Wording for each analytical outcome. A heuristic miss is never presented as proof; "proven"
 * is only shown when the backend attached a finite-model proof record.
 */
export function outcomeView(result: Pick<Result, 'analytical_outcome' | 'finite_model_proof'>): OutcomeView {
  const proof = result.finite_model_proof
  switch (result.analytical_outcome) {
    case 'feasible_candidate':
      return { title: 'Feasible candidate found', detail: 'The backend returned at least one layout it marked feasible. Check each layout\'s constraint records below.', tone: 'success', proof: 'not-claimed' }
    case 'feasible_zero_planting':
      return { title: 'Planting nothing is the feasible answer', detail: 'Under the accepted constraints the backend selected no new trees. This is a result, not an error.', tone: 'neutral', proof: 'not-claimed' }
    case 'no_eligible_candidates':
      return { title: 'No eligible candidate positions', detail: 'The candidate catalogue had no position allowed by the accepted constraints and site evidence.', tone: 'warning', proof: 'not-claimed' }
    case 'search_exhausted_without_target':
      return { title: 'Target not met by this search', detail: 'The search finished without reaching the target. This is not a proof that no layout can meet it.', tone: 'warning', proof: 'not-claimed' }
    case 'proven_infeasible_finite_model':
      return proof
        ? { title: 'Proven infeasible within the finite candidate model', detail: `Proof method ${proof.method}, evidence ${proof.evidence_ref}. It covers only the finite candidate model, not every possible position on site.`, tone: 'danger', proof: 'proof-record-present' }
        : { title: 'Infeasibility claimed without a proof record', detail: 'The result says "proven" but carries no finite-model proof. Treat it as unverified.', tone: 'danger', proof: 'claimed-without-proof' }
    case 'comparison_completed':
      return { title: 'Comparison completed', detail: 'See the comparison panel.', tone: 'neutral', proof: 'not-claimed' }
  }
}

export interface ObjectiveView { readonly text: string; readonly target: string | null }

export function objectiveView(scenario: Pick<Scenario, 'input'>): ObjectiveView {
  const o = scenario.input.objective
  if (o.kind === 'minimise_cost_for_target') {
    return { text: `Least cost to reach a target (${o.quantity_kind}, case ${o.primary_case_id})`, target: o.target_gain_m2_h == null ? 'target not set' : `${o.target_gain_m2_h} m²·h` }
  }
  return { text: `Most shade within budget (${o.quantity_kind}, case ${o.primary_case_id})`, target: null }
}

export interface LayoutRow {
  readonly layoutId: string
  readonly revision: number
  readonly role: EvaluatedLayout['role']
  readonly selected: boolean
  readonly treeCount: number
  readonly costPence: number
  /** Present only when the run's own scenario snapshot is known. */
  readonly budgetPence: number | null
  readonly maxTreeCount: number | null
  readonly feasibility: EvaluatedLayout['feasibility']
  readonly reasons: readonly string[]
  readonly metric: Metric | null
  readonly constraints: Result['constraints']
  readonly counts: { readonly pass: number; readonly fail: number; readonly unknown: number }
  readonly placements: EvaluatedLayout['layout']['placements']
}

const ROLE_ORDER: Record<EvaluatedLayout['role'], number> = { baseline: 0, reference: 1, alternative: 2 }

/** One row per evaluated layout, with its own metric for the primary case and its own constraint records. */
export function layoutRows(result: Result, inputScenario: Pick<Scenario, 'input'> | null): LayoutRow[] {
  const primaryCase = inputScenario?.input.objective.primary_case_id ?? null
  return [...result.layouts]
    .sort((a, b) => ROLE_ORDER[a.role] - ROLE_ORDER[b.role] || Number(b.selected) - Number(a.selected))
    .map(l => {
      const id = l.layout.layout_id
      const metrics = result.metrics.filter(m => m.layout_id === id && m.metric_id === 'additional_shade')
      const constraints = result.constraints.filter(c => c.layout_id === id)
      const counts = { pass: 0, fail: 0, unknown: 0 }
      constraints.forEach(c => { counts[c.status] += 1 })
      return {
        layoutId: id,
        revision: l.layout.revision,
        role: l.role,
        selected: l.selected,
        treeCount: l.tree_count,
        costPence: l.cost_pence,
        budgetPence: inputScenario?.input.constraints.budget_pence ?? null,
        maxTreeCount: inputScenario?.input.constraints.max_tree_count ?? null,
        feasibility: l.feasibility,
        reasons: l.reasons,
        metric: metrics.find(m => m.case_id === primaryCase) ?? metrics[0] ?? null,
        constraints,
        counts,
        placements: l.layout.placements,
      }
    })
}

export const ROLE_LABEL: Record<EvaluatedLayout['role'], string> = {
  baseline: 'Baseline (existing)',
  reference: 'Reference layout',
  alternative: 'Alternative',
}

/** Spend relative to budget, in words, using only the two returned integers. */
export function spendText(row: Pick<LayoutRow, 'costPence' | 'budgetPence'>, format: (p: number) => string): string {
  if (row.budgetPence === null) return `${format(row.costPence)} (budget unknown for this run)`
  return `${format(row.costPence)} of ${format(row.budgetPence)}`
}
