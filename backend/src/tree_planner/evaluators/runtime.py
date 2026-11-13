"""Trusted startup for a deliberately limited pure-Python synthetic reference.

No SiteBundle mesh importer or solar-position calculation is provided. The
registered asset is an explicit synthetic receiver/sun/obstacle declaration.
"""

from __future__ import annotations

import builtins
from dataclasses import dataclass
from datetime import datetime
import hashlib
from math import isfinite, sqrt
from pathlib import Path
import sys
from types import ModuleType
from uuid import uuid4

from tree_planner.canonical import canonical_bytes
from tree_planner.contracts import Capabilities, JobRequest, ScenarioRef
from . import ReferenceInputs, ReferenceJobHandler, ReferenceProvider, ReferenceUnsupported

SOURCE_HASHES = (
    ("shade_reference.py", "128ef3f607933785bb895a651f225a54a3d4af605a607ff28cfc3918f89d65ce"),
    ("ray.py", "7eb34bdaa967a0b01bbda977b2c2cd8385b19196609574d9ddea5aa4867b7198"),
)
EVALUATOR = "synthetic-one-tree-reference"
SOLAR = "analytic-chosen-synthetic-direction"
VERSION = "1"


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _module_state(module):
    """Detect replacement or mutation of loaded producer symbols before use."""
    state = []
    for name, value in sorted(vars(module).items()):
        if name == "__builtins__":
            continue
        methods = ()
        if isinstance(value, type) and value.__module__ == module.__name__:
            methods = tuple(
                (
                    key,
                    id(member),
                    getattr(member, "__code__", None),
                    repr(getattr(member, "__defaults__", None)),
                    repr(getattr(member, "__kwdefaults__", None)),
                )
                for key, member in sorted(vars(value).items())
            )
        state.append(
            (
                name,
                id(value),
                getattr(value, "__code__", None),
                repr(getattr(value, "__defaults__", None)),
                repr(getattr(value, "__kwdefaults__", None)),
                methods,
            )
        )
    return state


@dataclass(frozen=True)
class TrustedNumerics:
    root: Path
    shade: ModuleType
    ray: ModuleType
    _shade_state: tuple
    _ray_state: tuple

    def verify(self):
        for name, expected in SOURCE_HASHES:
            try:
                actual = _digest(self.root / "backend/src/tree_planner/physics" / name)
            except OSError as exc:
                raise ReferenceUnsupported("numerical source unavailable") from exc
            if actual != expected:
                raise ReferenceUnsupported("numerical source hash changed or unverified")
        if (
            tuple(_module_state(self.shade)) != self._shade_state
            or tuple(_module_state(self.ray)) != self._ray_state
        ):
            raise ReferenceUnsupported("loaded numerical implementation changed")
        return dict(SOURCE_HASHES)


def load_numerics(source: Path) -> TrustedNumerics:
    """Compile only approved actual bytes; no copied source, pyc or package init.

    The producer's exact absolute ray import is routed to its verified ray module.
    All other imports retain normal Python semantics. This is trusted startup,
    never a request-controlled path or a sandbox for arbitrary code.
    """
    root = Path(source).resolve(strict=True)
    physics = root / "backend/src/tree_planner/physics"
    payloads = {}
    for name, expected in SOURCE_HASHES:
        try:
            data = (physics / name).read_bytes()
        except OSError as exc:
            raise ReferenceUnsupported("numerical source unavailable") from exc
        if hashlib.sha256(data).hexdigest() != expected:
            raise ReferenceUnsupported("numerical source hash changed or unverified")
        payloads[name] = data
    # Unique names avoid collision with any other numerical checkout in-process.
    prefix = "_canopy_verified_reference_" + uuid4().hex
    modules = {}
    try:
        for name in ("ray", "shade_reference"):
            module = ModuleType(prefix + "_" + name)
            module.__file__ = str(physics / (name + ".py"))
            sys.modules[module.__name__] = module  # dataclasses resolves __module__
            modules[name] = module
            custom_builtins = dict(vars(builtins))

            def audited_import(name, globals=None, locals=None, fromlist=(), level=0):
                if name == "tree_planner.physics.ray" and level == 0:
                    return modules["ray"]
                return builtins.__import__(name, globals, locals, fromlist, level)

            custom_builtins["__import__"] = audited_import
            module.__dict__["__builtins__"] = custom_builtins
            exec(compile(payloads[name + ".py"], module.__file__, "exec"), module.__dict__)
        trusted = TrustedNumerics(
            root,
            modules["shade_reference"],
            modules["ray"],
            tuple(_module_state(modules["shade_reference"])),
            tuple(_module_state(modules["ray"])),
        )
        trusted.verify()
        return trusted
    except BaseException:
        for module in modules.values():
            sys.modules.pop(module.__name__, None)
        raise


@dataclass(frozen=True)
class SyntheticScene:
    receiver_point: tuple[float, float, float] = (0.0, 0.0, 0.0)
    receiver_normal: tuple[float, float, float] = (0.0, 0.0, 1.0)
    receiver_area_m2: float = 2.0
    sun_direction: tuple[float, float, float] = (0.0, -sqrt(0.5), sqrt(0.5))
    above_horizon: bool = True
    midpoint_utc: str = "2026-07-01T12:00:00Z"
    duration_h: float = 1.0
    obstacle_ellipsoids: tuple = ()

    def __post_init__(self):
        def vec(value, *, unit=False, positive=False):
            if (
                type(value) is not tuple
                or len(value) != 3
                or not all(type(x) in (int, float) and isfinite(x) for x in value)
                or (unit and abs(sum(x * x for x in value) - 1) > 1e-9)
                or (positive and any(x <= 0 for x in value))
            ):
                raise ValueError("immutable finite synthetic vector required")

        vec(self.receiver_point)
        vec(self.receiver_normal, unit=True)
        vec(self.sun_direction, unit=True)
        if type(self.above_horizon) is not bool or self.above_horizon != (
            self.sun_direction[2] > 0
        ):
            raise ValueError("synthetic horizon flag must match chosen direction")
        for value in (self.receiver_area_m2, self.duration_h):
            if type(value) not in (int, float) or not isfinite(value) or value <= 0:
                raise ValueError("positive finite area and duration required")
        from tree_planner.contracts.base import utc

        utc(self.midpoint_utc)
        if type(self.obstacle_ellipsoids) is not tuple:
            raise ValueError("immutable obstacle tuple required")
        for obstacle in self.obstacle_ellipsoids:
            if type(obstacle) is not tuple or len(obstacle) != 2:
                raise ValueError("immutable ellipsoid pair required")
            vec(obstacle[0])
            vec(obstacle[1], positive=True)

    def declaration(self):
        return dict(
            kind="explicit synthetic ENU reference inputs; no geometry importer",
            target_id="synthetic-target",
            receiver_point=list(self.receiver_point),
            receiver_normal=list(self.receiver_normal),
            receiver_area_m2=self.receiver_area_m2,
            solar_algorithm=SOLAR,
            solar_version=VERSION,
            sun_direction=list(self.sun_direction),
            above_horizon=self.above_horizon,
            midpoint_utc=self.midpoint_utc,
            duration_h=self.duration_h,
            obstacle_ellipsoids=[[list(c), list(r)] for c, r in self.obstacle_ellipsoids],
            evidence="Chosen analytic direction; timestamp labels a synthetic bin, not astronomy",
        )


@dataclass(frozen=True)
class ReferenceRuntime:
    app: object
    handler: ReferenceJobHandler
    numerical: TrustedNumerics
    scene: SyntheticScene
    scenario_ref: ScenarioRef

    def request(self, request_id, *, scenario=None):
        ref = scenario or self.scenario_ref
        value = self.app.state.scenarios.get_scenario(ref)
        return JobRequest.model_validate(
            dict(
                request_id=request_id,
                scenario_ref=ref.model_dump(mode="json"),
                operation="evaluate_layout",
                arguments={"layout_ref": value.input.proposed_layout_ref.model_dump(mode="json")},
            )
        )


def create_reference_runtime(
    workspace: Path,
    *,
    numerical_source: Path,
    scene: SyntheticScene = SyntheticScene(),
    start_worker: bool = True,
) -> ReferenceRuntime:
    """Create and seed an isolated local synthetic runtime through real services.

    Workspace must be new: startup never overwrites prior inputs or stored runs.
    The parent owns application admission composition; missing support fails closed.
    """
    from tree_planner.api import create_app
    from tree_planner.api.service import ApplicationService
    from .seed import seed_reference

    if not callable(getattr(ApplicationService, "resolve_for_execution", None)):
        raise ReferenceUnsupported("ApplicationService.resolve_for_execution is required")
    if not isinstance(scene, SyntheticScene):
        raise TypeError("immutable SyntheticScene required")
    numerical = load_numerics(numerical_source)
    workspace = Path(workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=False)
    assets_root = workspace / "inputs"
    assets_root.mkdir()
    declaration = canonical_bytes(scene.declaration())
    (assets_root / "synthetic-reference.json").write_bytes(declaration)
    # Hash actual provider/adapter/canonical source at startup and reject hot edits.
    paths = (
        Path(__file__),
        Path(__file__).with_name("__init__.py"),
        Path(__file__).with_name("seed.py"),
        Path(__file__).parents[1] / "canonical.py",
    )
    source_baseline = {str(path): _digest(path) for path in paths}
    holder = {}

    def verify():
        hashes = numerical.verify()
        for path in paths:
            try:
                actual = _digest(path)
            except OSError as exc:
                raise ReferenceUnsupported("provider implementation source unavailable") from exc
            if actual != source_baseline[str(path)]:
                raise ReferenceUnsupported(
                    "provider implementation source changed; restart required"
                )
            hashes["provider/" + path.name] = actual
        return hashes

    def resolve(ref, *, operation):
        return holder["app"].state.service.resolve_for_execution(ref, operation=operation)

    def inputs(deps, request):
        verify()
        if deps["site"] != holder["site"].model_dump(mode="json"):
            raise ReferenceUnsupported("synthetic site binding mismatch")
        asset = holder["site"].assets[0]
        if (
            holder["app"].state.assets.read(asset.ref.registry_id, "local_use_status")
            != declaration
        ):
            raise ReferenceUnsupported("synthetic numerical asset binding mismatch")
        scenario = deps["scenario"]
        inp = scenario["input"]
        ref = ScenarioRef.model_validate(
            {k: scenario[k] for k in ("scenario_id", "revision", "scope")}
        )
        if (
            request.scenario_ref != ref
            or request.arguments.layout_ref.model_dump(mode="json") != inp["proposed_layout_ref"]
            or len(inp["evaluation_cases"]) != 1
            or inp["numerics"] != holder["numerics"]
        ):
            raise ReferenceUnsupported("synthetic scenario or numerical version binding mismatch")
        case = inp["evaluation_cases"][0]
        if (
            case["target_ids"] != ["synthetic-target"]
            or case["time_bins"]
            != [dict(midpoint_utc=scene.midpoint_utc, duration_h=scene.duration_h)]
            or case["area_basis"] != "surface"
            or case["weather_ref"] is not None
            or case["target_weights"] != {"synthetic-target": 1.0}
        ):
            raise ReferenceUnsupported("synthetic sample or solar bin binding mismatch")
        layout = deps["layout"]
        if (
            len(layout["placements"]) != 1
            or {"layout_id": layout["layout_id"], "revision": layout["revision"]}
            != inp["proposed_layout_ref"]
        ):
            raise ReferenceUnsupported("synthetic layout binding mismatch")
        placement = layout["placements"][0]
        profile = deps["profiles"][placement["profile_id"]]
        state = profile["states"][case["profile_state"]]
        if (
            profile["library_revision"] != inp["profile_library_revision"]
            or state["horizon_years"] != case["horizon_years"]
            or state["attenuation"]["mode"] != "opaque"
        ):
            raise ReferenceUnsupported("synthetic profile binding mismatch")
        p = numerical.shade
        x, y, z = placement["position_enu_m"]
        return ReferenceInputs(
            ref,
            layout["layout_id"],
            layout["revision"],
            placement["placement_id"],
            case["case_id"],
            case["horizon_years"],
            "synthetic-target",
            (
                p.ReceiverSample(
                    scene.receiver_point,
                    scene.receiver_normal,
                    scene.receiver_area_m2,
                    "synthetic-target",
                ),
            ),
            (
                p.DraftSolarBin(
                    datetime.fromisoformat(scene.midpoint_utc.replace("Z", "+00:00")),
                    scene.duration_h,
                    scene.sun_direction,
                    scene.above_horizon,
                ),
            ),
            tuple(p.OpaqueEllipsoid(c, r) for c, r in scene.obstacle_ellipsoids),
            p.ProposedTree(
                p.OpaqueEllipsoid(
                    (x, y, z + state["crown_center_height_m"]), tuple(state["crown_radii_m"])
                ),
                p.OpaqueTrunk(x, y, z, state["trunk_radius_m"], state["trunk_height_m"]),
            ),
        )

    provider = ReferenceProvider(
        resolve,
        inputs,
        numerical.shade.evaluate_one_tree_synthetic,
        EVALUATOR,
        VERSION,
        SOLAR,
        VERSION,
        SOURCE_HASHES,
        verify,
    )
    handler = ReferenceJobHandler(provider)
    app = create_app(
        workspace / "store",
        approved_asset_root=assets_root,
        geometry_refs=frozenset({"synthetic-reference"}),
        capabilities=Capabilities(
            evaluator_versions=[EVALUATOR + "@" + VERSION],
            solar_versions=[SOLAR + "@" + VERSION],
            search_versions=[],
        ),
        handlers={"evaluate_layout": handler},
        start_worker=start_worker,
    )
    holder["app"] = app
    site, scenario = seed_reference(app.state.service, scene)
    holder["site"] = site
    holder["numerics"] = scenario.input.numerics.model_dump(mode="json")
    ref = ScenarioRef(
        scenario_id=scenario.scenario_id, revision=scenario.revision, scope=scenario.scope
    )
    # Startup proof through the exact same composition as admission and execution.
    app.state.service.resolve_for_execution(ref, operation="evaluate_layout")
    return ReferenceRuntime(app, handler, numerical, scene, ref)
