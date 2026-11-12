"""Named runtime validation boundary. Callers supply exact immutable records.

No database, network, human acceptance, scientific validation or implicit latest lookup.
"""

from collections.abc import Callable, Mapping
from pathlib import Path

from .base import Hash, ID, Array, ContractModel
from .profiles import Layout, TreeProfile
from .scenario import Scenario, ScenarioRef
from .site import AssetRef, Readiness, SiteBundle, Target


class ReferenceValidationError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class Capabilities(ContractModel):
    """An explicit runtime allowlist; no capability is inferred from version labels."""

    evaluator_versions: Array[ID]
    solar_versions: Array[ID]
    search_versions: Array[ID]


def validate_operation_supported(envelope, *, supported_operations: frozenset[str]) -> None:
    if envelope.root.operation not in supported_operations:
        raise ReferenceValidationError(
            "UNSUPPORTED_OPERATION", "operation has no implemented handler"
        )


def validate_site_references(
    site: SiteBundle,
    *,
    geometry_refs: frozenset[str],
    target_overlap: Callable[[Target, Target], bool],
) -> None:
    """Trusted importer supplies resolved geometry IDs and an actual overlap test.

    Bounding envelopes alone do not decide whether scored surfaces intersect.
    This callback interface is deliberately not a client-serializable ready flag.
    """
    refs = [t.geometry_ref for t in site.targets]
    refs += [
        f.geometry_ref
        for group in (
            site.planting_regions,
            site.exclusions,
            site.existing_trees,
            site.protected_surfaces,
        )
        for f in group
    ]
    refs += [
        site.coverage.study_extent_ref,
        site.coverage.context_extent_ref,
        *site.coverage.missing_region_refs,
    ]
    if not set(refs) <= geometry_refs:
        raise ReferenceValidationError("INVALID_INPUT", "unresolved geometry reference")
    for index, a in enumerate(site.targets):
        for b in site.targets[index + 1 :]:
            overlap = target_overlap(a, b)
            if type(overlap) is not bool:
                raise ReferenceValidationError("INVALID_INPUT", "geometry overlap is unresolved")
            if overlap:
                raise ReferenceValidationError("INVALID_INPUT", "overlapping target surfaces")


def validate_asset_path(
    ref: AssetRef, root: Path, *, registry: Mapping[str, str] | None = None
) -> Path:
    if ref.registry_id is not None:
        if registry is None or ref.registry_id not in registry:
            raise ReferenceValidationError("INVALID_INPUT", "unresolved asset registry ID")
        # Registry values obey the same relative-path restrictions as direct references.
        ref = AssetRef(relative_path=registry[ref.registry_id])
    root = Path(root).resolve(strict=True)
    try:
        path = (root / ref.relative_path).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ReferenceValidationError("INVALID_INPUT", "asset does not resolve") from exc
    if not path.is_relative_to(root) or not path.is_file():
        raise ReferenceValidationError("INVALID_INPUT", "asset escapes bundle or is not a file")
    return path


def compute_readiness(site: SiteBundle, *, use: str = "local_use_status") -> Readiness:
    if use not in {
        "local_use_status",
        "team_share_status",
        "public_display_status",
        "export_status",
    }:
        raise ValueError("unknown rights use")
    blockers, warnings = [], []
    rights = {r.source_id: r for r in site.rights}
    for asset in site.assets:
        record = rights.get(asset.source_id)
        if record is None or getattr(record, use) != "permitted" or not record.evidence:
            blockers.append(f"{asset.asset_id}: {use} requires evidenced permission")
    if site.vertical_datum.status == "unknown":
        blockers.append("vertical datum unresolved")
    if site.vertical_datum.status == "assumed":
        warnings.append("vertical datum is assumed")
    if site.site_kind == "synthetic_test":
        warnings.append("synthetic test input; no Sheffield claim")
    warnings.extend(site.coverage.horizon_limitations)
    warnings.extend(site.coverage.boundary_limitations)
    if site.coverage.missing_region_refs:
        blockers.append("coverage contains unresolved missing regions")
    if not site.assets or not site.targets:
        blockers.append("assets and targets are required for analysis")
    return Readiness(
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        optional_missing_inputs=(),
        survey_requirements=site.readiness.survey_requirements,
    )


def validate_scenario_ref(
    ref: ScenarioRef, scenarios: Mapping[tuple[str, int], Scenario]
) -> Scenario:
    found = scenarios.get((ref.scenario_id, ref.revision))
    if found is None or (found.scenario_id, found.revision) != (ref.scenario_id, ref.revision):
        raise ReferenceValidationError("UNKNOWN_REVISION", "scenario revision is unresolved")
    if found.scope != ref.scope:
        raise ReferenceValidationError("REVISION_CONFLICT", "scenario scope mismatch")
    return found


def validate_scenario_references(
    scenario: Scenario,
    *,
    site: SiteBundle,
    profiles: Mapping[str, TreeProfile],
    layouts: Mapping[tuple[str, int], Layout],
    scenarios: Mapping[tuple[str, int], Scenario],
    capabilities: Capabilities,
    verified_catalogue_fingerprint: Hash,
    verified_geometry_fingerprint: Hash,
    operation: str | None = None,
) -> None:
    """Validate exact supplied revisions and producer-verified content identities.

    verified_* must come from trusted importer/storage hashes, never client readiness.
    Geometry membership, terrain attachment and arbitrary target intersections remain
    importer/evaluator responsibilities, not inferred by this schema layer.
    """
    inp = scenario.input
    if (
        inp.site_id,
        inp.scene_revision,
        inp.semantic_revision,
        inp.profile_library_revision,
        inp.candidate_catalogue_revision,
        inp.candidate_catalogue_fingerprint,
    ) != (
        site.site_id,
        site.scene_revision,
        site.semantic_revision,
        site.profile_library_revision,
        site.candidate_catalogue_revision,
        site.candidate_catalogue_fingerprint,
    ):
        raise ReferenceValidationError(
            "UNKNOWN_REVISION", "site/profile/catalogue revision or fingerprint mismatch"
        )
    if (
        verified_catalogue_fingerprint != site.candidate_catalogue_fingerprint
        or verified_geometry_fingerprint != site.geometry_fingerprint
    ):
        raise ReferenceValidationError("REVISION_CONFLICT", "verified content fingerprint mismatch")
    if compute_readiness(site).blockers:
        raise ReferenceValidationError("SITE_NOT_READY", "runtime readiness has blockers")
    if scenario.base_scenario_ref is not None:
        validate_scenario_ref(scenario.base_scenario_ref, scenarios)
    targets = {t.target_id: t for t in site.targets}
    if not set(inp.target_ids) <= targets.keys():
        raise ReferenceValidationError("INVALID_INPUT", "unresolved target")
    for name, available in (
        ("accepted_planting_region_ids", {f.feature_id for f in site.planting_regions}),
        ("excluded_region_ids", {f.feature_id for f in site.exclusions}),
    ):
        if not set(getattr(inp.constraints, name)) <= available:
            raise ReferenceValidationError("INVALID_INPUT", "unresolved region")
    required = set(inp.constraints.allowed_profile_ids) | {
        c.profile_id for c in site.candidate_catalogue
    }
    layout = None
    if inp.proposed_layout_ref is not None:
        ref = inp.proposed_layout_ref
        layout = layouts.get((ref.layout_id, ref.revision))
        if layout is None or (layout.layout_id, layout.revision) != (ref.layout_id, ref.revision):
            raise ReferenceValidationError("UNKNOWN_REVISION", "layout revision unresolved")
        required.update(p.profile_id for p in layout.placements)
    for profile_id in required:
        profile = profiles.get(profile_id)
        if (
            profile is None
            or profile.profile_id != profile_id
            or profile.library_revision != inp.profile_library_revision
        ):
            raise ReferenceValidationError("UNKNOWN_REVISION", "profile revision unresolved")
        for case in inp.evaluation_cases:
            state = profile.states.get(case.profile_state)
            if state is None or state.horizon_years != case.horizon_years:
                raise ReferenceValidationError("INVALID_INPUT", "profile state/horizon mismatch")
        if any(
            rule.clearance_state not in profile.states for rule in inp.constraints.spacing_rules
        ):
            raise ReferenceValidationError("INVALID_INPUT", "clearance state unresolved")
    for case in inp.evaluation_cases:
        if any(targets[t].area_basis != case.area_basis for t in case.target_ids):
            raise ReferenceValidationError("INVALID_INPUT", "target area basis mismatch")
        if case.weather_ref is not None:
            raise ReferenceValidationError(
                "UNSUPPORTED_OPERATION", "weather metric capability not implemented"
            )
    catalogue = {c.candidate_id: c for c in site.candidate_catalogue}
    for pair in inp.constraints.incompatible_candidate_pairs:
        if any(c not in catalogue for c in pair):
            raise ReferenceValidationError(
                "INVALID_INPUT", "candidate conflict reference unresolved"
            )
    if layout is not None:
        for placement in layout.placements:
            if placement.profile_id not in inp.constraints.allowed_profile_ids:
                raise ReferenceValidationError("INVALID_INPUT", "placement profile disallowed")
            if placement.candidate_id is not None:
                c = catalogue.get(placement.candidate_id)
                if (
                    c is None
                    or c.plantability_status == "excluded"
                    or (c.location_id, c.profile_id, c.position_enu_m)
                    != (placement.location_id, placement.profile_id, placement.position_enu_m)
                ):
                    raise ReferenceValidationError(
                        "INVALID_INPUT", "placement candidate mismatch or excluded"
                    )
        if any(pin not in layout.placements for pin in inp.constraints.pinned_placements):
            raise ReferenceValidationError("INVALID_INPUT", "pinned placement missing or changed")
    elif inp.constraints.pinned_placements:
        raise ReferenceValidationError("INVALID_INPUT", "pinned placements require layout")
    required_versions = [
        (
            f"{inp.numerics.evaluator}@{inp.numerics.evaluator_version}",
            capabilities.evaluator_versions,
        ),
        (
            f"{inp.numerics.solar_algorithm}@{inp.numerics.solar_version}",
            capabilities.solar_versions,
        ),
    ]
    if operation not in {
        None,
        "evaluate_layout",
        "compare_locations",
        "compare_scenarios",
        "search_layouts",
    }:
        raise ReferenceValidationError("UNSUPPORTED_OPERATION", "unknown analysis operation")
    # Evaluating a supplied layout does not execute the configured search algorithm.
    if operation in {None, "search_layouts"}:
        required_versions.append(
            (f"{inp.search.algorithm}@{inp.search.version}", capabilities.search_versions)
        )
    for label, available in required_versions:
        if label not in available:
            raise ReferenceValidationError(
                "UNSUPPORTED_OPERATION", "runtime algorithm/version unavailable"
            )
