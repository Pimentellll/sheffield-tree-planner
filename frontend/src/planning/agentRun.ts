/**
 * Planning-agent run lifecycle: frontend-normalised types, a pure reducer and helpers. No React, no fetch.
 *
 * There is NO agent-run API on the backend yet; issue #73 (Ben) owns it. When its generated types land, ONE
 * adapter file implements `AgentRunTransport` by mapping that contract onto these types: start/get/cancel of a
 * run, the server's status words onto `AgentRunSnapshot.phase`, a per-run monotonic sequence onto `seq`, and
 * the client `requestId` as the request identity a lost start reply is re-sent with. No endpoint is named here.
 *
 * Model text (`narrative`) is untrusted. Nothing here parses numbers from it or from a snapshot; figures shown
 * as metrics, costs or constraints come only from workspace run records through `evidenceChain`.
 */

export type AgentAvailability =
  | { readonly kind: 'unavailable'; readonly reason: string }
  | { readonly kind: 'available'; readonly model: string | null }

export type AgentRunPhase = 'submitting' | 'running' | 'stop_requested' | 'completed' | 'stopped' | 'failed' | 'status_unknown'

export interface AgentScenarioKey { readonly scenario_id: string; readonly revision: number; readonly scope: string }

export interface AgentToolStep {
  readonly seq: number
  /** Registered operation name, verbatim from the server. */
  readonly tool: string
  readonly status: 'requested' | 'running' | 'completed' | 'failed'
  readonly jobId: string | null
  readonly runId: string | null
  readonly error: string | null
}

/** Frontend-normalised snapshot. NOT a wire type: a future adapter maps the #73 generated types onto it. */
export interface AgentRunSnapshot {
  readonly agentRunId: string
  /** Monotonic per run; a snapshot with a lower seq than the last applied is stale. */
  readonly seq: number
  readonly phase: 'running' | 'stop_requested' | 'completed' | 'stopped' | 'failed'
  readonly steps: readonly AgentToolStep[]
  /** Untrusted model text. */
  readonly narrative: string | null
  /** Job or run ids the server says the model cited. */
  readonly evidenceIds: readonly string[]
  /** Server outcome word, verbatim. */
  readonly outcome: string | null
  readonly error: string | null
}

export interface AgentRunView {
  /** Client-generated; stable across retries of the same submit. */
  readonly requestId: string
  /** Null until the server answers. */
  readonly agentRunId: string | null
  readonly phase: AgentRunPhase
  readonly question: string
  /** The accepted scenario the run was started against. */
  readonly scenario: AgentScenarioKey
  readonly selectedFeatureId: string | null
  readonly steps: readonly AgentToolStep[]
  readonly narrative: string | null
  readonly evidenceIds: readonly string[]
  readonly outcome: string | null
  readonly error: string | null
  readonly lastSeq: number
}

export interface AgentRunTransport {
  status(): Promise<AgentAvailability>
  start(req: { readonly requestId: string; readonly question: string; readonly scenario: AgentScenarioKey; readonly selectedFeatureId: string | null }): Promise<AgentRunSnapshot>
  get(agentRunId: string): Promise<AgentRunSnapshot>
  cancel(agentRunId: string): Promise<AgentRunSnapshot>
}

export const AGENT_TRANSPORT_UNAVAILABLE_REASON =
  'The planning agent is not connected: this build has no agent-run API to call, so no agent run can be started.'

const notConnected = () => Promise.reject(new Error(AGENT_TRANSPORT_UNAVAILABLE_REASON))

/** The only production transport today: reports unavailable and refuses every run operation. */
export const unavailableTransport: AgentRunTransport = {
  status: () => Promise.resolve({ kind: 'unavailable', reason: AGENT_TRANSPORT_UNAVAILABLE_REASON }),
  start: notConnected,
  get: notConnected,
  cancel: notConnected,
}

const TERMINAL: ReadonlySet<AgentRunPhase> = new Set<AgentRunPhase>(['completed', 'stopped', 'failed'])
const SNAPSHOT_PHASES: ReadonlySet<string> = new Set(['running', 'stop_requested', 'completed', 'stopped', 'failed'])

export function isTerminalPhase(phase: AgentRunPhase): boolean {
  return TERMINAL.has(phase)
}

/** The accepted head has moved past the revision the run was started against (same scenario and scope). */
export function supersededByHead(run: AgentRunView, head: AgentScenarioKey | null): boolean {
  if (!head) return false
  return head.scenario_id === run.scenario.scenario_id && head.scope === run.scenario.scope && head.revision > run.scenario.revision
}

/**
 * A snapshot this client can read at all: a non-empty agent run id, a finite seq and a known phase. An adapter
 * that passes through an unknown server word, an empty id or a missing reply produces an unreadable snapshot;
 * the hook reports that as status unknown rather than leaving the run waiting forever.
 */
export function isReadableSnapshot(snap: AgentRunSnapshot | null | undefined): snap is AgentRunSnapshot {
  return !!snap
    && typeof snap.agentRunId === 'string' && snap.agentRunId !== ''
    && typeof snap.seq === 'number' && Number.isFinite(snap.seq)
    && SNAPSHOT_PHASES.has(snap.phase)
}

/**
 * Apply a server snapshot to the run. Returns `run` unchanged when the snapshot is unreadable (empty agent run
 * id, non-finite seq or a phase this client does not know), belongs to another agent run, is older than the
 * last applied (`seq < lastSeq`; an equal seq is re-applied, so a re-check can restore a known phase), or would
 * move a terminal run back to non-terminal.
 */
export function applySnapshot(run: AgentRunView, snap: AgentRunSnapshot): AgentRunView {
  if (!isReadableSnapshot(snap)) return run
  if (run.agentRunId !== null && snap.agentRunId !== run.agentRunId) return run
  if (snap.seq < run.lastSeq) return run
  if (isTerminalPhase(run.phase) && !isTerminalPhase(snap.phase)) return run
  return {
    ...run,
    agentRunId: snap.agentRunId,
    phase: snap.phase,
    steps: snap.steps,
    narrative: snap.narrative,
    evidenceIds: snap.evidenceIds,
    outcome: snap.outcome,
    error: snap.error,
    lastSeq: snap.seq,
  }
}

export const MAX_QUESTION_LENGTH = 2000

export function validateQuestion(text: string): { readonly ok: true; readonly question: string } | { readonly ok: false; readonly reason: string } {
  const question = text.trim()
  if (!question) return { ok: false, reason: 'Write a question for the planning agent first.' }
  if (question.length > MAX_QUESTION_LENGTH) {
    return { ok: false, reason: `The question is ${question.length} characters; the limit is ${MAX_QUESTION_LENGTH}.` }
  }
  return { ok: true, question }
}

// ---------------------------------------------------------------------------------------------
// Finding a run again after a reload or a remount
//
// Only what the client itself chose is kept: the request identity, the run id once the server gave one, the
// question, the scenario key and the selected feature. Nothing the server reported (phase, steps, narrative,
// evidence, outcome) is stored, so a restored run can show those only from a fresh server reply.

export interface StoredAgentRun {
  readonly requestId: string
  readonly agentRunId: string | null
  readonly question: string
  readonly scenario: AgentScenarioKey
  readonly selectedFeatureId: string | null
}

/** Session-storage key. The version is part of the key and of the record; a record of another version is dropped. */
export const AGENT_RUN_STORAGE_VERSION = 1
export const AGENT_RUN_STORAGE_KEY = `tree-planner.agent-run.v${AGENT_RUN_STORAGE_VERSION}`

const MAX_STORED_ID_LENGTH = 200
const storedId = (v: unknown): v is string => typeof v === 'string' && v !== '' && v.length <= MAX_STORED_ID_LENGTH

/** Exactly the stored fields of a run (a view carries more; the rest is dropped). */
export function storedRunOf(run: StoredAgentRun): StoredAgentRun {
  return {
    requestId: run.requestId,
    agentRunId: run.agentRunId,
    question: run.question,
    scenario: { scenario_id: run.scenario.scenario_id, revision: run.scenario.revision, scope: run.scenario.scope },
    selectedFeatureId: run.selectedFeatureId,
  }
}

export function encodeStoredRun(record: StoredAgentRun): string {
  return JSON.stringify({ version: AGENT_RUN_STORAGE_VERSION, ...storedRunOf(record) })
}

/** Null for anything that is not exactly a record this version wrote: bad JSON, another version, a wrong field. */
export function decodeStoredRun(raw: string | null | undefined): StoredAgentRun | null {
  if (typeof raw !== 'string' || raw === '') return null
  let parsed: unknown
  try { parsed = JSON.parse(raw) } catch { return null }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return null
  const o = parsed as Record<string, unknown>
  if (o.version !== AGENT_RUN_STORAGE_VERSION) return null
  if (!storedId(o.requestId)) return null
  if (o.agentRunId !== null && !storedId(o.agentRunId)) return null
  if (o.selectedFeatureId !== null && !storedId(o.selectedFeatureId)) return null
  if (typeof o.question !== 'string') return null
  const question = validateQuestion(o.question)
  if (!question.ok || question.question !== o.question) return null
  const s = o.scenario
  if (!s || typeof s !== 'object' || Array.isArray(s)) return null
  const { scenario_id, revision, scope } = s as Record<string, unknown>
  if (!storedId(scenario_id) || !storedId(scope)) return null
  if (typeof revision !== 'number' || !Number.isFinite(revision)) return null
  return {
    requestId: o.requestId, agentRunId: o.agentRunId, question: o.question,
    scenario: { scenario_id, revision, scope }, selectedFeatureId: o.selectedFeatureId,
  }
}

export const RESTORED_RUN_NOTE =
  'This request was made before the page was reloaded or this panel was reopened. Nothing about its progress was kept here, so its status is being asked from the server. If no answer arrives, re-check.'

/**
 * The view of a stored run before the server has answered: always 'status_unknown', never 'running', with no
 * steps, narrative, evidence or outcome. The first applied snapshot replaces all of those (lastSeq is 0).
 */
export function restoredRunView(record: StoredAgentRun): AgentRunView {
  return {
    ...storedRunOf(record),
    phase: 'status_unknown', steps: [], narrative: null, evidenceIds: [], outcome: null, error: RESTORED_RUN_NOTE, lastSeq: 0,
  }
}
