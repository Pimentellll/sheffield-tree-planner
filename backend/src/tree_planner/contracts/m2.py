"""Output-only input bindings for the explicitly synthetic local UI harness."""

from typing import Annotated, Literal

from pydantic import BeforeValidator, model_validator

from .base import Array, ContractModel, Hash, ID, Positive, Radii, UTC, Vec3, array
from .profiles import Layout, TreeProfile
from .scenario import Scenario
from .site import SiteBundle

Ellipsoid = Annotated[tuple[Vec3, Radii], BeforeValidator(array)]


class M2Scene(ContractModel):
    """The actual explicit numerical declaration, not imported site geometry."""

    kind: Literal["explicit synthetic ENU reference inputs; no geometry importer"]
    target_id: ID
    receiver_point: Vec3
    receiver_normal: Vec3
    receiver_area_m2: Positive
    solar_algorithm: Literal["analytic-chosen-synthetic-direction"]
    solar_version: Literal["1"]
    sun_direction: Vec3
    above_horizon: bool
    midpoint_utc: UTC
    duration_h: Positive
    obstacle_ellipsoids: Array[Ellipsoid]
    evidence: ID

    @model_validator(mode="after")
    def directions(self):
        for direction in (self.receiver_normal, self.sun_direction):
            if abs(sum(value * value for value in direction) - 1) > 1e-9:
                raise ValueError("synthetic declaration requires unit directions")
        if self.above_horizon != (self.sun_direction[2] > 0):
            raise ValueError("horizon flag must match the declared sun direction")
        return self


class M2Session(ContractModel):
    """Read-only exact input snapshot; result numbers are obtained only via jobs."""

    mode: Literal["synthetic_one_tree_reference"]
    session_id: ID
    source_asset_sha256: Hash
    scene: M2Scene
    scenario: Scenario
    site: SiteBundle
    layout: Layout
    profile: TreeProfile

    @model_validator(mode="after")
    def bindings(self):
        inp = self.scenario.input
        if self.scenario.scope != "accepted" or self.site.site_kind != "synthetic_test":
            raise ValueError("M2 exposes an accepted synthetic reference only")
        if (
            inp.site_id != self.site.site_id
            or inp.scene_revision != self.site.scene_revision
            or inp.semantic_revision != self.site.semantic_revision
            or inp.profile_library_revision != self.profile.library_revision
            or inp.proposed_layout_ref.layout_id != self.layout.layout_id
            or inp.proposed_layout_ref.revision != self.layout.revision
            or len(self.layout.placements) != 1
            or self.layout.placements[0].profile_id != self.profile.profile_id
            or len(inp.evaluation_cases) != 1
            or self.scene.target_id not in inp.evaluation_cases[0].target_ids
            or self.scene.solar_algorithm != inp.numerics.solar_algorithm
            or self.scene.solar_version != inp.numerics.solar_version
        ):
            raise ValueError("M2 scene/scenario/layout/profile bindings differ")
        if self.source_asset_sha256 not in {asset.sha256 for asset in self.site.assets}:
            raise ValueError("M2 declaration must cite an admitted site asset")
        return self
