import { describe, expect, it } from 'vitest'
import type { Job } from '../api/types'
import { CURRENTNESS_LABEL, NO_PROGRESS_CAPTION } from './evaluation'
import { CANCEL_NOTE, STATUS_LOST_DETAIL, STATUS_WORD, runningJobView, supersededView } from './runningJob'

// Labelled synthetic test inputs shaped like the backend Job wire type. Not runtime results.
const FP = '41d9' + '0'.repeat(56) + 'e2c0'
const job = (over: Partial<Job> = {}): Job => ({
  cancel_requested: false, created_at_utc: '2026-11-13T12:00:00Z', delivery: null, error: null, finished_at_utc: null,
  input_fingerprint: FP, job_id: 'job-0207', operation: 'search_layouts', progress: null,
  request_id: 'ui-1', run_id: null, scenario_id: 'scn-wp-014', scenario_revision: 4, schema_version: '0.1.0', scope: 'accepted',
  selection_seq: 2, started_at_utc: '2026-11-13T12:00:01Z', status: 'running', superseded_by_revision: null, view_slot: 'search', ...over,
})

describe('runningJobView', () => {
  it('shows the real status, operation, job identity and the job\'s own revision', () => {
    const v = runningJobView(job(), false)
    expect(v && [v.status, v.statusWord, v.pillTone, v.kicker, v.heading, v.jobId, v.scenarioRevision, v.viewSlot, v.selectionSeq, v.fingerprint])
      .toEqual(['running', 'Running', 'progress', 'SEARCH', 'Searching revision 4', 'job-0207', 4, 'search', 2, FP])
    expect(v?.detail).toBe('The local worker is processing this search.')
  })
  it('uses an uppercase kicker word per operation', () => {
    const kicker = (operation: Job['operation']) => runningJobView(job({ operation }), false)?.kicker
    expect([kicker('evaluate_layout'), kicker('search_layouts'), kicker('compare_locations'), kicker('compare_scenarios')])
      .toEqual(['EVALUATION', 'SEARCH', 'COMPARISON', 'COMPARISON'])
  })
  it('is indeterminate when the backend reports no progress, with counts only when total > 0', () => {
    expect(runningJobView(job(), false)?.progress).toEqual({ kind: 'indeterminate', caption: NO_PROGRESS_CAPTION })
    expect(runningJobView(job({ progress: { completed: 0, phase: 'x', total: 0, unit: 'u' } }), false)?.progress.kind).toBe('indeterminate')
    expect(runningJobView(job({ progress: { completed: 27, phase: 'greedy', total: 39, unit: 'placements' } }), false)?.progress)
      .toEqual({ kind: 'counts', completed: 27, total: 39 })
  })
  it('never shows a phase, even when the backend reports one', () => {
    const v = runningJobView(job({ progress: { completed: 27, phase: 'greedy selection', total: 39, unit: 'placements' } }), false)
    expect(JSON.stringify(v)).not.toContain('greedy')
  })
  it('uses the exact status words and the same tones as describeJob', () => {
    expect(Object.values(STATUS_WORD)).toEqual(['Queued', 'Running', 'Completed', 'Failed', 'Cancelled', 'Status unknown'])
    const tone = (status: Job['status']) => runningJobView(job({ status }), false)?.pillTone
    expect([tone('queued'), tone('running'), tone('completed'), tone('failed'), tone('cancelled')]).toEqual(['progress', 'progress', 'ok', 'warn', 'warn'])
    expect(runningJobView(job({ status: 'queued' }), false)?.detail).toBe('Waiting for the local worker.')
  })
  it('names a finished job with a noun, not a verb in progress', () => {
    expect(runningJobView(job({ status: 'completed', run_id: 'run-1' }), false)?.heading).toBe('Search of revision 4')
    expect(runningJobView(job({ status: 'cancelled', operation: 'evaluate_layout' }), false)?.heading).toBe('Evaluation of revision 4')
  })
  it('keeps the superseded note for active jobs, as describeJob does for finished ones', () => {
    expect(runningJobView(job({ superseded_by_revision: 5 }), false)?.detail).toBe('The local worker is processing this search. Superseded by revision 5.')
  })
  it('shows a lost status as unknown, never as running, with a re-check and no cancel or progress', () => {
    const v = runningJobView(job(), true)
    expect(v && [v.status, v.statusWord, v.pillTone, v.heading, v.detail, v.canRecheck, v.canCancel, v.progress.kind])
      .toEqual(['status-unknown', 'Status unknown', 'warn', 'Search of revision 4', STATUS_LOST_DETAIL, true, false, 'none'])
  })
  it('ignores a lost flag once the job is terminal', () => {
    const v = runningJobView(job({ status: 'completed', run_id: 'run-1' }), true)
    expect(v && [v.status, v.canRecheck, v.progress.kind]).toEqual(['completed', false, 'none'])
  })
  it('offers cancel only for an active job with no cancel pending', () => {
    expect(runningJobView(job(), false)?.canCancel).toBe(true)
    expect(runningJobView(job(), false)?.cancelLabel).toBe('Cancel search')
    const pending = runningJobView(job({ cancel_requested: true }), false)
    expect(pending && [pending.canCancel, pending.cancelLabel, pending.cancelRequested]).toEqual([false, 'Cancel requested', true])
    expect(runningJobView(job({ status: 'cancelled' }), false)?.canCancel).toBe(false)
    expect(runningJobView(job({ operation: 'evaluate_layout' }), false)?.cancelLabel).toBe('Cancel evaluation')
    expect(CANCEL_NOTE).toBe('Cancelling keeps no partial result.')
  })
  it('passes through the backend failure detail for a failed job', () => {
    const error = { code: 'WORKER_INTERRUPTED' as const, message: 'Worker restarted', details: {}, field_errors: [], retryable: false }
    const v = runningJobView(job({ status: 'failed', error }), false)
    expect(v?.detail).toContain('WORKER_INTERRUPTED: Worker restarted')
  })
  it('returns null without a job', () => {
    expect(runningJobView(null, true)).toBeNull()
  })
})

describe('supersededView', () => {
  const old = { scenario_id: 'scn-wp-014', scope: 'accepted' as const, scenario_revision: 3, superseded_by_revision: 4, run_id: 'run-3f81c2' }
  const head = (revision: number, over: Partial<{ scenario_id: string; scope: 'accepted' | 'hypothetical' }> = {}) =>
    ({ scenario_id: 'scn-wp-014', scope: 'accepted' as const, revision, ...over })
  it('names the superseding revision from the backend job field first, with the project\'s words', () => {
    const v = supersededView(old, head(5), true)
    expect(v && [v.revision, v.supersededBy, v.source, v.pill, v.meta]).toEqual([3, 4, 'job', 'REV 3 RUN · SUPERSEDED', 'run-3f81c2 · kept in history'])
    expect(v?.body).toBe(`${CURRENTNESS_LABEL.superseded.detail} Superseded by revision 4.`)
  })
  it('falls back to a newer accepted head of the same scenario and scope, and says so', () => {
    const v = supersededView({ ...old, superseded_by_revision: null }, head(4), true)
    expect(v && [v.supersededBy, v.source]).toEqual([4, 'head'])
  })
  it('does not name a revision it cannot know: another scenario, another scope, or an older head', () => {
    const unknown = { ...old, superseded_by_revision: null }
    for (const h of [head(5, { scenario_id: 'scn-other' }), head(5, { scope: 'hypothetical' }), head(2), null]) {
      const v = supersededView(unknown, h, true)
      expect(v && [v.supersededBy, v.source, v.body]).toEqual([null, null, CURRENTNESS_LABEL.superseded.detail])
    }
  })
  it('follows the project\'s currentness rule: nothing unless the caller says superseded', () => {
    expect(supersededView(old, head(5), false)).toBeNull()
    expect(supersededView(null, head(4), true)).toBeNull()
  })
  it('never carries a metric value', () => {
    expect(JSON.stringify(supersededView(old, head(4), true))).not.toMatch(/m²|m2_h|£|\d{3,}/)
  })
})
