import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ApiError, CanopyClient, TERMINAL_JOB_STATES } from '../api/client'
import { loadDevSession, verifyDeclaration, type DeclarationCheck, type DevSession } from '../api/session'
import type { Health, Job, Layout, Result, Scenario, SiteBundle, TreeProfile, Vec3 } from '../api/types'
import { buildCommit, classifyResult, evaluateRequest, refOf, samePosition, type Currentness } from './evaluation'

export type ConnectionState =
  | { readonly status: 'connecting' }
  | { readonly status: 'no-session'; readonly reason: string }
  | { readonly status: 'error'; readonly reason: string }
  | { readonly status: 'connected'; readonly health: Health }

export interface RunRecord {
  readonly job: Job
  readonly result: Result | null
}

export interface Workspace {
  readonly connection: ConnectionState
  readonly session: DevSession | null
  readonly declaration: DeclarationCheck | null
  readonly site: SiteBundle | null
  readonly profile: TreeProfile | null
  readonly scenario: Scenario | null
  readonly layout: Layout | null
  readonly placementId: string | null
  readonly committedPosition: Vec3 | null
  readonly draftPosition: Vec3 | null
  readonly draftDirty: boolean
  readonly activeJob: Job | null
  readonly runs: readonly RunRecord[]
  readonly currentRunId: string | null
  readonly busy: 'committing' | 'submitting' | 'cancelling' | null
  readonly notice: string | null
  readonly error: string | null
  readonly canEvaluate: boolean
  readonly currentness: (result: Result) => Currentness
  readonly setDraftPosition: (p: Vec3) => void
  readonly revertDraft: () => void
  readonly evaluate: () => Promise<void>
  readonly cancel: () => Promise<void>
  readonly reconnect: () => void
}

const POLL_MS = 150
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))
const message = (error: unknown) => (error instanceof Error ? error.message : String(error))
const newRequestId = () => `ui-${typeof crypto.randomUUID === 'function' ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`}`

const defaultClient = new CanopyClient()

export function useWorkspace(client: CanopyClient = defaultClient): Workspace {
  const [connection, setConnection] = useState<ConnectionState>({ status: 'connecting' })
  const [session, setSession] = useState<DevSession | null>(null)
  const [declaration, setDeclaration] = useState<DeclarationCheck | null>(null)
  const [site, setSite] = useState<SiteBundle | null>(null)
  const [profile, setProfile] = useState<TreeProfile | null>(null)
  const [scenario, setScenario] = useState<Scenario | null>(null)
  const [layout, setLayout] = useState<Layout | null>(null)
  const [draftPosition, setDraft] = useState<Vec3 | null>(null)
  const [activeJob, setActiveJob] = useState<Job | null>(null)
  const [runs, setRuns] = useState<RunRecord[]>([])
  const [currentRunId, setCurrentRunId] = useState<string | null>(null)
  const [busy, setBusy] = useState<Workspace['busy']>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [attempt, setAttempt] = useState(0)
  const scenarioRef = useRef<Scenario | null>(null)
  const activeJobId = useRef<string | null>(null)
  const alive = useRef(true)

  useEffect(() => { scenarioRef.current = scenario }, [scenario])
  useEffect(() => {
    alive.current = true
    return () => { alive.current = false }
  }, [])

  const placement = layout?.placements[0] ?? null
  const committedPosition = placement ? (placement.position_enu_m as Vec3) : null
  const draftDirty = Boolean(draftPosition && committedPosition && !samePosition(draftPosition, committedPosition))

  /** Re-read the backend's evaluation selection for the head revision. */
  const refreshSelection = useCallback(async (head: Scenario) => {
    const selections = await client.selections(refOf(head))
    if (!alive.current || scenarioRef.current?.revision !== head.revision) return
    setCurrentRunId(selections.evaluation.current_job?.run_id ?? null)
  }, [client])

  // Initial load: health, dev session, head scenario, site, layout and profile.
  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setConnection({ status: 'connecting' })
      setError(null)
      try {
        const health = await client.health()
        const dev = await loadDevSession()
        const params = new URLSearchParams(window.location.search)
        const scenarioId = params.get('scenario') ?? dev?.scenario_ref.scenario_id
        const knownRevision = Number(params.get('revision') ?? dev?.scenario_ref.revision ?? 1)
        if (!scenarioId) {
          if (!cancelled) setConnection({ status: 'no-session', reason: 'Backend is running, but no scenario was supplied. Start it with scripts/serve_reference.py or open ?scenario=<id>.' })
          return
        }
        const head = await client.latestScenario(scenarioId, knownRevision)
        const ref = head.input.proposed_layout_ref
        if (!ref) throw new Error('Scenario has no proposed layout')
        const [siteValue, layoutValue] = await Promise.all([
          client.site(head.input.site_id, head.input.scene_revision, head.input.semantic_revision),
          client.layout(ref.layout_id, ref.revision),
        ])
        const profileId = layoutValue.placements[0]?.profile_id
        if (!profileId) throw new Error('Layout has no placement to edit')
        const profileValue = await client.profile(profileId, head.input.profile_library_revision)
        const check = dev ? await verifyDeclaration(dev, siteValue) : null
        const selections = await client.selections(refOf(head))
        const selectedRun = selections.evaluation.current_job?.run_id ?? null
        const existing = selectedRun ? await client.result(selectedRun) : null
        if (cancelled) return
        setSession(dev)
        setDeclaration(check)
        setSite(siteValue)
        setLayout(layoutValue)
        setProfile(profileValue)
        setScenario(head)
        scenarioRef.current = head
        setDraft(layoutValue.placements[0].position_enu_m as Vec3)
        setCurrentRunId(selectedRun)
        if (existing && selections.evaluation.current_job) setRuns([{ job: selections.evaluation.current_job, result: existing }])
        setConnection({ status: 'connected', health })
      } catch (err) {
        if (!cancelled) setConnection({ status: 'error', reason: err instanceof ApiError && err.code === 'NETWORK' ? 'Backend not reachable on this origin.' : message(err) })
      }
    })()
    return () => { cancelled = true }
  }, [client, attempt])

  const record = useCallback((job: Job, result: Result | null) => {
    setRuns(previous => {
      const others = previous.filter(r => r.job.job_id !== job.job_id)
      return [{ job, result }, ...others].slice(0, 20)
    })
  }, [])

  const poll = useCallback(async (job: Job) => {
    let current = job
    while (alive.current && !TERMINAL_JOB_STATES.has(current.status)) {
      await sleep(POLL_MS)
      current = await client.job(job.job_id)
      if (activeJobId.current === job.job_id) setActiveJob(current)
    }
    const result = current.status === 'completed' && current.run_id ? await client.result(current.run_id) : null
    if (result && (result.source_job_id !== current.job_id || result.input_fingerprint !== current.input_fingerprint)) {
      throw new Error(`Result ${result.run_id} does not match job ${current.job_id}; not displayed`)
    }
    record(current, result)
    const head = scenarioRef.current
    if (head) await refreshSelection(head)
  }, [client, record, refreshSelection])

  const evaluate = useCallback(async () => {
    const head = scenarioRef.current
    if (!head || !layout || !placement || !draftPosition) return
    setError(null)
    setNotice(null)
    try {
      let target = head
      if (!samePosition(draftPosition, placement.position_enu_m as Vec3) || Date.parse(head.input.search.deadline_utc) <= Date.now()) {
        setBusy('committing')
        const plan = buildCommit(head, layout, placement.placement_id, draftPosition, Date.now())
        const storedLayout = await client.registerLayout(plan.layout)
        target = await client.replaceScenario(head.scenario_id, plan.input, plan.ifMatch)
        scenarioRef.current = target
        setScenario(target)
        setLayout(storedLayout)
        setDraft(storedLayout.placements.find(p => p.placement_id === placement.placement_id)!.position_enu_m as Vec3)
        setCurrentRunId(null)
        setNotice(`Saved as scenario revision ${target.revision} (layout revision ${storedLayout.revision}).${plan.deadlineRenewedTo ? ` Job deadline renewed to ${plan.deadlineRenewedTo}.` : ''}`)
      }
      setBusy('submitting')
      const job = await client.submitJob(evaluateRequest(target, newRequestId()))
      activeJobId.current = job.job_id
      setActiveJob(job)
      setBusy(null)
      await poll(job)
    } catch (err) {
      setBusy(null)
      if (err instanceof ApiError && err.code === 'REVISION_CONFLICT') {
        setError(`${err.message}. The backend refused because stored revision or input identity no longer matches (another accepted change, or a changed source asset). Nothing was computed; reload to see the latest scenario.`)
      } else {
        setError(message(err))
      }
    }
  }, [client, draftPosition, layout, placement, poll])

  const cancel = useCallback(async () => {
    const id = activeJobId.current
    if (!id) return
    setBusy('cancelling')
    try {
      const job = await client.cancelJob(id)
      if (activeJobId.current === id) setActiveJob(job)
    } catch (err) {
      setError(message(err))
    } finally {
      setBusy(null)
    }
  }, [client])

  const currentness = useCallback((result: Result): Currentness => {
    if (!scenario) return 'superseded'
    return classifyResult({ result, head: refOf(scenario), currentRunId, draftDirty })
  }, [scenario, currentRunId, draftDirty])

  const jobRunning = activeJob !== null && !TERMINAL_JOB_STATES.has(activeJob.status)
  const canEvaluate = connection.status === 'connected' && busy === null &&
    Boolean(connection.health.available_operations.includes('evaluate_layout')) && Boolean(placement)

  return useMemo(() => ({
    connection, session, declaration, site, profile, scenario, layout,
    placementId: placement?.placement_id ?? null,
    committedPosition, draftPosition, draftDirty, activeJob, runs, currentRunId, busy, notice, error,
    canEvaluate: canEvaluate && !(jobRunning && !draftDirty),
    currentness,
    setDraftPosition: (p: Vec3) => setDraft(p),
    revertDraft: () => committedPosition && setDraft(committedPosition),
    evaluate, cancel,
    reconnect: () => setAttempt(a => a + 1),
  }), [connection, session, declaration, site, profile, scenario, layout, placement, committedPosition, draftPosition, draftDirty, activeJob, runs, currentRunId, busy, notice, error, canEvaluate, jobRunning, currentness, evaluate, cancel])
}
