import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ApiError, CanopyClient, TERMINAL_JOB_STATES } from '../api/client'
import { loadDevSession, verifyDeclaration, type DeclarationCheck, type DevSession } from '../api/session'
import { followJob, isJobRunning } from './followJob'
import type { Health, Job, JobRequest, Layout, Result, Scenario, ScenarioRef, SiteBundle, TreeProfile, Vec3 } from '../api/types'
import {
  buildCommit, candidateAt, classifyResult, diffInputs, evaluateRequest, refOf, requirementsOf, sameRequirements, samePosition,
  validateRequirements, type Currentness, type FieldChange, type Requirements,
} from './evaluation'

export type ConnectionState =
  | { readonly status: 'connecting' }
  | { readonly status: 'no-session'; readonly reason: string }
  | { readonly status: 'error'; readonly reason: string }
  | { readonly status: 'connected'; readonly health: Health }

export interface RunRecord {
  readonly job: Job
  readonly result: Result | null
  /** The exact scenario snapshot the result was computed from (budget, objective, cases). */
  readonly inputScenario: Scenario | null
}

export type ViewSlot = 'evaluation' | 'search' | 'comparison'
export const slotOf = (operation: Result['operation']): ViewSlot =>
  operation === 'search_layouts' ? 'search' : operation === 'evaluate_layout' ? 'evaluation' : 'comparison'

/** A hypothetical scenario prepared elsewhere (for example by the planning agent) awaiting a human decision. */
export interface ProposalReview {
  readonly proposal: Scenario
  readonly changes: readonly FieldChange[]
  /** Accepting is only possible when the proposal's base is the current accepted head. */
  readonly baseIsHead: boolean
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
  readonly positionDirty: boolean
  readonly acceptedRequirements: Requirements | null
  readonly draftRequirements: Requirements | null
  readonly requirementsDirty: boolean
  readonly requirementErrors: readonly string[]
  readonly draftChanges: readonly FieldChange[]
  /** Any unaccepted edit: tree position or requirements. */
  readonly draftDirty: boolean
  readonly activeJob: Job | null
  /** Polling the active job failed: its real status is unknown until re-checked (never shown as running). */
  readonly jobStatusLost: boolean
  readonly runs: readonly RunRecord[]
  readonly currentRunId: string | null
  readonly currentRunIds: Readonly<Record<ViewSlot, string | null>>
  readonly busy: 'committing' | 'submitting' | 'cancelling' | 'loading-proposal' | 'accepting-proposal' | null
  readonly notice: string | null
  readonly error: string | null
  readonly canEvaluate: boolean
  readonly review: ProposalReview | null
  readonly currentness: (result: Result) => Currentness
  readonly setDraftPosition: (p: Vec3) => void
  readonly setDraftRequirements: (r: Requirements) => void
  readonly revertDraft: () => void
  readonly evaluate: () => Promise<void>
  readonly submit: (build: (head: Scenario, requestId: string) => JobRequest) => Promise<void>
  readonly cancel: () => Promise<void>
  /** Re-query the active job after a polling failure and, if it is still running, keep following it. */
  readonly recheckJob: () => Promise<void>
  readonly loadProposal: (scenarioId: string, revision: number) => Promise<void>
  readonly acceptProposal: () => Promise<void>
  readonly dismissProposal: () => void
  readonly reload: () => void
}

const POLL_MS = 150
const sleep = (ms: number) => new Promise<void>(resolve => setTimeout(resolve, ms))
const message = (error: unknown) => (error instanceof Error ? error.message : String(error))
export const newRequestId = () => `ui-${typeof crypto.randomUUID === 'function' ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`}`
const defaultClient = new CanopyClient()

function conflictText(err: ApiError) {
  return `${err.message}. The backend refused because the accepted revision or input identity no longer matches (another accepted change, or a changed source asset). Nothing was saved or computed; your draft is kept. Reload to see the latest accepted scenario.`
}

export function useWorkspace(client: CanopyClient = defaultClient): Workspace {
  const [connection, setConnection] = useState<ConnectionState>({ status: 'connecting' })
  const [session, setSession] = useState<DevSession | null>(null)
  const [declaration, setDeclaration] = useState<DeclarationCheck | null>(null)
  const [site, setSite] = useState<SiteBundle | null>(null)
  const [profile, setProfile] = useState<TreeProfile | null>(null)
  const [scenario, setScenario] = useState<Scenario | null>(null)
  const [layout, setLayout] = useState<Layout | null>(null)
  const [draftPosition, setDraft] = useState<Vec3 | null>(null)
  const [draftRequirements, setDraftRequirements] = useState<Requirements | null>(null)
  const [activeJob, setActiveJob] = useState<Job | null>(null)
  const [jobStatusLost, setJobStatusLost] = useState(false)
  const [runs, setRuns] = useState<RunRecord[]>([])
  const [currentRunIds, setCurrentRunIds] = useState<Record<ViewSlot, string | null>>({ evaluation: null, search: null, comparison: null })
  const currentRunId = currentRunIds.evaluation
  const [busy, setBusy] = useState<Workspace['busy']>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [review, setReview] = useState<ProposalReview | null>(null)
  const [attempt, setAttempt] = useState(0)
  const scenarioRef = useRef<Scenario | null>(null)
  const activeJobId = useRef<string | null>(null)
  const alive = useRef(true)
  // Selection reads can overlap (the early refresh after submit and the one after a job finishes). Each read is
  // numbered when issued; a reply older than the last applied selection is dropped, so a late reply cannot roll
  // the selection back. Direct writes (adopting a head, the initial load) count as applied too.
  const selectionIssued = useRef(0)
  const selectionApplied = useRef(0)
  const markSelectionWrite = () => { selectionIssued.current += 1; selectionApplied.current = selectionIssued.current }

  useEffect(() => { scenarioRef.current = scenario }, [scenario])
  useEffect(() => {
    alive.current = true
    return () => { alive.current = false }
  }, [])

  const placement = layout?.placements[0] ?? null
  const committedPosition = placement ? (placement.position_enu_m as Vec3) : null
  const positionDirty = Boolean(draftPosition && committedPosition && !samePosition(draftPosition, committedPosition))
  const acceptedRequirements = useMemo(() => (scenario ? requirementsOf(scenario) : null), [scenario])
  const requirementsDirty = Boolean(draftRequirements && acceptedRequirements && !sameRequirements(draftRequirements, acceptedRequirements))
  const draftDirty = positionDirty || requirementsDirty
  const exclusionIds = useMemo(() => site?.exclusions.map(e => e.feature_id) ?? [], [site])
  const requirementErrors = useMemo(() => (draftRequirements ? validateRequirements(draftRequirements, exclusionIds) : []), [draftRequirements, exclusionIds])

  const draftChanges = useMemo(() => {
    if (!scenario || !layout || !placement || !draftPosition || !draftDirty || requirementErrors.length) return []
    try {
      return buildCommit(scenario, layout, placement.placement_id, draftPosition, Date.now(), draftRequirements ?? undefined, candidateAt(site?.candidate_catalogue ?? [], draftPosition)).changes
        .filter(c => c.path !== 'search.deadline_utc')
    } catch {
      return []
    }
  }, [scenario, layout, placement, draftPosition, draftRequirements, draftDirty, requirementErrors, site])

  /** Re-read the backend's evaluation selection for the head revision. */
  const refreshSelection = useCallback(async (head: Scenario) => {
    selectionIssued.current += 1
    const seq = selectionIssued.current
    const selections = await client.selections(refOf(head))
    if (!alive.current || scenarioRef.current?.revision !== head.revision) return
    if (seq < selectionApplied.current) return // a newer selection was already applied
    selectionApplied.current = seq
    setCurrentRunIds({
      evaluation: selections.evaluation.current_job?.run_id ?? null,
      search: selections.search.current_job?.run_id ?? null,
      comparison: selections.comparison.current_job?.run_id ?? null,
    })
  }, [client])

  /** Adopt a new accepted head: its layout becomes the committed (and draft) position. */
  const adoptHead = useCallback(async (head: Scenario, keepDraft = false) => {
    const ref = head.input.proposed_layout_ref
    if (!ref) throw new Error('Scenario has no proposed layout')
    const nextLayout = await client.layout(ref.layout_id, ref.revision)
    scenarioRef.current = head
    setScenario(head)
    setLayout(nextLayout)
    if (!keepDraft) {
      setDraft(nextLayout.placements[0]?.position_enu_m as Vec3)
      setDraftRequirements(requirementsOf(head))
    }
    markSelectionWrite()
    setCurrentRunIds({ evaluation: null, search: null, comparison: null })
    return nextLayout
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
        const selected = (['evaluation', 'search', 'comparison'] as const)
          .map(slot => selections[slot].current_job)
          .filter((job): job is Job => Boolean(job?.run_id))
        const existing: RunRecord[] = await Promise.all(selected.map(async job => ({ job, result: await client.result(job.run_id!), inputScenario: head })))
        if (cancelled) return
        setSession(dev)
        setDeclaration(check)
        setSite(siteValue)
        setLayout(layoutValue)
        setProfile(profileValue)
        setScenario(head)
        scenarioRef.current = head
        setDraft(layoutValue.placements[0].position_enu_m as Vec3)
        setDraftRequirements(requirementsOf(head))
        markSelectionWrite()
        setCurrentRunIds({
          evaluation: selections.evaluation.current_job?.run_id ?? null,
          search: selections.search.current_job?.run_id ?? null,
          comparison: selections.comparison.current_job?.run_id ?? null,
        })
        setRuns(existing)
        setActiveJob(null)
        setJobStatusLost(false)
        setReview(null)
        setConnection({ status: 'connected', health })
      } catch (err) {
        if (!cancelled) setConnection({ status: 'error', reason: err instanceof ApiError && err.code === 'NETWORK' ? 'Backend not reachable on this origin.' : message(err) })
      }
    })()
    return () => { cancelled = true }
  }, [client, attempt])

  const record = useCallback((job: Job, result: Result | null, inputScenario: Scenario | null) => {
    setRuns(previous => [{ job, result, inputScenario }, ...previous.filter(r => r.job.job_id !== job.job_id)].slice(0, 30))
  }, [])

  const poll = useCallback(async (job: Job) => {
    // A failed poll marks the status unknown (the job may still be running) rather than leaving it shown as running.
    const current = await followJob(job, {
      fetchJob: id => client.job(id),
      sleep,
      alive: () => alive.current,
      onUpdate: j => { if (activeJobId.current === job.job_id) { setActiveJob(j); setJobStatusLost(false) } },
      onLost: () => { if (activeJobId.current === job.job_id) setJobStatusLost(true) },
    }, POLL_MS)
    const result = current.status === 'completed' && current.run_id ? await client.result(current.run_id) : null
    if (result && (result.source_job_id !== current.job_id || result.input_fingerprint !== current.input_fingerprint)) {
      throw new Error(`Result ${result.run_id} does not match job ${current.job_id}; not displayed`)
    }
    const inputScenario = result ? await client.scenario(result.input_snapshot_ref) : null
    record(current, result, inputScenario)
    const head = scenarioRef.current
    if (head) await refreshSelection(head)
  }, [client, record, refreshSelection])

  const handleFailure = useCallback(async (err: unknown) => {
    setBusy(null)
    if (!(err instanceof ApiError && err.code === 'REVISION_CONFLICT')) { setError(message(err)); return }
    setError(conflictText(err))
    // Never keep presenting the old head as current after a refused write: re-read the real head.
    const head = scenarioRef.current
    if (!head) return
    try {
      const latest = await client.latestScenario(head.scenario_id, head.revision)
      if (latest.revision !== head.revision) {
        await adoptHead(latest, true)
        await refreshSelection(latest)
        setError(`${conflictText(err)} A newer accepted revision ${latest.revision} now exists; it is loaded and your draft is kept on top of it. Review the changes and accept again.`)
      }
    } catch (probe) {
      setError(`${conflictText(err)} The latest revision could not be re-read: ${message(probe)}`)
    }
  }, [client, adoptHead, refreshSelection])

  /** Submit any registered job for the head accepted revision and follow it to completion. */
  const submit = useCallback(async (build: (head: Scenario, requestId: string) => JobRequest) => {
    const head = scenarioRef.current
    if (!head) return
    setError(null)
    try {
      setBusy('submitting')
      const job = await client.submitJob(build(head, newRequestId()))
      activeJobId.current = job.job_id
      setActiveJob(job)
      setJobStatusLost(false)
      setBusy(null)
      // The backend moves the slot's selection when it accepts the job, so the previous run must stop being
      // shown as CURRENT now, not only after this job finishes. Non-blocking; a failure here is not fatal.
      refreshSelection(head).catch(() => {})
      await poll(job)
    } catch (err) {
      await handleFailure(err)
    }
  }, [client, poll, handleFailure])

  /** Accept every draft edit as the next accepted revision (a human action), then recompute. */
  const evaluate = useCallback(async () => {
    const head = scenarioRef.current
    if (!head || !layout || !placement || !draftPosition) return
    if (requirementErrors.length) { setError(requirementErrors.join(' ')); return }
    setError(null)
    setNotice(null)
    try {
      let target = head
      if (draftDirty || Date.parse(head.input.search.deadline_utc) <= Date.now()) {
        setBusy('committing')
        const plan = buildCommit(head, layout, placement.placement_id, draftPosition, Date.now(), draftRequirements ?? undefined, candidateAt(site?.candidate_catalogue ?? [], draftPosition))
        const storedLayout = plan.layout ? await client.registerLayout(plan.layout) : null
        target = await client.replaceScenario(head.scenario_id, plan.input, plan.ifMatch)
        await adoptHead(target)
        const changed = plan.changes.filter(c => c.path !== 'search.deadline_utc').map(c => c.path)
        setNotice(`Accepted as scenario revision ${target.revision}${storedLayout ? ` (layout revision ${storedLayout.revision})` : ''}${changed.length ? `: ${changed.join(', ')}` : ''}.${plan.deadlineRenewedTo ? ` Job deadline renewed to ${plan.deadlineRenewedTo}.` : ''}`)
      }
      await submit(evaluateRequest)
    } catch (err) {
      await handleFailure(err)
    }
  }, [client, draftPosition, draftRequirements, draftDirty, layout, placement, requirementErrors, adoptHead, submit, handleFailure, site])

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

  const loadProposal = useCallback(async (scenarioId: string, revision: number) => {
    const head = scenarioRef.current
    if (!head) return
    setError(null)
    setBusy('loading-proposal')
    try {
      const proposal = await client.scenario({ scenario_id: scenarioId, revision, scope: 'hypothetical' })
      const base = proposal.base_scenario_ref
      setReview({
        proposal,
        changes: diffInputs(head.input, proposal.input),
        baseIsHead: Boolean(base && base.scenario_id === head.scenario_id && base.revision === head.revision && base.scope === 'accepted'),
      })
    } catch (err) {
      setError(err instanceof ApiError && err.code === 'UNKNOWN_REVISION' ? `No hypothetical scenario ${scenarioId} revision ${revision} exists.` : message(err))
    } finally {
      setBusy(null)
    }
  }, [client])

  const acceptProposal = useCallback(async () => {
    const head = scenarioRef.current
    if (!head || !review) return
    setError(null)
    setBusy('accepting-proposal')
    try {
      const ref: ScenarioRef = refOf(review.proposal)
      const accepted = await client.acceptScenario(ref, head.revision)
      await adoptHead(accepted)
      setReview(null)
      setNotice(`Proposal ${ref.scenario_id.slice(0, 8)}… rev ${ref.revision} accepted as scenario revision ${accepted.revision}. Recomputing.`)
      setBusy(null)
      await submit(evaluateRequest)
    } catch (err) {
      await handleFailure(err)
    }
  }, [client, review, adoptHead, submit, handleFailure])

  const currentness = useCallback((result: Result): Currentness => {
    if (!scenario) return 'superseded'
    return classifyResult({ result, head: refOf(scenario), currentRunId: currentRunIds[slotOf(result.operation)], draftDirty })
  }, [scenario, currentRunIds, draftDirty])

  const recheckJob = useCallback(async () => {
    const id = activeJobId.current
    if (!id) return
    setError(null)
    try {
      const job = await client.job(id)
      if (activeJobId.current === id) { setActiveJob(job); setJobStatusLost(false) }
      await poll(job)
    } catch (err) {
      if (activeJobId.current === id) setJobStatusLost(true)
      await handleFailure(err)
    }
  }, [client, poll, handleFailure])

  // A job whose status is unknown is not treated as running, so it cannot block planning indefinitely.
  const jobRunning = isJobRunning(activeJob, jobStatusLost)
  const connectedOk = connection.status === 'connected' && busy === null &&
    connection.health.available_operations.includes('evaluate_layout') && Boolean(placement)

  return useMemo(() => ({
    connection, session, declaration, site, profile, scenario, layout,
    placementId: placement?.placement_id ?? null,
    committedPosition, draftPosition, positionDirty, acceptedRequirements, draftRequirements, requirementsDirty, requirementErrors,
    draftChanges, draftDirty, activeJob, jobStatusLost, runs, currentRunId, currentRunIds, busy, notice, error, review,
    canEvaluate: connectedOk && requirementErrors.length === 0 && !(jobRunning && !draftDirty),
    currentness,
    setDraftPosition: (p: Vec3) => setDraft(p),
    setDraftRequirements: (r: Requirements) => setDraftRequirements(r),
    revertDraft: () => {
      if (committedPosition) setDraft(committedPosition)
      if (acceptedRequirements) setDraftRequirements(acceptedRequirements)
    },
    evaluate, submit, cancel, recheckJob, loadProposal, acceptProposal,
    dismissProposal: () => setReview(null),
    reload: () => setAttempt(a => a + 1),
  }), [connection, session, declaration, site, profile, scenario, layout, placement, committedPosition, draftPosition, positionDirty,
    acceptedRequirements, draftRequirements, requirementsDirty, requirementErrors, draftChanges, draftDirty, activeJob, jobStatusLost, runs, currentRunId, currentRunIds,
    busy, notice, error, review, connectedOk, jobRunning, currentness, evaluate, submit, cancel, recheckJob, loadProposal, acceptProposal])
}
