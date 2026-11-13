from datetime import datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import model_validator

from .base import (
    Array,
    ContractModel,
    Hash,
    ID,
    Map,
    Nonnegative,
    NonnegativeInt,
    Positive,
    Revision,
    UTC,
    unique,
)
from .profiles import LayoutRef, Placement

Scope = Literal["accepted", "hypothetical"]
AreaBasis = Literal["surface", "planimetric"]
QuantityKind = Literal[
    "geometric", "blocking_equivalent", "weighted_utility", "direct_incident_energy"
]
Unit = Literal["m", "m2", "h", "m2_h", "weighted_m2_h", "kWh", "kWh_per_m2", "GBP_pence"]


class ScenarioRef(ContractModel):
    scenario_id: ID
    revision: Revision
    scope: Scope


class TimeBin(ContractModel):
    midpoint_utc: UTC
    duration_h: Positive


class EvaluationCase(ContractModel):
    case_id: ID
    role: Literal["benefit", "winter_check", "establishment_report", "sensitivity"]
    profile_state: ID
    horizon_years: Nonnegative
    target_ids: Array[ID]
    time_bins: Array[TimeBin]
    target_weights: Map[ID, Nonnegative]
    source_ids: Array[ID]
    assumption_ids: Array[ID]
    area_basis: AreaBasis
    weather_ref: ID | None = None

    @model_validator(mode="after")
    def intervals(self):
        unique(self.target_ids, "case target_id")
        if not self.target_ids or not self.time_bins:
            raise ValueError("case needs targets and time bins")
        if set(self.target_weights) != set(self.target_ids):
            raise ValueError("every target requires an explicit weight")
        end = None
        for bin_ in self.time_bins:
            middle = datetime.fromisoformat(bin_.midpoint_utc.replace("Z", "+00:00"))
            try:
                half = timedelta(hours=bin_.duration_h / 2)
                start, next_end = middle - half, middle + half
            except OverflowError as exc:
                raise ValueError("time interval out of range") from exc
            if end is not None and start < end:
                raise ValueError("time bins must be sorted and non-overlapping")
            end = next_end
        return self


class SpacingRule(ContractModel):
    minimum_centre_separation_m: Nonnegative
    clearance_state: ID
    model_basis: ID
    evidence: Array[ID]


class WinterLimit(ContractModel):
    case_id: ID
    target_id: ID | None
    maximum_loss_m2_h: Nonnegative


class Constraints(ContractModel):
    budget_pence: NonnegativeInt
    budget_basis: Literal["upfront"]
    max_tree_count: NonnegativeInt | None
    accepted_planting_region_ids: Array[ID]
    excluded_region_ids: Array[ID]
    pinned_placements: Array[Placement]
    spacing_rules: Array[SpacingRule]
    incompatible_candidate_pairs: Array[tuple[ID, ID]]
    allowed_profile_ids: Array[ID]
    at_most_one_profile_per_location: Literal[True]
    winter_limits: Array[WinterLimit]
    survey_requirements: Array[ID]

    @model_validator(mode="after")
    def validate_rules(self):
        # Literal True alone accepts integer 1 in Pydantic; guard via before below.
        for name in ("accepted_planting_region_ids", "excluded_region_ids", "allowed_profile_ids"):
            unique(getattr(self, name), name)
        unique([p.placement_id for p in self.pinned_placements], "pin placement_id")
        unique([p.location_id for p in self.pinned_placements], "pin location_id")
        if any(not p.pinned for p in self.pinned_placements):
            raise ValueError("pinned placements must be pinned")
        if any(a == b for a, b in self.incompatible_candidate_pairs):
            raise ValueError("candidate conflict pair must be distinct")
        unique(
            [tuple(sorted(pair)) for pair in self.incompatible_candidate_pairs],
            "candidate conflict pair",
        )
        unique([(limit.case_id, limit.target_id) for limit in self.winter_limits], "winter limit")
        return self

    @model_validator(mode="before")
    @classmethod
    def strict_boolean(cls, value):
        if (
            isinstance(value, dict)
            and type(value.get("at_most_one_profile_per_location")) is not bool
        ):
            raise ValueError("at_most_one_profile_per_location requires true boolean")
        if isinstance(value, dict):
            value = dict(value)
            pairs = value.get("incompatible_candidate_pairs")
            if type(pairs) is list:
                value["incompatible_candidate_pairs"] = [
                    tuple(p) if type(p) is list else p for p in pairs
                ]
        return value


class Objective(ContractModel):
    kind: Literal["maximise_shade_under_budget", "minimise_cost_for_target"]
    primary_case_id: ID
    target_gain_m2_h: Positive | None = None
    quantity_kind: Literal["geometric", "blocking_equivalent"]

    @model_validator(mode="after")
    def target_mode(self):
        if (self.kind == "minimise_cost_for_target") != (self.target_gain_m2_h is not None):
            raise ValueError("positive target gain is required only for target objective")
        return self


class Numerics(ContractModel):
    evaluator: ID
    evaluator_version: ID
    spatial_spacing_m: Positive
    ray_offset_m: Positive
    intersection_tolerance_m: Nonnegative
    feasibility_tolerance: Nonnegative
    solar_algorithm: ID
    solar_version: ID
    quadrature: Literal["midpoint"]


class Search(ContractModel):
    algorithm: ID
    version: ID
    seed: int
    comparison_policy: ID
    reference_policy: ID
    deadline_utc: UTC


class ScenarioInput(ContractModel):
    schema_version: Literal["0.1.0"]
    site_id: ID
    scene_revision: Revision
    semantic_revision: Revision
    profile_library_revision: Revision
    candidate_catalogue_revision: Revision
    candidate_catalogue_fingerprint: Hash
    display_time_zone: ID
    target_ids: Array[ID]
    evaluation_cases: Array[EvaluationCase]
    constraints: Constraints
    objective: Objective
    numerics: Numerics
    search: Search
    assumptions: Array[ID]
    proposed_layout_ref: LayoutRef | None

    @model_validator(mode="after")
    def cases(self):
        try:
            ZoneInfo(self.display_time_zone)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("unknown display time zone") from exc
        unique(self.target_ids, "scenario target_id")
        unique([c.case_id for c in self.evaluation_cases], "case_id")
        cases = {c.case_id: c for c in self.evaluation_cases}
        primary = cases.get(self.objective.primary_case_id)
        if primary is None or primary.role != "benefit":
            raise ValueError("objective requires one primary benefit case")
        if any(not set(c.target_ids) <= set(self.target_ids) for c in self.evaluation_cases):
            raise ValueError("case has unresolved scenario target")
        for limit in self.constraints.winter_limits:
            case = cases.get(limit.case_id)
            if case is None or case.role != "winter_check":
                raise ValueError("winter limit requires a declared winter_check case")
            if limit.target_id is not None and limit.target_id not in case.target_ids:
                raise ValueError("winter limit target unresolved")
        return self


class Scenario(ContractModel):
    schema_version: Literal["0.1.0"]
    scenario_id: ID
    revision: Revision
    created_at_utc: UTC
    scope: Scope
    base_scenario_ref: ScenarioRef | None
    input: ScenarioInput

    @model_validator(mode="after")
    def accepted_base(self):
        if self.base_scenario_ref is not None and self.base_scenario_ref.scope != "accepted":
            raise ValueError("base must reference an accepted scenario")
        return self
