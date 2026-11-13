import { describe, expect, it } from 'vitest'
import type { Job } from '../api/types'
import { followJob, isJobRunning, type FollowJobDeps } from './followJob'

// LABELLED SYNTHETIC TEST INPUT: Job-shaped records to exercise the polling loop; not runtime results.
const job = (status: Job['status']): Job => ({ job_id: 'j1', status } as unknown as Job)

function harness(responses: Array<Job | Error>, alive = () => true) {
  const events: string[] = []
  let i = 0
  const deps: FollowJobDeps = {
    fetchJob: async () => {
      const next = responses[i++]
      if (next instanceof Error) throw next
      return next
    },
    sleep: async () => {},
    alive,
    onUpdate: j => events.push(`update:${j.status}`),
    onLost: () => events.push('lost'),
  }
  return { deps, events }
}

describe('followJob (stuck-running fix, -51 #3)', () => {
  it('follows a job to its terminal state, reporting each polled state', async () => {
    const { deps, events } = harness([job('running'), job('completed')])
    expect((await followJob(job('queued'), deps, 1)).status).toBe('completed')
    expect(events).toEqual(['update:running', 'update:completed'])
  })
  it('marks the status unknown and rethrows when a poll fails, instead of staying "running"', async () => {
    const { deps, events } = harness([job('running'), new Error('network down')])
    await expect(followJob(job('queued'), deps, 1)).rejects.toThrow('network down')
    expect(events).toEqual(['update:running', 'lost'])
  })
  it('re-following after a failure reports the job again (the host clears "unknown" on update)', async () => {
    const { deps, events } = harness([job('completed')])
    expect((await followJob(job('running'), deps, 1)).status).toBe('completed')
    expect(events).toEqual(['update:completed'])
  })
  it('does not poll a job that is already terminal, nor after the host has gone', async () => {
    const done = harness([])
    expect((await followJob(job('cancelled'), done.deps, 1)).status).toBe('cancelled')
    expect(done.events).toEqual([])
    const gone = harness([job('running')], () => false)
    expect((await followJob(job('running'), gone.deps, 1)).status).toBe('running')
    expect(gone.events).toEqual([])
  })
})

describe('isJobRunning', () => {
  it('never treats a job with unknown status as running, so it cannot block planning', () => {
    expect(isJobRunning(job('running'), false)).toBe(true)
    expect(isJobRunning(job('running'), true)).toBe(false)
    expect(isJobRunning(job('completed'), false)).toBe(false)
    expect(isJobRunning(null, false)).toBe(false)
  })
})
