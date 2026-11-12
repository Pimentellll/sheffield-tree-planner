"""Source trust and execution identity for the production synthetic factory."""

from dataclasses import FrozenInstanceError, replace
import os
import json
from pathlib import Path
import shutil

import pytest

from tree_planner.evaluators import ReferenceJobHandler, ReferenceUnsupported
from tree_planner.evaluators.runtime import SyntheticScene, create_reference_runtime, load_numerics


@pytest.fixture
def source():
    value = os.environ.get("CANOPY_NUMERICS_SOURCE")
    if not value:
        pytest.skip("real numerical source not configured")
    return Path(value)


def test_trusted_runtime_identity_and_immutable_inputs(tmp_path, source):
    runtime = create_reference_runtime(tmp_path / "runtime", numerical_source=source)
    ref = runtime.scenario_ref
    deps, hashes = runtime.app.state.service.resolve_for_execution(ref, operation="evaluate_layout")
    resolved = runtime.handler.execution_hashes(deps, operation="evaluate_layout")
    assert {"execution:" + k: v for k, v in resolved.items()}.items() <= hashes.items()
    assert runtime.handler.execution_hashes(deps, operation="evaluate_layout") == resolved
    request = runtime.request("identity")
    numerical = runtime.handler.provider.resolve_inputs(deps, request.root)
    with pytest.raises(FrozenInstanceError):
        numerical.samples[0].area_m2 = 99
    with pytest.raises(FrozenInstanceError):
        runtime.scene.receiver_area_m2 = 99
    assert numerical.samples[0].area_m2 == 2
    with pytest.raises(ReferenceUnsupported):
        runtime.handler.execution_hashes(deps, operation="search_layouts")


@pytest.mark.parametrize(
    "field,value",
    [
        ("receiver_area_m2", 3.0),
        ("receiver_point", (0.1, 0.0, 0.0)),
        ("sun_direction", (0.0, 0.0, 1.0)),
        ("obstacle_ellipsoids", (((0.0, -1.0, 1.0), (0.5, 0.5, 0.5)),)),
    ],
)
def test_scene_changes_execution_identity(tmp_path, source, field, value):
    one = create_reference_runtime(tmp_path / "one", numerical_source=source)
    two = create_reference_runtime(
        tmp_path / "two", numerical_source=source, scene=replace(SyntheticScene(), **{field: value})
    )
    first = one.app.state.service.resolve_for_execution(
        one.scenario_ref, operation="evaluate_layout"
    )[1]
    second = two.app.state.service.resolve_for_execution(
        two.scenario_ref, operation="evaluate_layout"
    )[1]
    assert first["execution:numerical_inputs"] != second["execution:numerical_inputs"]
    assert first["execution:implementation"] == second["execution:implementation"]


def test_dependency_and_layout_binding_fail_closed(tmp_path, source):
    runtime = create_reference_runtime(tmp_path / "runtime", numerical_source=source)
    deps, _ = runtime.app.state.service.resolve_for_execution(
        runtime.scenario_ref, operation="evaluate_layout"
    )
    import copy

    forged = copy.deepcopy(deps)
    forged["site"]["semantic_revision"] += 1
    with pytest.raises(ReferenceUnsupported, match="site"):
        runtime.handler.execution_hashes(forged, operation="evaluate_layout")
    changed = copy.deepcopy(deps)
    changed["layout"]["placements"][0]["position_enu_m"][0] = 20.0
    assert (
        runtime.handler.execution_hashes(changed, operation="evaluate_layout")["numerical_inputs"]
        != runtime.handler.execution_hashes(deps, operation="evaluate_layout")["numerical_inputs"]
    )


def test_changed_source_rejected_at_load_and_after_startup(tmp_path, source):
    root = tmp_path / "numerics"
    physics = root / "backend/src/tree_planner/physics"
    physics.mkdir(parents=True)
    for name in ("ray.py", "shade_reference.py"):
        shutil.copyfile(source / "backend/src/tree_planner/physics" / name, physics / name)
    runtime = create_reference_runtime(tmp_path / "runtime", numerical_source=root)
    path = physics / "ray.py"
    path.write_bytes(path.read_bytes() + b"\n# changed\n")
    with pytest.raises(ReferenceUnsupported, match="source"):
        load_numerics(root)
    with pytest.raises(ReferenceUnsupported, match="source"):
        runtime.app.state.service.resolve_for_execution(
            runtime.scenario_ref, operation="evaluate_layout"
        )


def test_loaded_callable_mutation_rejected(tmp_path, source):
    runtime = create_reference_runtime(tmp_path / "runtime", numerical_source=source)
    runtime.numerical.shade.evaluate_one_tree_synthetic = lambda *a, **k: None
    with pytest.raises(ReferenceUnsupported, match="implementation"):
        runtime.app.state.service.resolve_for_execution(
            runtime.scenario_ref, operation="evaluate_layout"
        )


@pytest.mark.parametrize("field", ["sample", "sun", "obstacle", "tree"])
def test_exact_numerical_content_changes_hash_under_same_dependencies(tmp_path, source, field):
    runtime = create_reference_runtime(tmp_path / "runtime", numerical_source=source)
    deps, _ = runtime.app.state.service.resolve_for_execution(
        runtime.scenario_ref, operation="evaluate_layout"
    )
    before = runtime.handler.execution_hashes(deps, operation="evaluate_layout")
    p = runtime.numerical.shade

    def changed_inputs(dependencies, request):
        original = runtime.handler.provider.resolve_inputs(dependencies, request)
        if field == "sample":
            return replace(original, samples=(replace(original.samples[0], area_m2=3.0),))
        if field == "sun":
            return replace(
                original, bins=(replace(original.bins[0], direction_enu=(0.0, 0.0, 1.0)),)
            )
        if field == "obstacle":
            return replace(
                original, obstacles=(p.OpaqueEllipsoid((0.0, -1.0, 1.0), (0.5, 0.5, 0.5)),)
            )
        return replace(
            original,
            tree=replace(
                original.tree, crown=replace(original.tree.crown, radii_m=(1.0, 1.0, 1.0))
            ),
        )

    handler = ReferenceJobHandler(replace(runtime.handler.provider, resolve_inputs=changed_inputs))
    after = handler.execution_hashes(deps, operation="evaluate_layout")
    assert before["binding"] == after["binding"]
    assert before["configuration"] == after["configuration"]
    assert before["numerical_inputs"] != after["numerical_inputs"]


def test_changed_provider_code_changes_identity_without_changing_versions(tmp_path, source):
    runtime = create_reference_runtime(tmp_path / "runtime", numerical_source=source)
    deps, _ = runtime.app.state.service.resolve_for_execution(
        runtime.scenario_ref, operation="evaluate_layout"
    )
    before = runtime.handler.execution_hashes(deps, operation="evaluate_layout")

    def changed_evaluate(*args, **kwargs):
        raise RuntimeError("different implementation")

    handler = ReferenceJobHandler(replace(runtime.handler.provider, evaluate=changed_evaluate))
    after = handler.execution_hashes(deps, operation="evaluate_layout")
    assert before["numerical_inputs"] == after["numerical_inputs"]
    assert before["configuration"] == after["configuration"]
    assert before["implementation"] != after["implementation"]


def test_loaded_class_mutation_rejected(tmp_path, source):
    runtime = create_reference_runtime(tmp_path / "runtime", numerical_source=source)
    runtime.numerical.shade.ReceiverSample.__init__ = lambda *args: None
    with pytest.raises(ReferenceUnsupported, match="implementation"):
        runtime.app.state.service.resolve_for_execution(
            runtime.scenario_ref, operation="evaluate_layout"
        )


def test_scene_rejects_mutable_or_invalid_geometry():
    with pytest.raises(ValueError, match="immutable"):
        SyntheticScene(receiver_point=[0, 0, 0])
    with pytest.raises(ValueError, match="immutable"):
        SyntheticScene(obstacle_ellipsoids=[])
    with pytest.raises(ValueError, match="vector"):
        SyntheticScene(receiver_normal=(0.0, 0.0, 2.0))
    with pytest.raises(ValueError, match="horizon"):
        SyntheticScene(above_horizon=False)


def test_demo_failed_invariant_exits_nonzero_and_stops_owned_server(tmp_path, source, monkeypatch):
    from tree_planner.evaluators import demo

    original = demo._require

    def fail_positive_invariant(condition, message):
        original(False if message == "analytic positive invariant failed" else condition, message)

    monkeypatch.setattr(demo, "_require", fail_positive_invariant)
    output = tmp_path / "failed-demo"
    assert demo.main(["--output", str(output), "--numerical-source", str(source)]) == 1
    evidence = json.loads((output / "evidence.json").read_text(encoding="utf-8"))
    assert evidence["status"] == "failed"
    assert evidence["failure"]["message"] == "analytic positive invariant failed"
    assert evidence["checks"]["owned_server_stopped"]
    assert evidence["checks"]["owned_worker_stopped"]
    # The failure was an invariant after a real positive HTTP Result, not a fake
    # successful result fixture or a mocked transport.
    results = [x for x in evidence["http"] if x["path"].startswith("/api/v1/results/")]
    assert results[0]["status"] == 200
    assert results[0]["body"]["metrics"][0]["value"] == 2.0
