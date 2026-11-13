"""Operation envelopes describe wire shapes, never authority to execute a tool."""

from typing import Annotated, Literal

from pydantic import ConfigDict, Field, RootModel

from .base import Array, ContractModel, ID, Revision, Vec3
from .profiles import LayoutRef
from .scenario import ScenarioInput, ScenarioRef

AsyncOperation = Literal[
    "evaluate_layout", "search_layouts", "compare_locations", "compare_scenarios"
]
Operation = Literal[
    "inspect_site",
    "prepare_scenario",
    "evaluate_layout",
    "search_layouts",
    "compare_locations",
    "compare_scenarios",
    "prepare_proposal",
]


class InspectSiteArguments(ContractModel):
    site_id: ID
    scene_revision: Revision


class PrepareScenarioArguments(ContractModel):
    base_scenario_ref: ScenarioRef | None
    # A full replacement candidate avoids untyped JSON patch/approval fields.
    proposed_edits: ScenarioInput


class EvaluateLayoutArguments(ContractModel):
    layout_ref: LayoutRef


class SearchLayoutsArguments(ContractModel):
    pass


class CompareLocationsArguments(ContractModel):
    layout_ref: LayoutRef
    placement_id: ID
    alternative_position_enu_m: Vec3


class CompareScenariosArguments(ContractModel):
    base_scenario_ref: ScenarioRef
    alternative_scenario_ref: ScenarioRef
    layout_refs: Array[LayoutRef]
    mode: Literal["fixed_layout", "redesign"]


class ResultRef(ContractModel):
    run_id: ID


class PrepareProposalArguments(ContractModel):
    result_refs: Array[ResultRef]


class InspectSiteRequest(ContractModel):
    request_id: ID
    operation: Literal["inspect_site"]
    arguments: InspectSiteArguments


class PrepareScenarioRequest(ContractModel):
    request_id: ID
    operation: Literal["prepare_scenario"]
    arguments: PrepareScenarioArguments


class EvaluateLayoutRequest(ContractModel):
    request_id: ID
    scenario_ref: ScenarioRef
    operation: Literal["evaluate_layout"]
    arguments: EvaluateLayoutArguments


class SearchLayoutsRequest(ContractModel):
    request_id: ID
    scenario_ref: ScenarioRef
    operation: Literal["search_layouts"]
    arguments: SearchLayoutsArguments


class CompareLocationsRequest(ContractModel):
    request_id: ID
    scenario_ref: ScenarioRef
    operation: Literal["compare_locations"]
    arguments: CompareLocationsArguments


class CompareScenariosRequest(ContractModel):
    request_id: ID
    scenario_ref: ScenarioRef
    operation: Literal["compare_scenarios"]
    arguments: CompareScenariosArguments


class PrepareProposalRequest(ContractModel):
    request_id: ID
    operation: Literal["prepare_proposal"]
    arguments: PrepareProposalArguments


JobRequestType = Annotated[
    EvaluateLayoutRequest
    | SearchLayoutsRequest
    | CompareLocationsRequest
    | CompareScenariosRequest,
    Field(discriminator="operation"),
]


class JobRequest(RootModel[JobRequestType]):
    model_config = ConfigDict(strict=True, frozen=True)


class OperationEnvelope(
    RootModel[
        Annotated[
            InspectSiteRequest
            | PrepareScenarioRequest
            | EvaluateLayoutRequest
            | SearchLayoutsRequest
            | CompareLocationsRequest
            | CompareScenariosRequest
            | PrepareProposalRequest,
            Field(discriminator="operation"),
        ]
    ]
):
    model_config = ConfigDict(strict=True, frozen=True)


def operation_slot(operation: str) -> str:
    return {
        "evaluate_layout": "evaluation",
        "search_layouts": "search",
        "compare_locations": "comparison",
        "compare_scenarios": "comparison",
    }[operation]
