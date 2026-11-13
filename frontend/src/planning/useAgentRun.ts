import { useEffect, useMemo, useRef, useState } from 'react'
import {
  AGENT_RUN_STORAGE_KEY, applySnapshot, decodeStoredRun, encodeStoredRun, isReadableSnapshot, isTerminalPhase,
  restoredRunView, storedRunOf, supersededByHead, unavailableTransport, validateQuestion,
  type AgentAvailability, type AgentRunSnapshot, type AgentRunTransport, type AgentRunView, type AgentScenarioKey,
  type StoredAgentRun,
} from './agentRun'
import type { Workspace } from './useWorkspace'

export interface AgentRunController {
  /** Null while the first status() is in flight. */
  readonly availability: AgentAvailability | null
  readonly run: AgentRunView | null
  /** Available, an accepted scenario is loaded, no draft edits, no non-terminal run. */
  readonly canSubmit: boolean
  /** Why canSubmit is false, in plain words; null when it is true. */
  readonly blockedReason: string | null
  /** supersededByHead(run, current accepted head). */
  readonly headMoved: boolean
  submit(question: string): void
  stop(): void
  /** Re-query a run whose status is unknown. */
  recheck(): void
  /** Forget a terminal or unknown run. */
  clear(): void
}

export interface AgentRunOptions {
  /** Delay between get() polls of a non-terminal run. */
  readonly pollMs?: number
  /** A transport call with no reply within this time is treated as failed (status unknown). 0 disables. */
  readonly requestTimeoutMs?: number
  /** The feature selected on the map when submit() is called, if the host tracks one. Default null. */
  readonly selectedFeatureId?: string | null
  /** Request identity generator (tests inject a deterministic one). */
  readonly newRequestId?: () => string
}

export const AGENT_POLL_MS = 1500
export const AGENT_REQUEST_TIMEOUT_MS = 30_000

const message = (error: unknown) => (error instanceof Error ? error.message : String(error))
const defaultRequestId = () =>
  `agent-${typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function' ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`}`

function withTimeout<T>(call: () => Promise<T>, ms: number): Promise<T> {
  const pending = Promise.resolve().then(call) // a synchronous throw becomes a rejection
  if (!(ms > 0) || !Number.isFinite(ms)) return pending
  return new Promise<T>((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`no reply within ${Math.max(1, Math.round(ms / 1000))} s`)), ms)
    pending.then(v => { clearTimeout(timer); resolve(v) }, e => { clearTimeout(timer); reject(e) })
  })
}

// Session storage holds only what is needed to find a run again (see StoredAgentRun). Every access can throw
// (private mode, blocked site data, quota), so each is guarded: without storage a run simply does not survive
// a reload, and nothing else changes.
function sessionStore(): Storage | null {
  try { return typeof window !== 'undefined' ? window.sessionStorage : null } catch { return null }
}
/** The stored record, or null. A record that cannot be read as this version's is removed. */
function readStoredRun(): StoredAgentRun | null {
  try {
    const store = sessionStore()
    const raw = store ? store.getItem(AGENT_RUN_STORAGE_KEY) : null
    if (!store || raw === null) return null
    const record = decodeStoredRun(raw)
    if (!record) store.removeItem(AGENT_RUN_STORAGE_KEY)
    return record
  } catch { return null }
}
function writeStoredRun(record: StoredAgentRun): void {
  try { sessionStore()?.setItem(AGENT_RUN_STORAGE_KEY, encodeStoredRun(record)) } catch { /* not stored */ }
}
function removeStoredRun(): void {
  try { sessionStore()?.removeItem(AGENT_RUN_STORAGE_KEY) } catch { /* nothing to remove, or not removable */ }
}
const storedSignature = (run: StoredAgentRun) => `${run.requestId}\n${run.agentRunId ?? ''}`

const headKey = (ws: Workspace): AgentScenarioKey | null =>
  ws.scenario ? { scenario_id: ws.scenario.scenario_id, revision: ws.scenario.revision, scope: ws.scenario.scope } : null

function blockedBy(availability: AgentAvailability | null, ws: Workspace, run: AgentRunView | null): string | null {
  if (availability === null) return 'Checking whether the planning agent is connected.'
  if (availability.kind === 'unavailable') return availability.reason
  if (!ws.scenario) return 'No accepted scenario is loaded, so there is nothing for the agent to work on.'
  if (ws.draftDirty || ws.editPending) return 'You have edits that are not accepted yet. Accept or revert them first: the agent works only on the accepted scenario.'
  if (run && run.phase === 'status_unknown') return 'The status of the last agent run is unknown. Re-check it, or clear it, before asking again.'
  if (run && !isTerminalPhase(run.phase)) return 'An agent run is still in progress. Wait for it to finish or stop it.'
  return null
}

const startUnknown = (err: unknown) =>
  `The request may or may not have reached the server (${message(err)}). Re-check to send the same request again; the server is expected not to start a second run for the same request id.`
const getUnknown = (err: unknown) =>
  `The run's current status could not be read (${message(err)}). It may still be running on the server. Re-check to ask again.`
const cancelUnknown = (err: unknown) =>
  `The stop request may or may not have reached the server (${message(err)}). The run may still be going. Re-check to see its status.`
/** A start reply arrived but could not be applied (no usable run id, an unknown status word or a bad seq). */
const START_REPLY_UNREADABLE =
  'The server answered the request, but its reply could not be read (no usable run id or an unrecognised status). A run may or may not have started. Re-check to send the same request again; the server is expected not to start a second run for the same request id.'
/** A get or cancel reply arrived but could not be read at all. */
const REPLY_UNREADABLE =
  "The server's reply about this run could not be read (no usable run id or an unrecognised status). The run may still be going. Re-check to ask again."

interface Live {
  transport: AgentRunTransport
  pollMs: number
  timeoutMs: number
  ws: Workspace
  availability: AgentAvailability | null
  selectedFeatureId: string | null
  makeId: () => string
}

/**
 * Lifecycle of one planning-agent run against the accepted scenario. Every reply is applied only if it answers
 * the latest call for the current request (a call token and the requestId are checked before each state write),
 * and nothing is written after unmount. Unmounting stops polling; it does not cancel the run on the server.
 *
 * A run that has not ended is remembered in session storage by its request id and run id only. After a reload
 * or a remount, once the transport reports available, it is shown as 'status_unknown' and asked for again:
 * get() when a run id was received, otherwise start() with the same request id. Only that reply can set its
 * phase, steps, narrative and evidence. The record is removed when the run ends and on clear().
 */
export function useAgentRun(ws: Workspace, transport: AgentRunTransport = unavailableTransport, options: AgentRunOptions = {}): AgentRunController {
  const [availability, setAvailability] = useState<AgentAvailability | null>(null)
  const [run, setRun] = useState<AgentRunView | null>(null)

  const live = useRef<Live | null>(null)
  live.current = {
    transport,
    pollMs: options.pollMs ?? AGENT_POLL_MS,
    timeoutMs: options.requestTimeoutMs ?? AGENT_REQUEST_TIMEOUT_MS,
    ws,
    availability,
    selectedFeatureId: options.selectedFeatureId ?? null,
    makeId: options.newRequestId ?? defaultRequestId,
  }

  // Built once; reads only refs, so the returned callbacks are stable across renders.
  const [ops] = useState(() => {
    const alive = { current: true }
    const runRef: { current: AgentRunView | null } = { current: null }
    /** Bumped by every transport call, clear() and unmount; only the latest call may write. */
    const token = { current: 0 }
    let pollTimer: ReturnType<typeof setTimeout> | null = null
    const cfg = () => live.current!

    /** Request id and run id last written; a poll that changes neither does not touch storage. */
    let stored: string | null = null
    const remember = (next: AgentRunView | null) => {
      if (!next || isTerminalPhase(next.phase)) { stored = null; removeStoredRun(); return }
      const signature = storedSignature(next)
      if (signature === stored) return
      stored = signature
      writeStoredRun(storedRunOf(next))
    }
    const commit = (next: AgentRunView | null) => { runRef.current = next; remember(next); setRun(next) }
    const stopPolling = () => { if (pollTimer !== null) clearTimeout(pollTimer); pollTimer = null }

    const call = (
      requestId: string,
      op: (t: AgentRunTransport) => Promise<AgentRunSnapshot>,
      unknownText: (err: unknown) => string,
      isStart = false,
    ) => {
      stopPolling()
      token.current += 1
      const mine = token.current
      const current = () => alive.current && mine === token.current && runRef.current?.requestId === requestId
      const { transport: t, timeoutMs } = cfg()
      withTimeout(() => op(t), timeoutMs).then(
        snap => {
          const prev = runRef.current
          if (!current() || !prev) return
          const next = applySnapshot(prev, snap)
          // A start reply that cannot be applied (or leaves no run id) would otherwise leave the run in
          // 'submitting' with nothing to poll and no way out. A get/cancel reply that cannot be read at all is the
          // same. Both become status_unknown, so Re-check and Clear are offered. A merely stale (lower seq) or
          // foreign-run get/cancel reply is still dropped and polling continues.
          if ((isStart && (next === prev || !next.agentRunId)) || !isReadableSnapshot(snap)) {
            commit({ ...prev, phase: 'status_unknown', error: isStart ? START_REPLY_UNREADABLE : REPLY_UNREADABLE })
            return
          }
          commit(next)
          if (!isTerminalPhase(next.phase) && next.phase !== 'status_unknown' && next.agentRunId) schedulePoll(requestId)
        },
        err => {
          if (!current() || !runRef.current) return
          // Never 'failed' and never still 'running': the server may or may not have acted on the call.
          commit({ ...runRef.current, phase: 'status_unknown', error: unknownText(err) })
        },
      )
    }

    const schedulePoll = (requestId: string) => {
      stopPolling()
      pollTimer = setTimeout(() => {
        pollTimer = null
        const r = runRef.current
        if (!alive.current || !r || r.requestId !== requestId || !r.agentRunId || isTerminalPhase(r.phase) || r.phase === 'status_unknown') return
        const id = r.agentRunId
        call(requestId, t => t.get(id), getUnknown)
      }, cfg().pollMs)
    }

    const startCall = (view: AgentRunView) => {
      // ASSUMPTION for #73 (Ben to confirm): start() is idempotent on requestId, so re-sending the same
      // requestId after a lost reply returns the same run rather than creating a second one. A re-sent start
      // is never presented as certain: until the server answers, the run stays 'status_unknown'.
      const req = { requestId: view.requestId, question: view.question, scenario: view.scenario, selectedFeatureId: view.selectedFeatureId }
      call(view.requestId, t => t.start(req), startUnknown, true)
    }

    const requery = (r: AgentRunView) => {
      if (r.agentRunId) {
        const id = r.agentRunId
        call(r.requestId, t => t.get(id), getUnknown)
      } else {
        startCall(r) // same requestId, same question and scenario
      }
    }

    return {
      // Reading here also drops a stored record this version cannot read, whatever the transport says.
      mount: () => { alive.current = true; readStoredRun() },
      unmount: () => { alive.current = false; token.current += 1; stopPolling() },
      /** Called when the transport reports available. Does nothing if a run is already held. */
      restore: () => {
        if (!alive.current || runRef.current !== null) return
        const record = readStoredRun()
        if (!record) return
        const view = restoredRunView(record) // 'status_unknown': stored data never says a run is going
        stored = storedSignature(view)
        commit(view)
        requery(view)
      },
      submit: (text: string) => {
        const c = cfg()
        if (blockedBy(c.availability, c.ws, runRef.current) !== null) return
        const head = headKey(c.ws)
        const valid = validateQuestion(text)
        if (!head || !valid.ok) return
        const view: AgentRunView = {
          requestId: c.makeId(), agentRunId: null, phase: 'submitting', question: valid.question, scenario: head,
          selectedFeatureId: c.selectedFeatureId, steps: [], narrative: null, evidenceIds: [], outcome: null, error: null, lastSeq: 0,
        }
        commit(view) // synchronous: a second submit in the same tick sees a non-terminal run and is ignored
        startCall(view)
      },
      stop: () => {
        const r = runRef.current
        if (!r || !r.agentRunId || r.phase !== 'running') return
        const id = r.agentRunId
        call(r.requestId, t => t.cancel(id), cancelUnknown)
      },
      recheck: () => {
        const r = runRef.current
        if (!r || r.phase !== 'status_unknown') return
        requery(r)
      },
      clear: () => {
        const r = runRef.current
        if (!r || !(isTerminalPhase(r.phase) || r.phase === 'status_unknown')) return
        token.current += 1 // any late reply for this run is dropped
        stopPolling()
        commit(null)
      },
    }
  })

  useEffect(() => {
    ops.mount()
    return ops.unmount
  }, [ops])

  useEffect(() => {
    let cancelled = false
    setAvailability(null)
    withTimeout(() => transport.status(), live.current!.timeoutMs).then(
      value => {
        if (cancelled) return
        setAvailability(value)
        // Same batch as the availability update, so there is no moment at which a new request could be
        // submitted while a stored run is still waiting to be found. Unavailable: the record is left alone.
        if (value.kind === 'available') ops.restore()
      },
      err => { if (!cancelled) setAvailability({ kind: 'unavailable', reason: `The planning agent is unavailable: its status could not be read (${message(err)}).` }) },
    )
    return () => { cancelled = true }
  }, [transport, ops])

  const headId = ws.scenario?.scenario_id
  const headRevision = ws.scenario?.revision
  const headScope = ws.scenario?.scope
  const blockedReason = blockedBy(availability, ws, run)
  const headMoved = useMemo(
    () => (run && headId !== undefined && headRevision !== undefined && headScope !== undefined
      ? supersededByHead(run, { scenario_id: headId, revision: headRevision, scope: headScope })
      : false),
    [run, headId, headRevision, headScope],
  )

  return useMemo(() => ({
    availability, run, canSubmit: blockedReason === null, blockedReason, headMoved,
    submit: ops.submit, stop: ops.stop, recheck: ops.recheck, clear: ops.clear,
  }), [availability, run, blockedReason, headMoved, ops])
}
