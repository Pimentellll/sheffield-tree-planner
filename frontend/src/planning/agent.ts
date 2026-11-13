import type { AgentRun, AgentStatus } from '../api/types'

export type Tone = 'success' | 'warning' | 'danger' | 'progress' | 'muted'

export interface View {
  readonly tone: Tone
  readonly title: string
  readonly detail: string
}

/** Whether the server will accept a run now. Never inferred: every field comes from /agent/status. */
export function availability(status: AgentStatus | null, statusError: string | null): View & { readonly available: boolean } {
  if (statusError) return { available: false, tone: 'danger', title: 'Agent status unavailable', detail: statusError }
  if (!status) return { available: false, tone: 'progress', title: 'Checking the planning agent…', detail: 'Asking the local backend whether a model is configured.' }
  if (!status.configured) return { available: false, tone: 'muted', title: 'Planning agent not configured', detail: status.reason ?? 'No local model is configured on this server. Manual evaluation, search and comparison still work.' }
  if (!status.reachable) return { available: false, tone: 'warning', title: 'Model service unreachable', detail: `${status.model} at ${status.model_base_url}: ${status.reason ?? 'no response'}. Manual workflows are unaffected.` }
  if (!status.model_listed) return { available: false, tone: 'warning', title: 'Model alias not served', detail: `${status.model} is not listed by the model service (serving: ${status.listed_models.join(', ') || 'nothing'}).` }
  return { available: true, tone: 'success', title: `Local model ready · ${status.model}`, detail: `Server-side tools: ${status.allowed_operations.join(', ')}. ${status.authority}` }
}

const RUN_VIEW: Record<AgentRun['status'], (run: AgentRun) => View> = {
  running: run => ({ tone: 'progress', title: run.stop_requested ? 'Stopping after the current step…' : 'Agent investigating…', detail: `${run.model_completions} model turn${run.model_completions === 1 ? '' : 's'} so far.` }),
  completed: run => ({ tone: 'success', title: 'Completed with verified backend evidence', detail: `Cited ${run.cited_run_ids.length} current run${run.cited_run_ids.length === 1 ? '' : 's'}; the summary below is generated from the stored results, not the model.` }),
  metadata_only: () => ({ tone: 'muted', title: 'Site metadata inspected', detail: 'No numerical result was computed.' }),
  draft_prepared: () => ({ tone: 'warning', title: 'Hypothetical draft prepared', detail: 'Not accepted and not computed. Review it in Proposal review.' }),
  needs_evidence: () => ({ tone: 'warning', title: 'No validated evidence', detail: 'The agent finished without a current backend result to cite.' }),
  failed: run => ({ tone: 'danger', title: 'Agent run failed safely', detail: `${run.reason ?? 'unknown reason'}. Nothing was accepted; any computed runs are listed below as uncited.` }),
  stopped: () => ({ tone: 'muted', title: 'Stopped', detail: 'The run stopped before a final answer. Nothing was accepted.' }),
  exhausted: () => ({ tone: 'warning', title: 'Action budget used up', detail: 'The agent reached its tool-call limit without a final answer.' }),
}

export function runView(run: AgentRun): View {
  return RUN_VIEW[run.status](run)
}

export const isRunning = (run: AgentRun | null) => run?.status === 'running'

/** Runs the tools computed that the accepted final answer did not cite (all of them on failure). */
export function uncitedRuns(run: AgentRun): string[] {
  return run.computed_run_ids.filter(id => !run.cited_run_ids.includes(id))
}

export const MAX_GOAL = 600

export function goalError(goal: string): string | null {
  if (!goal.trim()) return 'Describe what the agent should investigate.'
  if (goal.length > MAX_GOAL) return `Keep the goal under ${MAX_GOAL} characters (${goal.length}).`
  return null
}
