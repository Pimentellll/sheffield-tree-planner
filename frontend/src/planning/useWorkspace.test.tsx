// @vitest-environment jsdom
import { act, renderHook, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import type { CanopyClient } from '../api/client'
import type { Job, Result, Scenario } from '../api/types'
import { useWorkspace } from './useWorkspace'

// LABELLED SYNTHETIC TEST INPUT: a fake client returning contract-shaped records so the real hook can be
// driven through its job states. Nothing here is a runtime result or is rendered by the application.
const head = {
  scenario_id: 's1', revision: 1, scope: 'accepted', base_scenario_ref: null,
  input: {
    site_id: 'site', scene_revision: 1, semantic_revision: 1, profile_library_revision: 1, candidate_catalogue_revision: 1,
    proposed_layout_ref: { layout_id: 'L', revision: 1 },
    constraints: { budget_pence: 10_000, budget_basis: 'upfront', max_tree_count: null, excluded_region_ids: [], allowed_profile_ids: [], spacing_rules: [], winter_limits: [], pinned_placements: [], survey_requirements: [] },
    objective: { kind: 'maximise_shade_under_budget', primary_case_id: 'c', quantity_kind: 'geometric' },
    evaluation_cases: [{ case_id: 'c', profile_state: 'mature', role: 'benefit' }],
    search: { deadline_utc: '2099-01-01T00:00:00Z' },
  },
} as unknown as Scenario
const job = (id: string, status: Job['status'], runId: string | null): Job =>
  ({ job_id: id, status, run_id: runId, operation: 'evaluate_layout', scenario_id: 's1', scenario_revision: 1, scope: 'accepted', input_fingerprint: `f-${id}`, progress: null, cancel_requested: false, superseded_by_revision: null, error: null, delivery: null } as unknown as Job)
const result = (runId: string, jobId: string): Result =>
  ({ run_id: runId, source_job_id: jobId, input_fingerprint: `f-${jobId}`, scenario_id: 's1', scenario_revision: 1, scope: 'accepted', operation: 'evaluate_layout', input_snapshot_ref: { scenario_id: 's1', revision: 1, scope: 'accepted' }, metrics: [], layouts: [], constraints: [], missing_metrics: [], assumptions: [], limitations: [] } as unknown as Result)

interface Fake {
  selected: Job | null
  pollJob: () => Promise<Job>
  calls: string[]
  /** When set, each selections() reply waits for this promise (lets a test deliver replies out of order). */
  selectionsHook?: () => Promise<Job | null>
}

function fakeClient(state: Fake): CanopyClient {
  const r1 = result('r1', 'j1')
  return {
    health: async () => ({ status: 'ok', version: 't', schema_version: '0.1.0', worker_mode: 'background', available_operations: ['evaluate_layout'] }),
    latestScenario: async () => head,
    scenario: async () => head,
    site: async () => ({ site_kind: 'synthetic_test', name: 'synthetic', exclusions: [], candidate_catalogue: [] }),
    layout: async () => ({ layout_id: 'L', revision: 1, placements: [{ placement_id: 'p', position_enu_m: [0, 0, 0], profile_id: 'prof' }] }),
    profile: async () => ({ profile_id: 'prof', states: {} }),
    selections: async () => {
      state.calls.push('selections')
      const selected = state.selectionsHook ? await state.selectionsHook() : state.selected
      return { evaluation: { current_job: selected }, search: { current_job: null }, comparison: { current_job: null } }
    },
    result: async (runId: string) => (runId === 'r1' ? r1 : result(runId, 'j2')),
    submitJob: async () => { state.calls.push('submitJob'); return job('j2', 'queued', null) },
    job: () => state.pollJob(),
  } as unknown as CanopyClient
}

async function connected(state: Fake) {
  // One stable client, as the app passes: a new client per render would re-run the load effect forever.
  const client = fakeClient(state)
  const hook = renderHook(() => useWorkspace(client))
  await waitFor(() => expect(hook.result.current.connection.status).toBe('connected'))
  return hook
}

describe('useWorkspace job following (-51 review of #84)', () => {
  beforeEach(() => { window.history.replaceState({}, '', '/?scenario=s1&revision=1') })

  it('a failed poll marks the status unknown without blocking planning; recheckJob resumes and clears it', async () => {
    const state: Fake = { selected: job('j1', 'completed', 'r1'), pollJob: async () => { throw new Error('network down') }, calls: [] }
    const { result: ws } = await connected(state)
    await act(async () => { await ws.current.evaluate() })
    await waitFor(() => expect(ws.current.jobStatusLost).toBe(true), { timeout: 3000 })
    expect(ws.current.activeJob?.status).toBe('queued')
    expect(ws.current.canEvaluate).toBe(true) // an unknown status never blocks planning

    state.pollJob = async () => job('j2', 'completed', 'r2')
    state.selected = job('j2', 'completed', 'r2')
    await act(async () => { await ws.current.recheckJob() })
    await waitFor(() => expect(ws.current.jobStatusLost).toBe(false), { timeout: 3000 })
    await waitFor(() => expect(ws.current.runs[0]?.result?.run_id).toBe('r2'), { timeout: 3000 })
    expect(ws.current.currentness(ws.current.runs[0].result!)).toBe('current')
  })

  it('stops showing the previous run as CURRENT as soon as a new job is accepted, before it finishes', async () => {
    const state: Fake = { selected: job('j1', 'completed', 'r1'), pollJob: () => new Promise<Job>(() => {}), calls: [] }
    const { result: ws } = await connected(state)
    const previous = ws.current.runs[0].result!
    expect(ws.current.currentness(previous)).toBe('current')
    // The backend moves the evaluation slot to the new, still-running job when it accepts it.
    state.selected = job('j2', 'queued', null)
    await act(async () => { void ws.current.evaluate() })
    await waitFor(() => expect(ws.current.currentness(previous)).toBe('not-selected'), { timeout: 3000 })
    expect(state.calls.indexOf('selections', state.calls.indexOf('submitJob'))).toBeGreaterThan(-1)
    expect(ws.current.activeJob?.status).toBe('queued') // the new job is still running: nothing finished
  })

  it('drops a selection reply older than the last one applied (overlapping refreshes, -51 ordering guard)', async () => {
    const state: Fake = { selected: job('j1', 'completed', 'r1'), pollJob: async () => job('j2', 'completed', 'r2'), calls: [] }
    const { result: ws } = await connected(state)
    // From here every selections() reply waits until the test releases it.
    const releases: Array<(selected: Job | null) => void> = []
    state.selectionsHook = () => new Promise<Job | null>(resolve => { releases.push(resolve) })
    await act(async () => { void ws.current.evaluate() })
    // Read 1 is the early refresh after submit; read 2 is the refresh after the job completed and was recorded.
    await waitFor(() => expect(releases.length).toBe(2), { timeout: 3000 })
    await act(async () => { releases[1](job('j2', 'completed', 'r2')) })
    await waitFor(() => expect(ws.current.currentRunIds.evaluation).toBe('r2'), { timeout: 3000 })
    const newest = ws.current.runs[0].result!
    expect(ws.current.currentness(newest)).toBe('current')
    // The older reply arrives last, describing the job while it was still queued (no run yet): it must be dropped.
    await act(async () => { releases[0](job('j2', 'queued', null)) })
    await new Promise(resolve => setTimeout(resolve, 50))
    expect(ws.current.currentRunIds.evaluation).toBe('r2')
    expect(ws.current.currentness(newest)).toBe('current')
  })
})
