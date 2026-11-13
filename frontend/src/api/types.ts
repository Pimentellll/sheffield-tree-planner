// Wire types come only from the backend-generated file. Do not redefine them here.
export type {
  ContractError,
  Delivery,
  EvaluatedLayout,
  Job,
  JobRequest,
  Layout,
  Metric,
  Placement,
  Provenance,
  Result,
  Scenario,
  ScenarioInput_Input,
  ScenarioRef,
  ScenarioSelections,
  SiteBundle_Output as SiteBundle,
  SlotState,
  TreeProfile_Output as TreeProfile,
  TreeState,
} from '../../../generated/http'

export type Vec3 = readonly [number, number, number]

/** Fields from GET /api/v1/health. The backend returns an untyped dict, so this is read defensively. */
export interface Health {
  readonly status: string
  readonly version: string
  readonly schema_version: string
  readonly worker_mode: string
  readonly available_operations: readonly string[]
}
