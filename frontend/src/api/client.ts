import type {
  ContractError,
  Health,
  Job,
  JobRequest,
  Layout,
  Result,
  Scenario,
  ScenarioInput_Input,
  ScenarioRef,
  ScenarioSelections,
  SiteBundle,
  TreeProfile,
} from './types'

/** A typed backend failure. `contract` is the backend's ContractError body when one was returned. */
export class ApiError extends Error {
  readonly status: number
  readonly contract: ContractError | null

  constructor(status: number, contract: ContractError | null, fallback: string) {
    super(contract ? `${contract.code}: ${contract.message}` : fallback)
    this.name = 'ApiError'
    this.status = status
    this.contract = contract
  }

  get code(): string {
    return this.contract?.code ?? (this.status === 0 ? 'NETWORK' : `HTTP_${this.status}`)
  }
}

const isContractError = (value: unknown): value is ContractError =>
  typeof value === 'object' && value !== null && typeof (value as ContractError).code === 'string' &&
  typeof (value as ContractError).message === 'string'

export type FetchLike = (input: string, init?: RequestInit) => Promise<Response>

/**
 * Thin client over the implemented CANOPY HTTP API. It never synthesises a response:
 * every value returned here was parsed from an actual backend reply.
 */
export class CanopyClient {
  private readonly base: string
  private readonly fetcher: FetchLike

  constructor(base = '/api/v1', fetcher: FetchLike = (input, init) => fetch(input, init)) {
    this.base = base.replace(/\/$/, '')
    this.fetcher = fetcher
  }

  private async request<T>(method: string, path: string, body?: unknown, headers: Record<string, string> = {}): Promise<T> {
    let response: Response
    try {
      response = await this.fetcher(this.base + path, {
        method,
        headers: body === undefined ? headers : { 'Content-Type': 'application/json', ...headers },
        body: body === undefined ? undefined : JSON.stringify(body),
        cache: 'no-store',
      })
    } catch (error) {
      throw new ApiError(0, null, `Backend unreachable: ${error instanceof Error ? error.message : String(error)}`)
    }
    let parsed: unknown = null
    const text = await response.text()
    if (text) {
      try {
        parsed = JSON.parse(text)
      } catch {
        throw new ApiError(response.status, null, `Backend returned non-JSON (HTTP ${response.status})`)
      }
    }
    if (!response.ok) {
      const contract = isContractError(parsed) ? parsed : null
      // A 5xx without a contract error body comes from the dev proxy or gateway, not the evaluator: the backend
      // process is not answering. Say so instead of a bare status code (#56 failure states).
      throw new ApiError(response.status, contract, !contract && response.status >= 500
        ? `The local backend did not answer (HTTP ${response.status}). Nothing was computed. Check that the backend is running, then reload this page.`
        : `HTTP ${response.status}`)
    }
    return parsed as T
  }

  health() { return this.request<Health>('GET', '/health') }

  site(siteId: string, sceneRevision: number, semanticRevision: number) {
    return this.request<SiteBundle>('GET', `/sites/${encodeURIComponent(siteId)}?scene_revision=${sceneRevision}&semantic_revision=${semanticRevision}`)
  }

  profile(profileId: string, libraryRevision: number) {
    return this.request<TreeProfile>('GET', `/profiles/${encodeURIComponent(profileId)}?library_revision=${libraryRevision}`)
  }

  layout(layoutId: string, revision: number) {
    return this.request<Layout>('GET', `/layouts/${encodeURIComponent(layoutId)}?revision=${revision}`)
  }

  registerLayout(layout: Layout) { return this.request<Layout>('POST', '/layouts', layout) }

  scenario(ref: Pick<ScenarioRef, 'scenario_id' | 'revision'> & { scope?: ScenarioRef['scope'] }) {
    return this.request<Scenario>('GET', `/scenarios/${encodeURIComponent(ref.scenario_id)}?revision=${ref.revision}&scope=${ref.scope ?? 'accepted'}`)
  }

  /** Replace an accepted scenario; the backend rejects a stale `ifMatch` with REVISION_CONFLICT. */
  replaceScenario(scenarioId: string, input: ScenarioInput_Input, ifMatch: number) {
    return this.request<Scenario>('PUT', `/scenarios/${encodeURIComponent(scenarioId)}`, input, { 'If-Match': `"${ifMatch}"` })
  }

  /** Human acceptance of a hypothetical draft; If-Match is the accepted base (head) revision. */
  acceptScenario(hypothetical: ScenarioRef, ifMatchBase: number) {
    return this.request<Scenario>('POST', '/scenarios/accept', hypothetical, { 'If-Match': `"${ifMatchBase}"` })
  }

  selections(ref: ScenarioRef) {
    return this.request<ScenarioSelections>('GET', `/scenarios/${encodeURIComponent(ref.scenario_id)}/selections?revision=${ref.revision}&scope=${ref.scope}`)
  }

  submitJob(request: JobRequest) { return this.request<Job>('POST', '/jobs', request) }
  job(jobId: string) { return this.request<Job>('GET', `/jobs/${encodeURIComponent(jobId)}`) }
  cancelJob(jobId: string) { return this.request<Job>('POST', `/jobs/${encodeURIComponent(jobId)}/cancel`) }
  result(runId: string) { return this.request<Result>('GET', `/results/${encodeURIComponent(runId)}`) }

  /**
   * There is no "latest revision" endpoint. Starting from a known revision, step forward
   * until the backend reports UNKNOWN_REVISION, so a reload does not edit an old head.
   */
  async latestScenario(scenarioId: string, known: number, limit = 500): Promise<Scenario> {
    let current = await this.scenario({ scenario_id: scenarioId, revision: known })
    for (let i = 0; i < limit; i += 1) {
      try {
        current = await this.scenario({ scenario_id: scenarioId, revision: current.revision + 1 })
      } catch (error) {
        if (error instanceof ApiError && error.code === 'UNKNOWN_REVISION') return current
        throw error
      }
    }
    throw new ApiError(0, null, 'Scenario revision probe limit reached')
  }
}

export const TERMINAL_JOB_STATES = new Set<Job['status']>(['completed', 'failed', 'cancelled'])
