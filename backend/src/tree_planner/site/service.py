"""Typed persistence boundary. Server dispatcher owns human authority and dependencies."""

from datetime import datetime, timezone
from uuid import uuid4
import hashlib

from tree_planner.canonical import canonical_bytes, content_hash
from tree_planner.contracts import (
    SiteBundle,
    TreeProfile,
    Layout,
    Scenario,
    ScenarioInput,
    ScenarioRef,
    Capabilities,
    compute_readiness,
    validate_site_references,
    validate_scenario_references,
    ReferenceValidationError,
)
from .repository import DomainError
from .assets import PURPOSES


def _dump(model):
    return model.model_dump(mode="json", exclude_none=False)


def geometry_fingerprint(assets):
    """Backend content identity, not a scientific geometry validation."""
    records = [
        {k: getattr(a, k) for k in ("asset_id", "sha256", "kind", "semantic_class")} for a in assets
    ]
    return content_hash(sorted(records, key=lambda x: tuple(x.values())))


def catalogue_fingerprint(candidates):
    return content_hash([_dump(c) for c in candidates])


def _key(*parts):
    return content_hash(list(parts))


def _ref(kind, key, scope=None):
    result = {"kind": kind, "id": key, "revision": 1}
    if scope:
        result["scope"] = scope
    return result


class ScenarioService:
    def __init__(
        self,
        repository,
        assets,
        capabilities: Capabilities,
        *,
        geometry_refs=None,
        target_overlap=None,
    ):
        if (
            not isinstance(capabilities, Capabilities)
            or assets.repository.db_path != repository.db_path
        ):
            raise ValueError("Explicit capabilities and a shared repository are required")
        self.repository, self.assets, self.capabilities = repository, assets, capabilities
        self.geometry_refs, self.target_overlap = geometry_refs, target_overlap
        with repository.transaction() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS scenario_acceptances (hyp_id TEXT NOT NULL, hyp_rev INTEGER NOT NULL, PRIMARY KEY(hyp_id,hyp_rev))"
            )

    def _put(self, kind, key, value):
        with self.repository.transaction() as db:
            ref = _ref(kind, key)
            try:
                old = self.repository._get(db, ref)
            except DomainError as exc:
                if exc.code != "UNKNOWN_REVISION":
                    raise
                self.repository._insert(db, kind, key, 1, "", _dump(value))
            else:
                if canonical_bytes(old["value"]) != canonical_bytes(_dump(value)):
                    raise DomainError(
                        "REVISION_CONFLICT", "Immutable identity has different content"
                    )
        return value

    def _load(self, db, kind, key, cls):
        return cls.model_validate(self.repository._get(db, _ref(kind, key))["value"])

    def _verify_assets(self, site):
        rights = {r.source_id: r for r in site.rights}
        for r in site.rights:
            source = self.assets.get_source(r.source_id)
            statuses = {p: getattr(r, p) for p in PURPOSES}
            if (r.source_reference, r.licence_reference, list(r.evidence), statuses) != (
                source["source_reference"],
                source["licence_reference"],
                source["evidence"],
                source["rights"],
            ):
                raise DomainError("REVISION_CONFLICT", "Source rights evidence mismatch")
        for asset in site.assets:
            if asset.ref.registry_id is None:
                raise DomainError(
                    "UNSUPPORTED_OPERATION", "Relative asset imports require a trusted importer"
                )
            item = self.assets.get(asset.ref.registry_id)
            source = self.assets.get_source(asset.source_id)
            r = rights.get(asset.source_id)
            if (
                r is None
                or item["source_id"] != asset.source_id
                or item["sha256"] != asset.sha256
                or item["capture_date"] != asset.capture_date
            ):
                raise DomainError("REVISION_CONFLICT", "Asset source or digest mismatch")
            statuses = {p: getattr(r, p) for p in PURPOSES}
            if (r.source_reference, r.licence_reference, list(r.evidence), statuses) != (
                source["source_reference"],
                source["licence_reference"],
                source["evidence"],
                source["rights"],
            ) or (
                item["source_reference"],
                item["licence_reference"],
                item["evidence"],
                item["rights"],
            ) != (
                source["source_reference"],
                source["licence_reference"],
                source["evidence"],
                source["rights"],
            ):
                raise DomainError("REVISION_CONFLICT", "Source rights evidence mismatch")
            try:
                digest = hashlib.sha256(
                    self.assets._path(item["relative_path"]).read_bytes()
                ).hexdigest()
            except OSError as exc:
                raise DomainError("INVALID_INPUT", "Asset unavailable") from exc
            if digest != asset.sha256:
                raise DomainError("REVISION_CONFLICT", "Asset content changed")

    def register_site(self, site: SiteBundle) -> SiteBundle:
        if not isinstance(site, SiteBundle):
            raise TypeError("SiteBundle required")
        self._verify_assets(site)
        if (
            geometry_fingerprint(site.assets) != site.geometry_fingerprint
            or catalogue_fingerprint(site.candidate_catalogue)
            != site.candidate_catalogue_fingerprint
        ):
            raise DomainError("REVISION_CONFLICT", "Site content fingerprint mismatch")
        return self._put(
            "typed_site", _key(site.site_id, site.scene_revision, site.semantic_revision), site
        )

    def get_site(self, site_id: str, scene_revision: int, semantic_revision: int) -> SiteBundle:
        with self.repository.transaction() as db:
            site = self._load(
                db, "typed_site", _key(site_id, scene_revision, semantic_revision), SiteBundle
            )
        self._verify_assets(site)
        if (
            geometry_fingerprint(site.assets) != site.geometry_fingerprint
            or catalogue_fingerprint(site.candidate_catalogue)
            != site.candidate_catalogue_fingerprint
        ):
            raise DomainError("REVISION_CONFLICT", "Site content fingerprint mismatch")
        return site

    def readiness(
        self,
        site_id: str,
        scene_revision: int,
        semantic_revision: int,
        *,
        use: str = "local_use_status",
    ):
        return compute_readiness(self.get_site(site_id, scene_revision, semantic_revision), use=use)

    def register_profile(self, profile: TreeProfile) -> TreeProfile:
        if not isinstance(profile, TreeProfile):
            raise TypeError("TreeProfile required")
        return self._put(
            "typed_profile", _key(profile.profile_id, profile.library_revision), profile
        )

    def get_profile(self, profile_id: str, library_revision: int) -> TreeProfile:
        with self.repository.transaction() as db:
            return self._load(db, "typed_profile", _key(profile_id, library_revision), TreeProfile)

    def register_layout(self, layout: Layout) -> Layout:
        if not isinstance(layout, Layout):
            raise TypeError("Layout required")
        return self._put("typed_layout", _key(layout.layout_id, layout.revision), layout)

    def get_layout(self, layout_id: str, revision: int) -> Layout:
        with self.repository.transaction() as db:
            return self._load(db, "typed_layout", _key(layout_id, revision), Layout)

    def _scenario(self, db, ref):
        if not isinstance(ref, ScenarioRef):
            raise TypeError("ScenarioRef required")
        scenario = Scenario.model_validate(
            self.repository._get(
                db,
                {
                    "kind": "scenario",
                    "id": ref.scenario_id,
                    "revision": ref.revision,
                    "scope": ref.scope,
                },
            )["value"]
        )
        if (scenario.scenario_id, scenario.revision, scenario.scope) != (
            ref.scenario_id,
            ref.revision,
            ref.scope,
        ):
            raise DomainError("REVISION_CONFLICT", "Scenario identity mismatch")
        return scenario

    def current_accepted_ref(self, scenario_id: str) -> ScenarioRef:
        """Read explicit head metadata for actor authorisation, not snapshot fallback."""
        head = self.repository.head_reference("scenario", scenario_id)
        if head.get("scope") != "accepted":
            raise DomainError("REVISION_CONFLICT", "An accepted task is required")
        return ScenarioRef(scenario_id=head["id"], revision=head["revision"], scope="accepted")

    def get_scenario(self, ref: ScenarioRef) -> Scenario:
        with self.repository.transaction() as db:
            return self._scenario(db, ref)

    def acceptance_source(self, ref: ScenarioRef) -> ScenarioRef | None:
        with self.repository.transaction() as db:
            self._scenario(db, ref)
            item = self.repository._get(
                db,
                {
                    "kind": "scenario",
                    "id": ref.scenario_id,
                    "revision": ref.revision,
                    "scope": ref.scope,
                },
            )
            return (
                ScenarioRef.model_validate(item["source_ref"])
                if item["source_ref"] is not None
                else None
            )

    def _dependencies(self, inp):
        site = self.get_site(inp.site_id, inp.scene_revision, inp.semantic_revision)
        if (
            inp.profile_library_revision,
            inp.candidate_catalogue_revision,
            inp.candidate_catalogue_fingerprint,
        ) != (
            site.profile_library_revision,
            site.candidate_catalogue_revision,
            site.candidate_catalogue_fingerprint,
        ):
            raise DomainError("UNKNOWN_REVISION", "Site catalogue or library revision mismatch")
        targets = {x.target_id: x for x in site.targets}
        if not set(inp.target_ids) <= targets.keys():
            raise DomainError("INVALID_INPUT", "Unresolved target")
        for field, group in [
            ("accepted_planting_region_ids", site.planting_regions),
            ("excluded_region_ids", site.exclusions),
        ]:
            if not set(getattr(inp.constraints, field)) <= {x.feature_id for x in group}:
                raise DomainError("INVALID_INPUT", "Unresolved region")
        layout = (
            self.get_layout(inp.proposed_layout_ref.layout_id, inp.proposed_layout_ref.revision)
            if inp.proposed_layout_ref
            else None
        )
        ids = set(inp.constraints.allowed_profile_ids) | {
            c.profile_id for c in site.candidate_catalogue
        }
        if layout:
            ids.update(p.profile_id for p in layout.placements)
        profiles = {i: self.get_profile(i, inp.profile_library_revision) for i in ids}
        for profile in profiles.values():
            for case in inp.evaluation_cases:
                state = profile.states.get(case.profile_state)
                if state is None or state.horizon_years != case.horizon_years:
                    raise DomainError("INVALID_INPUT", "Profile state or horizon mismatch")
            if any(
                rule.clearance_state not in profile.states for rule in inp.constraints.spacing_rules
            ):
                raise DomainError("INVALID_INPUT", "Clearance state unresolved")
        if any(
            targets[t].area_basis != case.area_basis
            for case in inp.evaluation_cases
            for t in case.target_ids
        ):
            raise DomainError("INVALID_INPUT", "Target area basis mismatch")
        candidates = {c.candidate_id: c for c in site.candidate_catalogue}
        if any(
            c not in candidates
            for pair in inp.constraints.incompatible_candidate_pairs
            for c in pair
        ):
            raise DomainError("INVALID_INPUT", "Candidate reference unresolved")
        if layout:
            for p in layout.placements:
                if p.profile_id not in inp.constraints.allowed_profile_ids:
                    raise DomainError("INVALID_INPUT", "Placement profile disallowed")
                if p.candidate_id is not None:
                    c = candidates.get(p.candidate_id)
                    if (
                        c is None
                        or c.plantability_status == "excluded"
                        or (c.location_id, c.profile_id, c.position_enu_m)
                        != (p.location_id, p.profile_id, p.position_enu_m)
                    ):
                        raise DomainError("INVALID_INPUT", "Placement candidate mismatch")
            if any(pin not in layout.placements for pin in inp.constraints.pinned_placements):
                raise DomainError("INVALID_INPUT", "Pinned placement missing")
        elif inp.constraints.pinned_placements:
            raise DomainError("INVALID_INPUT", "Pinned placements require layout")
        return site, profiles, layout

    def _analysis_sources(self, site, profiles, inp):
        """Resolve exact registry IDs and require evidenced local permission.

        site.rights declares asset rights; it is not a closed manifest of profile,
        case or semantic sources. Every cited ID must independently resolve in the
        registry. Explicit assumptions may remain assumptions; free-text evidence
        labels and client readiness never substitute for provenance or permission.
        Layout/pin profiles and catalogue profiles are included by _dependencies.
        """
        records = [
            *site.targets,
            *site.planting_regions,
            *site.exclusions,
            *site.existing_trees,
            *site.protected_surfaces,
            *site.candidate_catalogue,
            *profiles.values(),
            *inp.evaluation_cases,
        ]
        if any(not record.source_ids and not record.assumption_ids for record in records):
            raise DomainError("RIGHTS_UNKNOWN", "Source or assumption declaration is missing")
        ids = {r.source_id for r in site.rights} | {a.source_id for a in site.assets}
        ids.update(source_id for record in records for source_id in record.source_ids)
        sources = {source_id: self.assets.get_source(source_id) for source_id in sorted(ids)}
        for source in sources.values():
            if source["rights"]["local_use_status"] == "restricted":
                raise DomainError("RIGHTS_RESTRICTED", "Local source use is restricted")
            if source["rights"]["local_use_status"] != "permitted" or not source["evidence"]:
                raise DomainError("RIGHTS_UNKNOWN", "Local source permission is not evidenced")
        return sources

    def _new(self, id_, rev, scope, inp, base):
        return Scenario(
            schema_version="0.1.0",
            scenario_id=id_,
            revision=rev,
            created_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            scope=scope,
            base_scenario_ref=base,
            input=inp,
        )

    def _insert_scenario(self, db, scenario, source=None):
        self.repository._insert(
            db,
            "scenario",
            scenario.scenario_id,
            scenario.revision,
            scenario.scope,
            _dump(scenario),
            source,
        )
        return scenario

    def prepare_scenario(
        self, input: ScenarioInput, *, base_ref: ScenarioRef | None = None
    ) -> Scenario:
        if not isinstance(input, ScenarioInput):
            raise TypeError("ScenarioInput required")
        self._dependencies(input)
        with self.repository.transaction() as db:
            if base_ref is not None:
                if base_ref.scope != "accepted":
                    raise DomainError("REVISION_CONFLICT", "Base must be accepted")
                self._scenario(db, base_ref)
            return self._insert_scenario(
                db, self._new(uuid4().hex, 1, "hypothetical", input, base_ref)
            )

    def create_accepted(self, input: ScenarioInput, *, on_accept=None) -> Scenario:
        if not isinstance(input, ScenarioInput):
            raise TypeError("ScenarioInput required")
        self._dependencies(input)
        with self.repository.transaction() as db:
            result = self._insert_scenario(db, self._new(uuid4().hex, 1, "accepted", input, None))
            if on_accept:
                on_accept(result.scenario_id, result.revision, connection=db)
            return result

    def replace_accepted(
        self, ref: ScenarioRef, input: ScenarioInput, *, if_match: int, on_accept=None
    ) -> Scenario:
        if not isinstance(input, ScenarioInput):
            raise TypeError("ScenarioInput required")
        self._dependencies(input)
        with self.repository.transaction() as db:
            old = self._scenario(db, ref)
            head = db.execute(
                "SELECT revision FROM heads WHERE kind=? AND id=?", ("scenario", ref.scenario_id)
            ).fetchone()[0]
            if (
                ref.scope != "accepted"
                or head != ref.revision
                or type(if_match) is not int
                or if_match != ref.revision
            ):
                raise DomainError("REVISION_CONFLICT", "Accepted head changed")
            result = self._insert_scenario(
                db, self._new(old.scenario_id, head + 1, "accepted", input, ref)
            )
            if on_accept:
                on_accept(result.scenario_id, result.revision, connection=db)
            return result

    def accept_scenario(self, ref: ScenarioRef, *, if_match: int, on_accept=None) -> Scenario:
        draft = self.get_scenario(ref)
        self._dependencies(draft.input)
        with self.repository.transaction() as db:
            draft = self._scenario(db, ref)
            base = draft.base_scenario_ref
            if ref.scope != "hypothetical" or base is None:
                raise DomainError("REVISION_CONFLICT", "Hypothetical requires accepted base")
            self._scenario(db, base)
            head = db.execute(
                "SELECT revision FROM heads WHERE kind=? AND id=?", ("scenario", base.scenario_id)
            ).fetchone()[0]
            if (
                head != base.revision
                or type(if_match) is not int
                or if_match != base.revision
                or db.execute(
                    "SELECT 1 FROM scenario_acceptances WHERE hyp_id=? AND hyp_rev=?",
                    (ref.scenario_id, ref.revision),
                ).fetchone()
            ):
                raise DomainError("REVISION_CONFLICT", "Base changed or draft already accepted")
            result = self._insert_scenario(
                db, self._new(base.scenario_id, head + 1, "accepted", draft.input, base), _dump(ref)
            )
            db.execute(
                "INSERT INTO scenario_acceptances VALUES (?,?)", (ref.scenario_id, ref.revision)
            )
            if on_accept:
                on_accept(result.scenario_id, result.revision, connection=db)
            return result

    def resolve_for_job(self, ref: ScenarioRef, *, operation: str | None = None):
        """Resolve immutable inputs; the dispatcher separately authorises task scope."""
        scenario = self.get_scenario(ref)
        if scenario.scope == "hypothetical":
            if scenario.base_scenario_ref is None:
                raise DomainError(
                    "REVISION_CONFLICT", "Hypothetical analysis requires an accepted base"
                )
            base = self.get_scenario(scenario.base_scenario_ref)
            if base.scope != "accepted":
                raise DomainError("REVISION_CONFLICT", "Hypothetical base must be accepted")
        site, profiles, layout = self._dependencies(scenario.input)
        sources = self._analysis_sources(site, profiles, scenario.input)
        if self.geometry_refs is None or (len(site.targets) > 1 and self.target_overlap is None):
            raise DomainError("SITE_NOT_READY", "Trusted geometry producer unavailable")
        try:
            validate_site_references(
                site, geometry_refs=self.geometry_refs, target_overlap=self.target_overlap
            )
            base = (
                self.get_scenario(scenario.base_scenario_ref)
                if scenario.base_scenario_ref
                else None
            )
            scenarios = {(base.scenario_id, base.revision): base} if base else {}
            layouts = {(layout.layout_id, layout.revision): layout} if layout else {}
            validate_scenario_references(
                scenario,
                site=site,
                profiles=profiles,
                layouts=layouts,
                scenarios=scenarios,
                capabilities=self.capabilities,
                verified_catalogue_fingerprint=catalogue_fingerprint(site.candidate_catalogue),
                verified_geometry_fingerprint=geometry_fingerprint(site.assets),
                operation=operation,
            )
        except ReferenceValidationError as exc:
            raise DomainError(exc.code, str(exc)) from exc
        dependencies = {
            "scenario": _dump(scenario),
            "base_scenario": _dump(base) if base else None,
            "site": _dump(site),
            "readiness": _dump(compute_readiness(site)),
            "profiles": {k: _dump(v) for k, v in sorted(profiles.items())},
            "layout": _dump(layout) if layout else None,
            "assets": {a.asset_id: self.assets.get(a.ref.registry_id) for a in site.assets},
            "sources": sources,
        }
        hashes = {
            "scenario": content_hash(dependencies["scenario"]),
            "site": content_hash(dependencies["site"]),
            "catalogue": catalogue_fingerprint(site.candidate_catalogue),
            "geometry": geometry_fingerprint(site.assets),
            **{f"profile:{k}": content_hash(v) for k, v in dependencies["profiles"].items()},
        }
        if base:
            hashes["base_scenario"] = content_hash(dependencies["base_scenario"])
        if layout:
            hashes["layout"] = content_hash(dependencies["layout"])
        hashes["assets"] = content_hash(dependencies["assets"])
        hashes["sources"] = content_hash(dependencies["sources"])
        return dependencies, hashes

    def agent(self):
        return _AgentService(self)


class _AgentService:
    def __init__(self, service):
        self.__service = service

    def get_scenario(self, ref: ScenarioRef) -> Scenario:
        return self.__service.get_scenario(ref)

    def prepare_scenario(
        self, input: ScenarioInput, *, base_ref: ScenarioRef | None = None
    ) -> Scenario:
        return self.__service.prepare_scenario(input, base_ref=base_ref)


PlanningRepository = ScenarioService
