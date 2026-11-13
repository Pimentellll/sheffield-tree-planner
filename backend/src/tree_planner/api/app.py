"""Local-only HTTP application composed from typed persistence and JobStore."""

import asyncio
from collections.abc import Mapping
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import re
from typing import Literal

from fastapi import FastAPI, Header, Query, Response
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from tree_planner.contracts import (
    Capabilities,
    ContractError,
    ContractModel,
    Job,
    JobRequest,
    Layout,
    OperationEnvelope,
    SCHEMA_VERSION,
    Result,
    Scenario,
    ScenarioInput,
    ScenarioRef,
    Selection,
    SiteBundle,
    SiteInspection,
    TreeProfile,
    compute_readiness,
)
from tree_planner.contracts.base import Array, ID
from tree_planner.jobs import JobStoreError, JobWorker
from tree_planner.site.repository import DomainError
from .security import LocalOnlyMiddleware
from .service import AgentDispatcher, ApplicationService


def application_version():
    try:
        return version("sheffield-tree-planner-readiness")
    except PackageNotFoundError:
        # Source-checkout execution, without inventing a second version constant.
        import tomllib

        manifest = Path(__file__).resolve().parents[4] / "pyproject.toml"
        if manifest.is_file():
            return tomllib.loads(manifest.read_text(encoding="utf-8"))["project"]["version"]
        return "0+uninstalled"


class SourceRights(ContractModel):
    local_use_status: Literal["permitted", "restricted", "unknown"]
    team_share_status: Literal["permitted", "restricted", "unknown"]
    public_display_status: Literal["permitted", "restricted", "unknown"]
    export_status: Literal["permitted", "restricted", "unknown"]


class SourceRegistration(ContractModel):
    source_reference: ID
    licence_reference: ID
    evidence: Array[ID]
    rights: SourceRights


class AssetRegistration(ContractModel):
    relative_path: ID
    source_id: ID
    capture_date: ID


class SlotState(ContractModel):
    selection: Selection | None
    current_job: Job | None


class ScenarioSelections(ContractModel):
    evaluation: SlotState
    search: SlotState
    comparison: SlotState


_MESSAGES = {
    "INVALID_INPUT": "Request validation failed",
    "UNKNOWN_REVISION": "Exact reference was not found",
    "REVISION_CONFLICT": "Revision or request identity conflicts with stored state",
    "RIGHTS_RESTRICTED": "Local source use is restricted",
    "RIGHTS_UNKNOWN": "Local source permission is not evidenced",
    "SITE_NOT_READY": "Site is not ready for analysis",
    "UNSUPPORTED_OPERATION": "Operation or runtime configuration is unsupported",
    "TOOL_UNAVAILABLE": "The local operation is unavailable",
    "DEADLINE_EXCEEDED": "The job deadline expired",
    "RESULT_VALIDATION_FAILED": "Stored output failed validation",
}


def error_response(code, status, *, fields=(), retryable=False):
    error = ContractError(
        code=code,
        message=_MESSAGES.get(code, "Local operation failed"),
        retryable=retryable,
        field_errors=fields,
        details={},
    )
    return JSONResponse(error.model_dump(mode="json"), status_code=status)


class _SafeFailures:
    """Contain callback/storage failures inside the security response boundary.

    Starlette's outer ServerErrorMiddleware re-raises exceptions after sending a
    response. Containing them here also prevents raw callback details in its log.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = False

        async def track(message):
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, receive, track)
        except Exception:
            if started:
                raise
            await error_response("TOOL_UNAVAILABLE", 503, retryable=True)(scope, receive, send)


def _revision(value: str):
    if not re.fullmatch(r"[1-9][0-9]{0,18}", value) or int(value) > 9223372036854775807:
        raise DomainError("INVALID_INPUT", "A positive exact revision is required")
    return int(value)


def _match(value: str | None):
    if value is None or not re.fullmatch(r'"[1-9][0-9]{0,18}"', value):
        raise DomainError("REVISION_CONFLICT", "Quoted If-Match revision required")
    return _revision(value[1:-1])


def create_app(
    workspace: Path,
    *,
    handlers: Mapping | None = None,
    capabilities: Capabilities | None = None,
    approved_asset_root: Path | None = None,
    geometry_refs: frozenset[str] | None = None,
    target_overlap=None,
    start_worker: bool = True,
    allowed_ui_origins=(),
) -> FastAPI:
    """Configure trusted Python providers only; no serialized callback discovery.

    Loopback origin checks protect a local workflow, not other OS users/processes.
    No handler means manual state management with typed unavailable job errors.
    """
    service = ApplicationService(
        workspace,
        handlers=handlers,
        capabilities=capabilities,
        approved_asset_root=approved_asset_root,
        geometry_refs=geometry_refs,
        target_overlap=target_overlap,
    )
    agent = AgentDispatcher(service)

    @asynccontextmanager
    async def lifespan(app):
        if start_worker and service.handlers:
            service.lease.acquire()
            try:
                service.worker = JobWorker(service.jobs, service.handlers)
                service.worker.start(exclusive=True)
                app.state.worker = service.worker
                app.state.worker_mode = "background"
                yield
            finally:
                # Keep the OS lock until a cooperative handler actually exits.
                if service.worker is not None:
                    await asyncio.to_thread(service.worker.stop)
                service.worker = None
                app.state.worker = None
                app.state.worker_mode = "manual"
                service.lease.release()
        else:
            yield

    app = FastAPI(
        title="CANOPY local API",
        version=application_version(),
        lifespan=lifespan,
        redirect_slashes=False,
        docs_url=None,
        redoc_url=None,
        openapi_url="/api/v1/openapi.json",
        responses={
            status: {"model": ContractError} for status in (400, 403, 404, 405, 409, 413, 422, 503)
        },
    )
    app.add_middleware(_SafeFailures)
    app.add_middleware(LocalOnlyMiddleware, allowed_origins=tuple(allowed_ui_origins))
    app.state.service = service
    app.state.repository = service.repository
    app.state.assets = service.assets
    app.state.scenarios = service.scenarios
    app.state.jobs = service.jobs
    app.state.agent = agent
    app.state.run_one = service.run_one
    app.state.worker = None
    app.state.worker_mode = "manual"

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        # Never expose Pydantic's input, ctx, validator exception, or raw messages.
        # Unknown/dynamic object keys also contain untrusted data.
        fields = []
        known = {
            "body",
            "query",
            "path",
            "header",
            "revision",
            "scene_revision",
            "semantic_revision",
            "library_revision",
            "scope",
            "profile_id",
            "site_id",
            "scenario_id",
            "run_id",
            "job_id",
        }
        from tree_planner import contracts

        for obj in vars(contracts).values():
            if isinstance(obj, type) and hasattr(obj, "model_fields"):
                known.update(obj.model_fields)
        for item in exc.errors()[:64]:
            loc = ".".join(str(p) if isinstance(p, int) or p in known else "*" for p in item["loc"])
            fields.append(
                {
                    "field": loc or "body",
                    "message": "Required field"
                    if item["type"] == "missing"
                    else "Invalid field value",
                }
            )
        return error_response("INVALID_INPUT", 422, fields=fields)

    @app.exception_handler(DomainError)
    async def domain_error(request, exc):
        code = exc.code if exc.code in _MESSAGES else "INVALID_INPUT"
        status = {
            "UNKNOWN_REVISION": 404,
            "REVISION_CONFLICT": 409,
            "TOOL_UNAVAILABLE": 503,
            "RESULT_VALIDATION_FAILED": 503,
        }.get(code, 422)
        return error_response(code, status, retryable=code == "TOOL_UNAVAILABLE")

    @app.exception_handler(JobStoreError)
    async def job_error(request, exc):
        if str(exc) == "idempotency conflict":
            return error_response("REVISION_CONFLICT", 409)
        return error_response("TOOL_UNAVAILABLE", 503, retryable=True)

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return error_response(
            "UNKNOWN_REVISION" if exc.status_code == 404 else "INVALID_INPUT", exc.status_code
        )

    @app.exception_handler(Exception)
    async def infrastructure_error(request, exc):
        return error_response("TOOL_UNAVAILABLE", 503, retryable=True)

    # ValidationError from stored/callback output is infrastructure failure, never
    # request errors or raw Pydantic diagnostics. Explicit registration avoids echo.
    app.add_exception_handler(ValidationError, infrastructure_error)
    app.add_exception_handler(ResponseValidationError, infrastructure_error)

    @app.get("/api/v1/health")
    def health():
        return {
            "status": "ok",
            "version": app.version,
            "schema_version": SCHEMA_VERSION,
            "worker_mode": app.state.worker_mode,
            "available_operations": sorted(service.handlers),
            "security_scope": "local origin protection; not multi-user OS authentication",
        }

    @app.get("/api/v1/version")
    def get_version():
        return {"version": app.version, "schema_version": SCHEMA_VERSION}

    @app.post("/api/v1/sources", status_code=201)
    def source(body: SourceRegistration):
        return service.assets.register_source(**body.model_dump(mode="json"))

    @app.post("/api/v1/assets", status_code=201)
    def asset(body: AssetRegistration):
        return service.assets.register_from_source(**body.model_dump(mode="json"))

    @app.post("/api/v1/sites/import", status_code=201, response_model=SiteBundle)
    def import_site(body: SiteBundle):
        site = service.scenarios.register_site(body)
        return site.model_copy(update={"readiness": compute_readiness(site)})

    @app.get("/api/v1/sites/{site_id}", response_model=SiteBundle)
    def get_site(site_id: str, scene_revision: str = Query(), semantic_revision: str = Query()):
        site = service.scenarios.get_site(
            site_id, _revision(scene_revision), _revision(semantic_revision)
        )
        return site.model_copy(update={"readiness": compute_readiness(site)})

    @app.post("/api/v1/profiles", status_code=201, response_model=TreeProfile)
    def profile(body: TreeProfile):
        return service.scenarios.register_profile(body)

    @app.get("/api/v1/profiles/{profile_id}", response_model=TreeProfile)
    def get_profile(profile_id: str, library_revision: str = Query()):
        return service.scenarios.get_profile(profile_id, _revision(library_revision))

    @app.post("/api/v1/layouts", status_code=201, response_model=Layout)
    def layout(body: Layout):
        return service.scenarios.register_layout(body)

    @app.get("/api/v1/layouts/{layout_id}", response_model=Layout)
    def get_layout(layout_id: str, revision: str = Query()):
        return service.scenarios.get_layout(layout_id, _revision(revision))

    @app.post("/api/v1/scenarios", status_code=201, response_model=Scenario)
    def create_scenario(body: ScenarioInput, response: Response):
        result = service.create_accepted(body)
        response.headers["ETag"] = f'"{result.revision}"'
        return result

    @app.put("/api/v1/scenarios/{scenario_id}", response_model=Scenario)
    def replace_scenario(
        scenario_id: str,
        body: ScenarioInput,
        response: Response,
        if_match: str | None = Header(default=None),
    ):
        result = service.replace_accepted(scenario_id, body, _match(if_match))
        response.headers["ETag"] = f'"{result.revision}"'
        return result

    @app.get("/api/v1/scenarios/{scenario_id}", response_model=Scenario)
    def get_scenario(
        scenario_id: str,
        response: Response,
        revision: str = Query(),
        scope: Literal["accepted", "hypothetical"] = "accepted",
    ):
        result = service.scenarios.get_scenario(
            ScenarioRef(scenario_id=scenario_id, revision=_revision(revision), scope=scope)
        )
        response.headers["ETag"] = f'"{result.revision}"'
        return result

    @app.get("/api/v1/scenarios/{scenario_id}/selections", response_model=ScenarioSelections)
    def selections(
        scenario_id: str,
        revision: str = Query(),
        scope: Literal["accepted", "hypothetical"] = "accepted",
    ):
        return service.selections(
            ScenarioRef(scenario_id=scenario_id, revision=_revision(revision), scope=scope)
        )

    @app.post("/api/v1/scenarios/accept", response_model=Scenario)
    def accept_scenario(
        body: ScenarioRef, response: Response, if_match: str | None = Header(default=None)
    ):
        result = service.accept_scenario(body, _match(if_match))
        response.headers["ETag"] = f'"{result.revision}"'
        return result

    @app.post("/api/v1/operations", response_model=Scenario | Job | SiteInspection)
    def operation(
        body: OperationEnvelope,
        response: Response,
        task_id: str | None = Header(default=None, alias="X-Canopy-Scenario-Id"),
        task_revision: str | None = Header(default=None, alias="X-Canopy-Scenario-Revision"),
    ):
        # A transport can pin its host-selected context across multiple calls.
        # Neither a tool argument nor this header can create human acceptance.
        if (task_id is None) != (task_revision is None):
            raise DomainError("INVALID_INPUT", "Both task context headers are required")
        accepted_ref = service.jobs.active_ref()
        if task_id is not None:
            if not task_id.strip():
                raise DomainError("INVALID_INPUT", "An exact task identifier is required")
            accepted_ref = ScenarioRef(
                scenario_id=task_id, revision=_revision(task_revision), scope="accepted"
            )
        dispatcher = AgentDispatcher(service, accepted_ref=accepted_ref)
        result = dispatcher.dispatch(body)
        if body.root.operation in service.handlers:
            response.status_code = 202
        return result

    @app.post("/api/v1/jobs", status_code=202, response_model=Job)
    def submit_job(body: JobRequest):
        return service.submit(body)

    @app.get("/api/v1/jobs/{job_id}", response_model=Job)
    def get_job(job_id: str):
        result = service.jobs.get_job(job_id)
        if result is None:
            raise DomainError("UNKNOWN_REVISION", "Job not found")
        return result

    @app.post("/api/v1/jobs/{job_id}/cancel", response_model=Job)
    def cancel(job_id: str):
        get_job(job_id)
        service.jobs.cancel(job_id)
        return get_job(job_id)

    @app.get("/api/v1/results/{run_id}", response_model=Result)
    def result(run_id: str):
        result = service.jobs.read_run(run_id)
        if result is None:
            raise DomainError("UNKNOWN_REVISION", "Run not found")
        return result

    return app
