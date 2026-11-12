"""Trusted HTTP composition; no evaluator, network client or model callbacks.

Human methods are local dispatcher authority, not multi-user OS authentication.
The workspace lease must also be respected by any non-HTTP worker process.
"""

from collections.abc import Mapping
from contextlib import contextmanager
from pathlib import Path
import os
import re
import threading
from types import MappingProxyType
from uuid import uuid4

from tree_planner.canonical import content_hash
from tree_planner.contracts import (
    Capabilities,
    JobRequest,
    OperationEnvelope,
    Scenario,
    ScenarioRef,
)
from tree_planner.jobs import JobStore
from tree_planner.site.assets import AssetRegistry
from tree_planner.site.repository import DomainError, Repository
from tree_planner.site.service import ScenarioService

ASYNC_OPERATIONS = frozenset(
    {"evaluate_layout", "search_layouts", "compare_locations", "compare_scenarios"}
)


class WorkspaceLease:
    """An actual nonblocking OS file lock, held through recovery and execution."""

    def __init__(self, workspace: Path):
        self.path = workspace / ".canopy-worker.lock"
        self._guard = threading.Lock()
        self._file = None

    def acquire(self):
        if not self._guard.acquire(blocking=False):
            raise DomainError("TOOL_UNAVAILABLE", "Workspace worker is already owned", True)
        handle = None
        try:
            handle = self.path.open("a+b")
            if handle.seek(0, os.SEEK_END) == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._file = handle
        except BaseException as exc:
            if handle is not None:
                handle.close()
            self._guard.release()
            if isinstance(exc, OSError):
                raise DomainError(
                    "TOOL_UNAVAILABLE", "Workspace worker is unavailable", True
                ) from exc
            raise

    def release(self):
        if self._file is not None:
            handle, self._file = self._file, None
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                handle.close()
                self._guard.release()

    @contextmanager
    def held(self):
        self.acquire()
        try:
            yield
        finally:
            self.release()


class ApplicationService:
    def __init__(
        self,
        workspace: Path,
        *,
        handlers: Mapping | None = None,
        capabilities: Capabilities | None = None,
        approved_asset_root: Path | None = None,
        geometry_refs: frozenset[str] | None = None,
        target_overlap=None,
    ):
        registry = dict(handlers or {})
        if any(
            key not in ASYNC_OPERATIONS or not callable(value) for key, value in registry.items()
        ):
            raise ValueError("Only trusted callable domain handlers may be registered")
        self.handlers = MappingProxyType(registry)
        # Opaque callbacks cannot reuse cache across service instances. A real
        # provider supplies stable, verified code and input identity explicitly.
        self._unversioned_execution_identity = content_hash({"instance": uuid4().hex})
        self.repository = Repository(Path(workspace))
        if approved_asset_root is None:
            approved_asset_root = self.repository.workspace / "assets"
            approved_asset_root.mkdir(exist_ok=True)
        self.assets = AssetRegistry(self.repository, Path(approved_asset_root))
        self.scenarios = ScenarioService(
            self.repository,
            self.assets,
            capabilities
            if capabilities is not None
            else Capabilities(evaluator_versions=[], solar_versions=[], search_versions=[]),
            geometry_refs=geometry_refs,
            target_overlap=target_overlap,
        )
        self.jobs = JobStore(self.repository.db_path)
        self.lease = WorkspaceLease(self.repository.workspace)
        self.worker = None

    def run_one(self, stop_event: threading.Event | None = None):
        """Manual deterministic execution; no restart recovery or fabricated output."""
        with self.lease.held():
            return self.jobs.run_one(self.handlers, stop_event or threading.Event())

    def recover_startup(self):
        """Explicit manual recovery after acquiring exclusive workspace ownership."""
        with self.lease.held():
            return self.jobs.recover_exclusive_startup(exclusive=True)

    def create_accepted(self, input):
        return self.scenarios.create_accepted(input, on_accept=self.jobs.activate)

    def replace_accepted(self, scenario_id, input, revision):
        ref = ScenarioRef(scenario_id=scenario_id, revision=revision, scope="accepted")
        return self.scenarios.replace_accepted(
            ref, input, if_match=revision, on_accept=self.jobs.activate
        )

    def accept_scenario(self, ref: ScenarioRef, revision: int):
        """Human-only callable; deliberately absent from the agent dispatcher."""
        return self.scenarios.accept_scenario(ref, if_match=revision, on_accept=self.jobs.activate)

    def resolve_for_execution(self, ref: ScenarioRef, *, operation: str):
        """Bind authoritative dependencies and trusted execution inputs to admission."""
        dependencies, hashes = self.scenarios.resolve_for_job(ref, operation=operation)
        handler = self.handlers.get(operation)
        if handler is None:
            raise DomainError("TOOL_UNAVAILABLE", "No trusted provider is configured", True)
        describe = getattr(handler, "execution_hashes", None)
        if describe is None:
            extra = {"unversioned-provider-instance": self._unversioned_execution_identity}
        else:
            if not callable(describe):
                raise DomainError("TOOL_UNAVAILABLE", "Execution identity is unavailable", True)
            extra = describe(dependencies, operation=operation)
        if (
            not isinstance(extra, Mapping)
            or not extra
            or any(
                type(key) is not str
                or not key.strip()
                or type(value) is not str
                or re.fullmatch(r"[0-9a-f]{64}", value) is None
                for key, value in extra.items()
            )
        ):
            raise DomainError("TOOL_UNAVAILABLE", "Execution identity is unverified", True)
        return dependencies, {
            **hashes,
            **{"execution:" + key: value for key, value in extra.items()},
        }

    def submit(self, request: JobRequest):
        operation = request.root
        scenario = self.scenarios.get_scenario(operation.scenario_ref)
        site = self.scenarios.get_site(
            scenario.input.site_id, scenario.input.scene_revision, scenario.input.semantic_revision
        )
        # Rights failures are explicit even when no provider has been installed.
        for right in site.rights:
            if right.local_use_status == "restricted":
                raise DomainError("RIGHTS_RESTRICTED", "Local source use is restricted")
            if right.local_use_status != "permitted" or not right.evidence:
                raise DomainError("RIGHTS_UNKNOWN", "Local source permission is not evidenced")
        deps, hashes = self.resolve_for_execution(
            operation.scenario_ref, operation=operation.operation
        )
        # Only the exact proposed layout has currently been validated by the typed
        # service. Resolve other refs first, then refuse a scientific scope expansion.
        if operation.operation in {"evaluate_layout", "compare_locations"}:
            ref = operation.arguments.layout_ref
            layout = self.scenarios.get_layout(ref.layout_id, ref.revision)
            if ref != scenario.input.proposed_layout_ref:
                raise DomainError(
                    "UNSUPPORTED_OPERATION", "Layout requires scenario-bound validation"
                )
            if (
                operation.operation == "compare_locations"
                and operation.arguments.placement_id
                not in {p.placement_id for p in layout.placements}
            ):
                raise DomainError("INVALID_INPUT", "Placement reference is unresolved")
        if operation.operation == "compare_scenarios":
            # Shared comparison/investigation validation is not yet supplied by
            # ScenarioService. Never submit an incompletely resolved comparison.
            raise DomainError(
                "UNSUPPORTED_OPERATION", "Scenario comparison admission is unavailable"
            )
        if operation.operation not in self.handlers:
            raise DomainError(
                "TOOL_UNAVAILABLE", "No trusted provider is configured for this operation", True
            )
        resolved = Scenario.model_validate(deps["scenario"])
        # Share the repository write transaction so acceptance cannot interleave
        # selection admission. Dependency objects themselves are immutable.
        with self.repository.transaction() as connection:
            return self.jobs.submit(
                request,
                resolved,
                content_hashes=hashes,
                deadline_utc=resolved.input.search.deadline_utc,
                connection=connection,
            )

    def selections(self, ref: ScenarioRef):
        self.scenarios.get_scenario(ref)
        return {
            slot: {
                "selection": self.jobs.selection(ref.scenario_id, ref.revision, ref.scope, slot),
                "current_job": self.jobs.current(ref.scenario_id, ref.revision, ref.scope, slot),
            }
            for slot in ("evaluation", "search", "comparison")
        }


class AgentDispatcher:
    """A host-bound investigation surface, deliberately without human acceptance.

    The host, never a tool argument, selects the accepted task. Every invocation
    rechecks its exact head and active selection. A proposed relaxation may be
    saved for review; that does not authorise computing it.
    """

    def __init__(self, service: ApplicationService, *, accepted_ref: ScenarioRef | None = None):
        self.__service = service
        self.__accepted_ref = (
            ScenarioRef.model_validate(accepted_ref) if accepted_ref is not None else None
        )
        if self.__accepted_ref is not None and self.__accepted_ref.scope != "accepted":
            raise DomainError("REVISION_CONFLICT", "An accepted task is required")

    def _task(self) -> Scenario:
        ref = self.__accepted_ref
        if ref is None:
            raise DomainError("REVISION_CONFLICT", "The host must select an accepted task")
        if (
            self.__service.scenarios.current_accepted_ref(ref.scenario_id) != ref
            or self.__service.jobs.active_ref() != ref
        ):
            raise DomainError("REVISION_CONFLICT", "The accepted task is no longer current")
        return self.__service.scenarios.get_scenario(ref)

    def _scope(self, ref: ScenarioRef) -> Scenario:
        from tree_planner.agents.policy import validate_analysis

        accepted = self._task()
        scenario = self.__service.scenarios.get_scenario(ref)
        if ref != self.__accepted_ref and (
            scenario.scope != "hypothetical" or scenario.base_scenario_ref != self.__accepted_ref
        ):
            raise DomainError("REVISION_CONFLICT", "Scenario is outside the accepted task")
        try:
            validate_analysis(accepted, scenario.input)
        except ValueError as exc:
            raise DomainError(
                "REVISION_CONFLICT", "Analysis requires a new human-accepted task"
            ) from exc
        return scenario

    def dispatch(self, envelope):
        from tree_planner.agents.policy import validate_preparation
        from tree_planner.contracts import SiteInspection

        envelope = OperationEnvelope.model_validate(envelope)
        operation = envelope.root
        if operation.operation == "prepare_scenario":
            base = operation.arguments.base_scenario_ref
            if base is not None:
                accepted = self._task()
                if base != self.__accepted_ref:
                    raise DomainError("REVISION_CONFLICT", "Proposal is outside the accepted task")
                try:
                    validate_preparation(accepted, operation.arguments.proposed_edits)
                except ValueError as exc:
                    raise DomainError(
                        "REVISION_CONFLICT", "Proposal changes accepted evidence authority"
                    ) from exc
            elif self.__accepted_ref is not None:
                raise DomainError(
                    "REVISION_CONFLICT", "A scoped proposal requires its accepted base"
                )
            return self.__service.scenarios.agent().prepare_scenario(
                operation.arguments.proposed_edits, base_ref=base
            )
        if operation.operation == "inspect_site":
            accepted = self._task()
            inp, args = accepted.input, operation.arguments
            if (args.site_id, args.scene_revision) != (inp.site_id, inp.scene_revision):
                raise DomainError("REVISION_CONFLICT", "Site is outside the accepted task")
            site = self.__service.scenarios.get_site(
                inp.site_id, inp.scene_revision, inp.semantic_revision
            )
            return SiteInspection(
                schema_version="0.1.0",
                site_id=site.site_id,
                scene_revision=site.scene_revision,
                semantic_revision=site.semantic_revision,
                site_kind=site.site_kind,
                geometry_fingerprint=site.geometry_fingerprint,
                readiness=self.__service.scenarios.readiness(
                    site.site_id, site.scene_revision, site.semantic_revision
                ),
                registered_operations=sorted(self.__service.handlers),
                source_ids=[right.source_id for right in site.rights],
                limitations=[
                    "Metadata inspection is not a numerical result or scientific acceptance"
                ],
            )
        if operation.operation in ASYNC_OPERATIONS:
            self._scope(operation.scenario_ref)
            if operation.operation == "compare_scenarios":
                self._scope(operation.arguments.base_scenario_ref)
                self._scope(operation.arguments.alternative_scenario_ref)
            return self.__service.submit(
                JobRequest.model_validate(operation.model_dump(mode="json"))
            )
        raise DomainError(
            "UNSUPPORTED_OPERATION", "No exact domain provider is available for this operation"
        )

    def poll(self, job_id: str):
        """Return an actual stored job only inside the host-selected task."""
        job = self.__service.jobs.get_job(job_id)
        self._scope(
            ScenarioRef(
                scenario_id=job.scenario_id, revision=job.scenario_revision, scope=job.scope
            )
        )
        return job

    def result(self, run_id: str):
        """Read an immutable run; the loop independently checks delivery eligibility."""
        result = self.__service.jobs.read_run(run_id)
        self._scope(result.input_snapshot_ref)
        return result

    def selection(self, ref: ScenarioRef, slot: str):
        """Read authoritative selection metadata, never reconstruct it from arrival order."""
        self._scope(ref)
        selection = self.__service.jobs.selection(ref.scenario_id, ref.revision, ref.scope, slot)
        if selection is None:
            raise DomainError("UNKNOWN_REVISION", "No operation is selected for this slot")
        return selection
