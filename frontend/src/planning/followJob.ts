import type { Job } from '../api/types'
import { TERMINAL_JOB_STATES } from '../api/client'

/** What following a job needs from its host (useWorkspace supplies the real client and state setters). */
export interface FollowJobDeps {
  readonly fetchJob: (jobId: string) => Promise<Job>
  readonly sleep: (ms: number) => Promise<void>
  /** False once the host unmounts; following stops quietly. */
  readonly alive: () => boolean
  /** Each successfully polled state (a success also means the status is known again). */
  readonly onUpdate: (job: Job) => void
  /** A poll failed: the job's real status is unknown. The error is rethrown to the caller. */
  readonly onLost: () => void
}

/** Poll a job until it reaches a terminal state, the host goes away, or a poll fails. */
export async function followJob(job: Job, deps: FollowJobDeps, intervalMs: number): Promise<Job> {
  let current = job
  while (deps.alive() && !TERMINAL_JOB_STATES.has(current.status)) {
    await deps.sleep(intervalMs)
    try {
      current = await deps.fetchJob(job.job_id)
    } catch (err) {
      deps.onLost()
      throw err
    }
    deps.onUpdate(current)
  }
  return current
}

/** A job counts as running only while its status is known; an unknown status never blocks planning. */
export function isJobRunning(job: Pick<Job, 'status'> | null, statusLost: boolean): boolean {
  return job !== null && !TERMINAL_JOB_STATES.has(job.status) && !statusLost
}
