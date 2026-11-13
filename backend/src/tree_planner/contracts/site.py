"""Site ingestion retains unknown evidence. Runtime readiness is derived separately."""

import math
from pathlib import PurePosixPath, PureWindowsPath
from typing import Annotated, Literal

from pydantic import Field, model_validator

from .base import Array, ContractModel, Date, Hash, ID, Matrix4, Positive, Revision, Vec3, unique
from .scenario import AreaBasis

UseStatus = Literal["permitted", "restricted", "unknown"]


class AssetRef(ContractModel):
    registry_id: ID | None = None
    relative_path: ID | None = None

    @model_validator(mode="after")
    def safe_reference(self):
        if (self.registry_id is None) == (self.relative_path is None):
            raise ValueError("exactly one registry_id or relative_path is required")
        if self.relative_path is not None:
            path = self.relative_path
            win, posix = PureWindowsPath(path), PurePosixPath(path)
            if (
                win.drive
                or win.root
                or posix.is_absolute()
                or ":" in path
                or "\\" in path
                or any(p in ("", ".", "..") for p in path.split("/"))
                or any(ord(c) < 32 for c in path)
            ):
                raise ValueError("asset path must be a safe bundle-relative path")
        return self


class Asset(ContractModel):
    asset_id: ID
    ref: AssetRef
    sha256: Hash
    kind: ID
    source_id: ID
    capture_date: Date | Literal["unknown"]
    semantic_class: ID


class Rights(ContractModel):
    source_id: ID
    source_reference: ID
    licence_reference: ID
    required_attribution: str
    local_use_status: UseStatus
    team_share_status: UseStatus
    public_display_status: UseStatus
    export_status: UseStatus
    evidence: Array[ID]


class Origin(ContractModel):
    latitude_deg: Annotated[float, Field(ge=-90, le=90)]
    longitude_deg: Annotated[float, Field(ge=-180, le=180)]
    height_m: float


class VerticalDatum(ContractModel):
    name: ID
    status: Literal["known", "assumed", "unknown"]
    evidence: Array[ID]


class Bounds(ContractModel):
    """Optional axis-aligned ENU envelope; does not establish polygon overlap."""

    minimum_enu_m: Vec3
    maximum_enu_m: Vec3

    @model_validator(mode="after")
    def ordered(self):
        if any(a > b for a, b in zip(self.minimum_enu_m, self.maximum_enu_m)):
            raise ValueError("bounds minimum exceeds maximum")
        return self


class Target(ContractModel):
    target_id: ID
    geometry_ref: ID
    area_basis: AreaBasis
    evidence_status: ID
    source_ids: Array[ID]
    assumption_ids: Array[ID]
    bounds: Bounds | None = None


class SemanticFeature(ContractModel):
    feature_id: ID
    geometry_ref: ID
    evidence_status: ID
    source_ids: Array[ID]
    assumption_ids: Array[ID]


class Candidate(ContractModel):
    candidate_id: ID
    location_id: ID
    position_enu_m: Vec3
    profile_id: ID
    plantability_status: Literal["documented_model_region", "provisional", "excluded"]
    source_ids: Array[ID]
    assumption_ids: Array[ID]


class Coverage(ContractModel):
    study_extent_ref: ID
    context_extent_ref: ID
    missing_region_refs: Array[ID]
    horizon_limitations: Array[ID]
    boundary_limitations: Array[ID]


class Readiness(ContractModel):
    blockers: Array[ID]
    warnings: Array[ID]
    optional_missing_inputs: Array[ID]
    survey_requirements: Array[ID]


class SiteInspection(ContractModel):
    """Scoped metadata; registered handlers do not certify numerical readiness."""

    schema_version: Literal["0.1.0"]
    site_id: ID
    scene_revision: Revision
    semantic_revision: Revision
    site_kind: Literal["real_site", "synthetic_test"]
    geometry_fingerprint: Hash
    readiness: Readiness
    registered_operations: Array[ID]
    source_ids: Array[ID]
    limitations: Array[ID]


class SiteBundle(ContractModel):
    schema_version: Literal["0.1.0"]
    site_id: ID
    scene_revision: Revision
    semantic_revision: Revision
    geometry_fingerprint: Hash
    profile_library_revision: Revision
    candidate_catalogue_revision: Revision
    candidate_catalogue_fingerprint: Hash
    site_kind: Literal["real_site", "synthetic_test"]
    name: ID
    origin: Origin
    # Closed candidate registry, not a promise that an importer is implemented.
    horizontal_crs: Literal["EPSG:27700", "EPSG:4326"]
    vertical_datum: VerticalDatum
    analysis_frame: Literal["enu_m"]
    source_units: ID
    metres_per_source_unit: Positive
    source_true_north: Vec3
    source_up_axis: Vec3
    source_to_analysis: Matrix4
    analysis_to_viewer: Matrix4
    assets: Array[Asset]
    targets: Array[Target]
    planting_regions: Array[SemanticFeature]
    exclusions: Array[SemanticFeature]
    existing_trees: Array[SemanticFeature]
    protected_surfaces: Array[SemanticFeature]
    candidate_catalogue: Array[Candidate]
    rights: Array[Rights]
    coverage: Coverage
    readiness: Readiness

    @model_validator(mode="after")
    def coherent(self):
        north, up = self.source_true_north, self.source_up_axis
        if not math.isclose(sum(x * x for x in north), 1, abs_tol=1e-12):
            raise ValueError("source_true_north must be an explicit unit vector")
        if not math.isclose(sum(x * x for x in up), 1, abs_tol=1e-12):
            raise ValueError("source_up_axis must be an explicit unit vector")
        if abs(sum(x * y for x, y in zip(north, up))) > 1e-12:
            raise ValueError("north and up must be perpendicular")
        # Source transform linear part must map declared source north/up into ENU.
        east = (
            north[1] * up[2] - north[2] * up[1],
            north[2] * up[0] - north[0] * up[2],
            north[0] * up[1] - north[1] * up[0],
        )
        for direction, axis in ((east, 0), (north, 1), (up, 2)):
            transformed = [
                sum(self.source_to_analysis[i][j] * direction[j] for j in range(3))
                for i in range(3)
            ]
            expected = [self.metres_per_source_unit if i == axis else 0 for i in range(3)]
            if any(
                not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
                for a, b in zip(transformed, expected)
            ):
                raise ValueError("source transform conflicts with scale/north/up")
        if self.source_to_analysis[3] != (0, 0, 0, 1):
            raise ValueError("source_to_analysis must be an affine homogeneous transform")
        for collection, key in (
            (self.assets, "asset_id"),
            (self.targets, "target_id"),
            (self.rights, "source_id"),
            (self.candidate_catalogue, "candidate_id"),
        ):
            unique([getattr(item, key) for item in collection], key)
        unique(
            [
                f.feature_id
                for group in (
                    self.planting_regions,
                    self.exclusions,
                    self.existing_trees,
                    self.protected_surfaces,
                )
                for f in group
            ],
            "feature_id",
        )
        unique([t.geometry_ref for t in self.targets], "target surface reference (overlap)")
        locations = {}
        pairs = []
        for candidate in self.candidate_catalogue:
            if (
                candidate.location_id in locations
                and locations[candidate.location_id] != candidate.position_enu_m
            ):
                raise ValueError("location_id must resolve to one position")
            locations[candidate.location_id] = candidate.position_enu_m
            pairs.append((candidate.location_id, candidate.profile_id))
        unique(pairs, "location/profile candidate pair")
        unique(list(locations.values()), "position assigned multiple location IDs")
        # Same-location profile alternatives are intentionally allowed.
        return self
