import type { M2Session } from '../../../generated/contracts'
import type { Job, Result, ScenarioSelections } from '../../../generated/http'

export const sessionIdentity = (s: M2Session) => JSON.stringify(s)
export function currentMetric(s: M2Session, job: Job, result: Result, selections: ScenarioSelections): number | null {
  const selection = selections.evaluation.selection
  const current = selections.evaluation.current_job
  const d = job.delivery
  const ref = { scenario_id: job.scenario_id, revision: job.scenario_revision, scope: job.scope }
  const sameRef = (r: typeof ref) => r.scenario_id === ref.scenario_id && r.revision === ref.revision && r.scope === ref.scope
  if (!selection || !current || !d || job.status !== 'completed' || current.status !== 'completed' || job.superseded_by_revision !== null || current.superseded_by_revision !== null ||
      job.operation !== 'evaluate_layout' || job.view_slot !== 'evaluation' || job.scope !== 'accepted' ||
      s.scenario.scenario_id !== ref.scenario_id || s.scenario.revision !== ref.revision || s.scenario.scope !== ref.scope ||
      selection.accepted_job_id !== job.job_id || selection.selection_seq !== job.selection_seq || selection.view_slot !== job.view_slot || !sameRef(selection.scenario_ref) ||
      current.job_id !== job.job_id || current.selection_seq !== job.selection_seq || current.scenario_id !== job.scenario_id || current.scenario_revision !== job.scenario_revision || current.scope !== job.scope || current.input_fingerprint !== job.input_fingerprint || current.run_id !== job.run_id || current.view_slot !== job.view_slot || JSON.stringify(current.delivery) !== JSON.stringify(d) ||
      d.job_id !== job.job_id || d.selection_seq !== job.selection_seq || d.view_slot !== job.view_slot || d.scenario_id !== ref.scenario_id || d.scenario_revision !== ref.revision || d.scope !== ref.scope ||
      d.input_fingerprint !== job.input_fingerprint || d.run_id !== job.run_id || result.run_id !== d.run_id || result.source_job_id !== d.source_job_id ||
      result.input_fingerprint !== d.input_fingerprint || !sameRef(result.input_snapshot_ref) || result.scenario_id !== ref.scenario_id || result.scenario_revision !== ref.revision || result.scope !== ref.scope || result.operation !== 'evaluate_layout') return null
  const metric = result.metrics.find(m => m.metric_id === 'additional_shade' && m.quantity_kind === 'geometric' && m.unit === 'm2_h' && sameRef(m.scenario_ref) && m.layout_id === s.layout.layout_id)
  return metric && Number.isFinite(metric.value) ? metric.value : null
}
