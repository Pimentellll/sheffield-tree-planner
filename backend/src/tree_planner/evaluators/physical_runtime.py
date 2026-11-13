"""Opt-in synthetic CPU runtime with registered scene assets and typed job fences.

This is local engineering evidence, not a real-site or scientific acceptance gate.
The product agent can only invoke the existing typed dispatcher operations.
"""

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
from importlib import import_module
import inspect
import json
from pathlib import Path
import sys
from time import perf_counter

from tree_planner.api.app import application_version, create_app
from tree_planner.canonical import canonical_bytes, content_hash
from tree_planner.contracts import Capabilities, JobRequest, Layout, Result, ScenarioRef
from tree_planner.jobs.search import LayoutVerdict, SearchHandler, SearchVerdict, _code_identity
from tree_planner.jobs.comparison import changed_fields

OPERATIONS = frozenset(
    {"evaluate_layout", "search_layouts", "compare_locations", "compare_scenarios"}
)


def _now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _loaded_state(module):
    records = []

    def function(name, obj):
        return (
            name,
            id(obj),
            content_hash(_code_identity(obj.__code__)),
            repr(
                (
                    obj.__defaults__,
                    obj.__kwdefaults__,
                    tuple(repr(c.cell_contents) for c in (obj.__closure__ or ())),
                )
            ),
        )

    for name, obj in sorted(vars(module).items()):
        if inspect.isfunction(obj):
            records.append(function(name, obj))
        elif inspect.isclass(obj) and obj.__module__ == module.__name__:
            for method, value in sorted(vars(obj).items()):
                if isinstance(value, (staticmethod, classmethod)):
                    value = value.__func__
                if inspect.isfunction(value):
                    records.append(function(name + "." + method, value))
        elif name.isupper() and type(obj) in (str, int, float, bool, tuple, frozenset):
            records.append(
                (
                    name,
                    id(obj),
                    content_hash(repr(sorted(obj)) if isinstance(obj, frozenset) else repr(obj)),
                    "constant",
                )
            )
    return tuple(records)


class PhysicalHandler:
    """Trusted configuration; requests cannot provide a path, callback or executable."""

    def __init__(self):
        # Windows native scientific-library initialisation must finish on the
        # startup thread, before the background worker advertises readiness.
        # Independent cold/warm main-server repros exposed a stuck NumPy DLL
        # import when the first solar call performed this in the worker thread.
        for dependency in ("numpy", "pandas", "pvlib"):
            import_module(dependency)
        from tree_planner.physics.evaluator import compute
        from tree_planner.search import check, prepare, search

        self.compute, self.prepare, self.check, self.search = compute, prepare, check, search
        self._callbacks = (compute, prepare, check, search)
        self.service = None
        __import__("tree_planner.jobs.comparison")
        # Import all transitive owned numerical modules before freezing their identity.
        modules = [
            m
            for name, m in sorted(sys.modules.items())
            if (
                name.startswith("tree_planner.physics")
                or name.startswith("tree_planner.search")
                or name.startswith("tree_planner.contracts")
                or name
                in {
                    __name__,
                    "tree_planner.evaluators.physical_seed",
                    "tree_planner.canonical",
                    "tree_planner.api.app",
                    "tree_planner.api.service",
                    "tree_planner.jobs",
                    "tree_planner.jobs.search",
                    "tree_planner.jobs.comparison",
                    "tree_planner.site.service",
                }
            )
            and getattr(m, "__file__", None)
        ]
        self._modules = tuple(modules)
        self._states = tuple(_loaded_state(m) for m in modules)
        self._files = {m.__name__: Path(m.__file__) for m in modules}
        self._source = {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in self._files.items()
        }
        self._versions = {
            name: version(name) for name in ("pvlib", "numpy", "pandas", "scipy", "pyproj")
        }

    def _manifest(self):
        if (self.compute, self.prepare, self.check, self.search) != self._callbacks:
            raise ValueError("Configured numerical callback changed")
        current = {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in self._files.items()
        }
        if (
            current != self._source
            or tuple(_loaded_state(m) for m in self._modules) != self._states
        ):
            raise ValueError("Numerical implementation changed since trusted startup")
        if any(version(name) != value for name, value in self._versions.items()):
            raise ValueError("Numerical dependency version changed")
        return {
            "source": current,
            "loaded_code": {
                m.__name__: {name: digest for name, _, digest, _ in state}
                for m, state in zip(self._modules, self._states)
            },
            "dependencies": self._versions,
            "runtime": application_version(),
        }

    def _dependencies(self, deps):
        if deps["site"]["site_kind"] != "synthetic_test":
            raise ValueError("This runtime has no accepted real-site evidence")
        assets = [a for a in deps["site"]["assets"] if a["kind"] == "canopy_physical_scene_v1"]
        if len(assets) != 1:
            raise ValueError("Exactly one registered physical scene required")
        asset = assets[0]
        registered = deps["assets"][asset["asset_id"]]
        data = self.service.assets._path(registered["relative_path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != asset["sha256"]:
            raise ValueError("Registered physical scene bytes changed")
        scene = json.loads(data)
        if scene.get("format_version") != "canopy-physical-scene/1":
            raise ValueError("Unsupported physical scene version")
        numerics = deps["scenario"]["input"]["numerics"]
        if (
            numerics["evaluator"],
            numerics["evaluator_version"],
            numerics["solar_algorithm"],
            numerics["solar_version"],
        ) != ("canopy-cpu-reference", "takeover-v1", "pvlib-spa-geometric", "0.15.2") or scene.get(
            "spatial_spacing_m"
        ) != numerics["spatial_spacing_m"]:
            raise ValueError("Unsupported physical configuration or sampling spacing")
        search = deps["scenario"]["input"]["search"]
        maximum_exact_integer = 2**53 - 1
        if (
            deps["scenario"]["input"]["constraints"]["budget_pence"] > maximum_exact_integer
            or sum(p["cost_pence"] for p in deps["profiles"].values())
            * max(1, len(deps["site"]["candidate_catalogue"]))
            > maximum_exact_integer
        ):
            raise ValueError("Cost/budget exceeds exact numeric evidence range")
        if search["algorithm"] != "overlap-greedy-local" or search["version"] != "takeover-v1":
            raise ValueError("Unsupported search configuration")
        if (search["comparison_policy"], search["reference_policy"]) != (
            "same-constraints-actual-spend-count",
            "deterministic-reference",
        ):
            raise ValueError("Unsupported comparison/reference policy")
        return {**deepcopy(deps), "scene": scene}

    def execution_hashes(self, deps, *, operation):
        if operation not in OPERATIONS:
            raise ValueError("Unsupported operation")
        enriched = self._dependencies(deps)
        if operation == "compare_scenarios":
            self._dependencies(deps["comparison_context"]["alternative"])
        # Bind complete resolved scene/settings and both source and loaded implementation.
        return {
            "physical-inputs": content_hash(enriched),
            "physical-implementation": content_hash(self._manifest()),
        }

    def comparison_dependencies(self, deps, arguments):
        from tree_planner.site.repository import DomainError

        args = arguments.model_dump(mode="json") if hasattr(arguments, "model_dump") else arguments
        ref = ScenarioRef(**{k: deps["scenario"][k] for k in ("scenario_id", "revision", "scope")})
        base_ref = ScenarioRef.model_validate(args["base_scenario_ref"])
        alternative_ref = ScenarioRef.model_validate(args["alternative_scenario_ref"])
        if base_ref != ref or base_ref.scope != "accepted" or alternative_ref == ref:
            raise DomainError(
                "INVALID_INPUT", "Comparison requires an accepted primary and distinct alternative"
            )
        base, base_hashes = self.service.scenarios.resolve_for_job(
            ref, operation="compare_scenarios"
        )
        alternative, alternative_hashes = self.service.scenarios.resolve_for_job(
            alternative_ref, operation="compare_scenarios"
        )
        if alternative_ref.scope == "hypothetical" and alternative["scenario"][
            "base_scenario_ref"
        ] != ref.model_dump(mode="json"):
            raise DomainError("REVISION_CONFLICT", "Alternative is outside the accepted base")
        if (
            base != deps
            or base["site"] != alternative["site"]
            or base["profiles"] != alternative["profiles"]
        ):
            raise DomainError(
                "UNSUPPORTED_OPERATION",
                "Comparison requires identical site, catalogue and profile snapshots",
            )
        expected = {
            content_hash(d["scenario"]["input"]["proposed_layout_ref"]) for d in (base, alternative)
        }
        if {content_hash(x) for x in args["layout_refs"]} != expected or len(
            args["layout_refs"]
        ) != len(expected):
            raise DomainError(
                "INVALID_INPUT", "Comparison requires exact scenario-bound layout references"
            )
        if base["layout"] is None or alternative["layout"] is None:
            raise DomainError("INVALID_INPUT", "Comparison requires resolved layouts")
        if (
            args["mode"] == "fixed_layout"
            and base["layout"]["placements"] != alternative["layout"]["placements"]
        ):
            raise DomainError("INVALID_INPUT", "Fixed-layout comparison cannot change placements")
        context = dict(
            format_version="canopy-comparison-context/1",
            arguments=args,
            base=base,
            base_hashes=base_hashes,
            alternative=alternative,
            alternative_hashes=alternative_hashes,
        )
        return {**deps, "comparison_context": context}, context

    def __call__(self, job, context, run_id, local_stop, external_stop):
        request = JobRequest.model_validate(context["request"]).root
        ref = ScenarioRef(
            scenario_id=job.scenario_id, revision=job.scenario_revision, scope=job.scope
        )
        identity = context["identity"]

        def stop():
            if local_stop.is_set() or external_stop.is_set():
                raise ValueError("Execution cancelled")
            if datetime.now(timezone.utc) >= datetime.fromisoformat(
                context["deadline_utc"].replace("Z", "+00:00")
            ):
                raise ValueError("Deadline exceeded")

        def resolve():
            stop()
            deps, hashes = self.service.resolve_for_execution(
                ref,
                operation=job.operation,
                arguments=request.arguments if job.operation == "compare_scenarios" else None,
            )
            if (
                hashes != identity["content_hashes"]
                or deps["scenario"] != identity["scenario"]
                or content_hash(identity) != job.input_fingerprint
                or request.request_id != job.request_id
                or request.scenario_ref != ref
                or request.operation != job.operation
                or identity["operation"] != job.operation
                or identity["arguments"] != request.arguments.model_dump(mode="json")
            ):
                raise ValueError("Admitted execution identity changed")
            return self._dependencies(deps)

        deps = resolve()
        started, tick = _now(), perf_counter()
        problem = self.prepare(deps)

        def evaluate(placements):
            stop()
            return self.compute(
                deps, placements, stop=stop, diagnostic=job.operation == "compare_locations"
            )

        entries = []
        comparison = None
        outcome = "comparison_completed"
        if job.operation == "evaluate_layout":
            layout = Layout.model_validate(deps["layout"])
            entries.append(
                (
                    layout,
                    "alternative",
                    self.check(
                        problem,
                        layout.model_dump(mode="json")["placements"],
                        evaluate,
                        diagnostic=True,
                    ),
                    False,
                )
            )
        elif job.operation == "search_layouts":
            from tree_planner.physics import build_masks, evaluate_masks

            candidates = deps["site"]["candidate_catalogue"]
            masks = build_masks(deps, candidates, stop=stop)

            def masked_evaluate(placements):
                stop()
                if any(p["candidate_id"] is None for p in placements):
                    return self.compute(deps, placements, stop=stop)
                return evaluate_masks(
                    deps, candidates, masks, [p["candidate_id"] for p in placements], stop=stop
                )

            found = self.search(problem, masked_evaluate, stop=stop)
            outcome = found.outcome
            for label, choice in (("reference", found.reference), ("alternative", found.best)):
                if choice is None:
                    continue
                layout = Layout.model_validate(
                    dict(
                        schema_version="0.1.0",
                        layout_id=run_id + "-" + label,
                        revision=1,
                        kind="reference" if label == "reference" else "proposed",
                        placements=list(choice.placements),
                    )
                )
                verdict = self.check(problem, list(choice.placements), evaluate)
                selected = label == "alternative" and outcome in {
                    "feasible_candidate",
                    "feasible_zero_planting",
                }
                entries.append((layout, label, verdict, selected))
            if not entries:
                # Search diagnostics still report the admitted fixed layout if pins force failure.
                layout = Layout.model_validate(deps["layout"])
                entries.append(
                    (
                        layout,
                        "alternative",
                        self.check(problem, layout.model_dump(mode="json")["placements"], evaluate),
                        False,
                    )
                )
        elif job.operation == "compare_locations":
            from tree_planner.search import relocate

            layout = Layout.model_validate(deps["layout"])
            placements = layout.model_dump(mode="json")["placements"]
            alternative = relocate(
                problem,
                placements,
                request.arguments.placement_id,
                list(request.arguments.alternative_position_enu_m),
                evaluate,
            )
            changed = ["placements." + request.arguments.placement_id + ".position_enu_m"]
            data = layout.model_dump(mode="json")
            data.update(
                layout_id=run_id + "-relocation",
                kind="hypothetical",
                placements=list(alternative.placements),
            )
            entries = [
                (layout, "baseline", self.check(problem, placements, evaluate), False),
                (Layout.model_validate(data), "alternative", alternative.verdict, False),
            ]
            comparison = dict(mode="fixed_layout", changed_inputs=changed, deltas=[])
        elif job.operation == "compare_scenarios":
            comparison_context = deps["comparison_context"]
            entries = []
            for label, one in (
                ("baseline", comparison_context["base"]),
                ("alternative", comparison_context["alternative"]),
            ):
                one = self._dependencies(one)
                one_ref = ScenarioRef(
                    **{k: one["scenario"][k] for k in ("scenario_id", "revision", "scope")}
                )
                one_problem = self.prepare(one)

                def one_evaluate(placements):
                    stop()
                    return self.compute(one, placements, stop=stop)

                layout = Layout.model_validate(one["layout"])
                if request.arguments.mode == "redesign":
                    found = self.search(one_problem, one_evaluate, stop=stop)
                    if found.best is None:
                        raise ValueError("Comparison redesign produced no validated layout")
                    layout = Layout.model_validate(
                        dict(
                            schema_version="0.1.0",
                            layout_id=run_id + "-" + label,
                            revision=1,
                            kind="proposed",
                            placements=list(found.best.placements),
                        )
                    )
                verdict = self.check(
                    one_problem,
                    layout.model_dump(mode="json")["placements"],
                    one_evaluate,
                    diagnostic=True,
                )
                entries.append((layout, label, verdict, False, one, one_ref))
            changed = changed_fields(
                comparison_context["base"]["scenario"]["input"],
                comparison_context["alternative"]["scenario"]["input"],
            )
            comparison = dict(mode=request.arguments.mode, changed_inputs=changed, deltas=[])
        else:
            raise ValueError("Unsupported operation")
        if job.operation != "compare_scenarios":
            entries = [(*entry, deps, ref) for entry in entries]
        metrics, constraints, layouts = [], [], []
        scenario = deps["scenario"]["input"]
        for layout, role, verdict, selected, entry_deps, entry_ref in entries:
            cases = {c["case_id"]: c for c in entry_deps["scenario"]["input"]["evaluation_cases"]}
            layouts.append(
                dict(
                    layout=layout,
                    scenario_ref=entry_ref,
                    role=role,
                    cost_pence=verdict.cost_pence,
                    tree_count=len(layout.placements),
                    feasibility="feasible" if verdict.feasible else "infeasible",
                    reasons=list(verdict.reasons),
                    selected=selected,
                )
            )
            constraints.extend(
                dict(**dict(record), scenario_ref=entry_ref, layout_id=layout.layout_id)
                for record in verdict.records
            )
            output = verdict.evaluation
            for row in output["cases"]:
                case = cases[row["case_id"]]
                if (
                    row["case_id"]
                    == entry_deps["scenario"]["input"]["objective"]["primary_case_id"]
                    and row["quantity_kind"]
                    != entry_deps["scenario"]["input"]["objective"]["quantity_kind"]
                ):
                    raise ValueError("Primary objective physical quantity differs from calculation")
                for target_id, physical, weighted in [
                    (None, row["physical_m2_h"], row["weighted_m2_h"])
                ] + [
                    (t["target_id"], t["physical_m2_h"], t["weighted_m2_h"]) for t in row["targets"]
                ]:
                    values = [
                        ("additional_shade", physical, "m2_h", "unweighted", row["quantity_kind"]),
                        (
                            "weighted_shade_utility",
                            weighted,
                            "weighted_m2_h",
                            "declared-target-weights",
                            "weighted_utility",
                        ),
                    ]
                    if case["role"] == "winter_check":
                        values.append(
                            (
                                "winter_sun_loss",
                                physical,
                                "m2_h",
                                "unweighted",
                                row["quantity_kind"],
                            )
                        )
                    for metric_id, value, unit, weighting, quantity in values:
                        metrics.append(
                            dict(
                                metric_instance_id=f"{run_id}:{len(metrics)}",
                                metric_id=metric_id,
                                scenario_ref=entry_ref,
                                value=value,
                                unit=unit,
                                layout_id=layout.layout_id,
                                case_id=row["case_id"],
                                target_id=target_id,
                                horizon_years=case["horizon_years"],
                                weighting=weighting,
                                quantity_kind=quantity,
                                area_basis=case["area_basis"],
                            )
                        )
        if comparison:
            first, second = entries[0][0].layout_id, entries[1][0].layout_id
            first_ref, second_ref = entries[0][5], entries[1][5]
            for a in (
                m for m in metrics if m["layout_id"] == first and m["scenario_ref"] == first_ref
            ):
                b = next(
                    (
                        m
                        for m in metrics
                        if m["layout_id"] == second
                        and m["scenario_ref"] == second_ref
                        and all(
                            m[k] == a[k]
                            for k in (
                                "metric_id",
                                "case_id",
                                "target_id",
                                "unit",
                                "quantity_kind",
                                "horizon_years",
                                "weighting",
                                "area_basis",
                            )
                        )
                    ),
                    None,
                )
                if b is None:
                    continue
                comparison["deltas"].append(
                    dict(
                        base_metric_instance_id=a["metric_instance_id"],
                        alternative_metric_instance_id=b["metric_instance_id"],
                        value=b["value"] - a["value"],
                        unit=a["unit"],
                        mode=comparison["mode"],
                        changed_inputs=comparison["changed_inputs"],
                    )
                )
        finished = _now()
        if job.operation == "search_layouts":
            selected_ids = {entry["layout"].layout_id for entry in layouts if entry["selected"]}
            metrics.sort(key=lambda metric: metric["layout_id"] not in selected_ids)
        result = Result.model_validate(
            dict(
                schema_version="0.1.0",
                run_id=run_id,
                source_job_id=job.job_id,
                scenario_id=ref.scenario_id,
                scenario_revision=ref.revision,
                scope=ref.scope,
                input_fingerprint=job.input_fingerprint,
                input_snapshot_ref=ref,
                operation=job.operation,
                arguments=request.arguments,
                analytical_outcome=outcome,
                layouts=layouts,
                metrics=metrics,
                missing_metrics=[],
                comparison=comparison,
                constraints=constraints,
                assumptions=scenario["assumptions"],
                limitations=[
                    "Synthetic local engineering proof; no accepted Sheffield site",
                    "Assumed crown geometry/cost/transmission; survey requirements remain unknown",
                    "CPU direct-beam discretised model; no temperature, building energy, carbon or biological prediction",
                    "Search reports best evaluated finite-catalogue layout; no global optimality claim",
                ],
                source_ids=sorted(set().union(*(set(e[4]["sources"]) for e in entries))),
                provenance=dict(
                    tool_version=application_version(),
                    evaluator_version=scenario["numerics"]["evaluator_version"],
                    solar_version=scenario["numerics"]["solar_version"],
                    search_version=scenario["search"]["version"],
                    schema_version="0.1.0",
                    seed=scenario["search"]["seed"],
                    created_at_utc=_now(),
                    compute_started_at_utc=started,
                    compute_finished_at_utc=finished,
                    timings_s={"analysis": perf_counter() - tick},
                    physics_device=dict(
                        name="CPU", backend="Python", version=sys.version.split()[0]
                    ),
                    inference_device=None,
                    source_hashes=identity["content_hashes"],
                    execution_mode="live",
                ),
            )
        )
        if job.operation == "search_layouts":
            self._validate_search(deps, result, problem, evaluate, ref)
        resolve()
        stop()
        return result

    def _validate_search(self, deps, result, problem, evaluate, ref):
        """Recompute every returned layout and metric; optimiser scores are not authority."""
        verdicts = []
        target_met = None
        target = deps["scenario"]["input"]["objective"]
        for entry in result.layouts:
            verdict = self.check(
                problem, entry.layout.model_dump(mode="json")["placements"], evaluate
            )
            records = tuple(
                dict(
                    **dict(c),
                    scenario_ref=ref.model_dump(mode="json"),
                    layout_id=entry.layout.layout_id,
                )
                for c in verdict.records
            )
            verdicts.append(
                LayoutVerdict(
                    entry.layout.layout_id,
                    "feasible" if verdict.feasible else "infeasible",
                    verdict.cost_pence,
                    records,
                )
            )
            case_map = {c["case_id"]: c for c in verdict.evaluation["cases"]}
            for metric in (m for m in result.metrics if m.layout_id == entry.layout.layout_id):
                row = case_map[metric.case_id]
                if metric.target_id is not None:
                    row = next(t for t in row["targets"] if t["target_id"] == metric.target_id)
                actual = (
                    row["weighted_m2_h"]
                    if metric.metric_id == "weighted_shade_utility"
                    else row["physical_m2_h"]
                )
                if metric.value != actual:
                    raise ValueError("Independent physical metric mismatch")
            if target["kind"] == "minimise_cost_for_target":
                met = (
                    case_map[target["primary_case_id"]]["physical_m2_h"]
                    >= target["target_gain_m2_h"]
                )
                if entry.selected or target_met is None:
                    target_met = met
                elif met:
                    target_met = True
        independent = SearchVerdict(tuple(verdicts), result.analytical_outcome, target_met, False)
        SearchHandler._check(
            result,
            independent,
            deps,
            __import__("tree_planner.contracts", fromlist=["Scenario"]).Scenario.model_validate(
                deps["scenario"]
            ),
            ref,
        )


@dataclass
class PhysicalRuntime:
    app: object
    scenario_ref: ScenarioRef
    scene_path: Path
    handler: PhysicalHandler


def create_physical_runtime(workspace: Path, *, start_worker=True, winter=False):
    from .physical_seed import seed_physical, synthetic_scene

    workspace = Path(workspace).resolve()
    if workspace.exists() and any(workspace.iterdir()):
        raise ValueError("A fresh empty numerical workspace is required")
    assets = workspace / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    scene_path = assets / "physical-scene.json"
    data = canonical_bytes(synthetic_scene())
    if scene_path.exists() and scene_path.read_bytes() != data:
        raise ValueError("Existing registered scene differs; choose a fresh workspace")
    scene_path.write_bytes(data)
    handler = PhysicalHandler()
    app = create_app(
        workspace,
        handlers={name: handler for name in OPERATIONS},
        capabilities=Capabilities(
            evaluator_versions=["canopy-cpu-reference@takeover-v1"],
            solar_versions=["pvlib-spa-geometric@0.15.2"],
            search_versions=["overlap-greedy-local@takeover-v1"],
        ),
        geometry_refs=frozenset({"receiver", "planting", "study", "context"}),
        start_worker=start_worker,
    )
    handler.service = app.state.service
    _, scenario = seed_physical(app.state.service, winter=winter)
    ref = ScenarioRef(
        scenario_id=scenario.scenario_id, revision=scenario.revision, scope=scenario.scope
    )
    return PhysicalRuntime(app, ref, scene_path, handler)
