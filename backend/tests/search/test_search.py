"""Synthetic finite examples; calculations below are not Sheffield evidence."""

import pytest
from tree_planner.search import prepare, check, search, relocate
from tree_planner.site.service import catalogue_fingerprint
from tree_planner.contracts import SiteBundle
from backend.tests.site.synthetic_inputs import site_data, input_data, profile_data


def deps():
    site = site_data()
    scenario = input_data()
    profile = profile_data()
    profile["cost_pence"] = 5
    site["candidate_catalogue"] = [
        dict(
            candidate_id=f"c{i}",
            location_id=f"l{i}",
            position_enu_m=[i * 3, 0, 0],
            profile_id="synthetic-profile",
            plantability_status="provisional",
            source_ids=[],
            assumption_ids=["synthetic"],
        )
        for i in range(3)
    ]
    site["candidate_catalogue_fingerprint"] = catalogue_fingerprint(
        SiteBundle.model_validate(site).candidate_catalogue
    )
    scenario["candidate_catalogue_fingerprint"] = site["candidate_catalogue_fingerprint"]
    scenario["constraints"]["budget_pence"] = 10
    return dict(
        site=site,
        scenario=dict(
            schema_version="0.1.0",
            scenario_id="s",
            revision=1,
            created_at_utc="2026-11-13T00:00:00Z",
            scope="accepted",
            base_scenario_ref=None,
            input=scenario,
        ),
        profiles={"synthetic-profile": profile},
        scene={"regions": {}, "flat_ground_z_m": 0},
    )


def calc(placements):
    cells = {"c0": {0, 1, 2}, "c1": {2, 3, 4}, "c2": {5, 6}}
    area = len(set().union(*(cells[p["candidate_id"]] for p in placements)))
    return {
        "cases": [
            {
                "case_id": "summer",
                "role": "benefit",
                "quantity_kind": "geometric",
                "physical_m2_h": float(area),
                "weighted_m2_h": float(area),
                "targets": [{"target_id": "target", "physical_m2_h": float(area)}],
            }
        ]
    }


def test_overlap_and_independent_validator():
    p = prepare(deps())
    result = search(p, calc)
    assert result.best.score == 5
    assert result.best.cost_pence == 10
    assert check(p, result.best.placements, calc).feasible
    assert not check(p, result.best.placements + result.best.placements, calc).feasible
    assert search(p, calc).best == result.best


def test_fingerprint_and_unresolved_regions_fail_closed():
    d = deps()
    d["site"]["candidate_catalogue"][0]["position_enu_m"][0] = 50
    with pytest.raises(ValueError):
        prepare(d)
    d = deps()
    d["scenario"]["input"]["constraints"]["accepted_planting_region_ids"] = ["missing"]
    with pytest.raises(ValueError):
        prepare(d)


def test_relocation_keeps_identity_and_others():
    p = prepare(deps())
    result = search(p, calc)
    old = result.best.placements
    moved = relocate(p, old, old[0]["placement_id"], [6, 0, 0], calc)
    assert moved.placements[0]["placement_id"] == old[0]["placement_id"]
    assert moved.placements[1:] == old[1:]
    assert moved.verdict.feasible is False
    assert moved.verdict.evaluation is not None


def test_stop_is_not_a_result():
    with pytest.raises(InterruptedError):
        search(prepare(deps()), calc, stop=lambda: True)


def test_budget_count_spacing_and_ground_rejected():
    d = deps()
    d["scenario"]["input"]["constraints"]["spacing_rules"] = [
        dict(
            minimum_centre_separation_m=4,
            clearance_state="mature",
            model_basis="synthetic",
            evidence=[],
        )
    ]
    p = prepare(d)
    candidates = p.site.candidate_catalogue
    from tree_planner.search import _placement

    assert (
        "spacing" in check(p, (_placement(candidates[0]), _placement(candidates[1])), calc).reasons
    )
    assert "budget" in check(p, tuple(_placement(c) for c in candidates), calc).reasons
    d["scene"]["flat_ground_z_m"] = 1
    p = prepare(d)
    assert "terrain attachment" in check(p, (_placement(candidates[0]),), calc).reasons


def test_target_miss_and_exact_tiny_enumeration():
    d = deps()
    d["scenario"]["input"]["objective"].update(kind="minimise_cost_for_target", target_gain_m2_h=20)
    p = prepare(d)
    result = search(p, calc, exact_limit=3)
    assert result.outcome == "search_exhausted_without_target"
    assert result.best.score == 5
    assert result.proof_verified is False


def test_empty_and_no_eligible():
    d = deps()
    d["scenario"]["input"]["constraints"]["allowed_profile_ids"] = []
    assert search(prepare(d), calc).outcome == "feasible_zero_planting"
    d["scenario"]["input"]["objective"].update(kind="minimise_cost_for_target", target_gain_m2_h=1)
    assert search(prepare(d), calc).outcome == "no_eligible_candidates"


def test_polygon_boundaries_exclusions_and_invalid_geometry():
    d = deps()
    d["site"]["planting_regions"] = [
        dict(
            feature_id="plant",
            geometry_ref="g",
            evidence_status="synthetic",
            source_ids=[],
            assumption_ids=["synthetic"],
        )
    ]
    d["site"]["exclusions"] = [
        dict(
            feature_id="ban",
            geometry_ref="b",
            evidence_status="synthetic",
            source_ids=[],
            assumption_ids=["synthetic"],
        )
    ]
    rules = d["scenario"]["input"]["constraints"]
    rules["accepted_planting_region_ids"] = ["plant"]
    rules["excluded_region_ids"] = ["ban"]
    d["scene"]["regions"] = {
        "plant": [[0, -1], [9, -1], [9, 1], [0, 1]],
        "ban": [[2, -1], [4, -1], [4, 1], [2, 1]],
    }
    from tree_planner.search import _placement

    p = prepare(d)
    assert check(p, (_placement(p.site.candidate_catalogue[0]),), calc).feasible
    assert "excluded region" in check(p, (_placement(p.site.candidate_catalogue[1]),), calc).reasons
    d["scene"]["regions"]["plant"] = [[0, 0], [5, 5], [0, 5], [5, 0], [6, 2]]
    with pytest.raises(ValueError, match="polygon"):
        prepare(d)


def test_pins_conflicts_profile_and_count():
    from tree_planner.search import _placement

    d = deps()
    p = prepare(d)
    a, b, c = map(_placement, p.site.candidate_catalogue)
    a["pinned"] = True
    d["scenario"]["input"]["constraints"]["pinned_placements"] = [a]
    d["scenario"]["input"]["constraints"]["max_tree_count"] = 1
    d["scenario"]["input"]["constraints"]["incompatible_candidate_pairs"] = [["c0", "c1"]]
    p = prepare(d)
    assert "missing pin" in check(p, (b,), calc).reasons
    verdict = check(p, (a, b), calc)
    assert "count" in verdict.reasons and "incompatible pair" in verdict.reasons
    assert any(
        r["rule"] == "survey:synthetic survey required" and r["status"] == "unknown"
        for r in verdict.records
    )
    d["scenario"]["input"]["constraints"]["allowed_profile_ids"] = []
    assert "profile not allowed" in check(prepare(d), (a,), calc).reasons


def test_bad_terrain_and_unknown_candidate_pair_fail_closed():
    d = deps()
    del d["scene"]["flat_ground_z_m"]
    with pytest.raises(ValueError, match="terrain"):
        prepare(d)
    d = deps()
    d["scenario"]["input"]["constraints"]["incompatible_candidate_pairs"] = [["c0", "missing"]]
    with pytest.raises(ValueError, match="candidate"):
        prepare(d)


def test_swap_improves_greedy_and_matches_exhaustive_synthetic():
    def synthetic_union(placements):
        cells = {"c0": {0, 1, 2}, "c1": {0, 1, 3}, "c2": {2, 4}}
        value = float(len(set().union(*(cells[p["candidate_id"]] for p in placements))))
        return {
            "cases": [
                {
                    "case_id": "summer",
                    "role": "benefit",
                    "quantity_kind": "geometric",
                    "physical_m2_h": value,
                    "weighted_m2_h": value,
                    "targets": [],
                }
            ]
        }

    p = prepare(deps())
    heuristic = search(p, synthetic_union)
    exact = search(p, synthetic_union, exact_limit=3)
    assert heuristic.best.score == exact.best.score == 5
    assert any(step[0] == "improve" for step in heuristic.trace)
    assert heuristic.reference.score == 4
    assert exact.proof_verified is False


def test_invalid_candidate_and_pence_types_are_rejected():
    d = deps()
    d["profiles"]["synthetic-profile"]["cost_pence"] = 5.5
    with pytest.raises(ValueError):
        prepare(d)
    d = deps()
    d["site"]["candidate_catalogue"][0]["plantability_status"] = "unknown"
    with pytest.raises(ValueError):
        prepare(d)


def test_real_physics_search_matches_tiny_exhaustive():
    physics = pytest.importorskip("tree_planner.physics")
    d = deps()
    n = d["scenario"]["input"]["numerics"]
    n.update(
        evaluator="canopy-cpu-reference",
        evaluator_version="takeover-v1",
        solar_algorithm="pvlib-spa-geometric",
        solar_version="0.15.2",
        ray_offset_m=1e-6,
        intersection_tolerance_m=1e-10,
        feasibility_tolerance=1e-9,
    )
    d["scene"].update(
        format_version="canopy-physical-scene/1",
        spatial_spacing_m=1.0,
        triangles=[],
        existing_trees=[],
        samples=[
            {
                "sample_id": f"s{i}",
                "position_enu_m": [float(i), 0, 0],
                "normal_enu": [0, 0, 1],
                "area_m2": 1.0,
                "target_id": "target",
                "area_basis": "surface",
            }
            for i in range(10)
        ],
    )
    p = prepare(d)

    def evaluate(placements):
        return physics.compute(d, placements)

    result = search(p, evaluate)
    exact = search(p, evaluate, exact_limit=3)
    assert result.best.score <= exact.best.score
    assert check(p, result.best.placements, evaluate).feasible
    assert result.best.score == pytest.approx(
        evaluate(result.best.placements)["cases"][0]["physical_m2_h"]
    )


def test_real_physics_winter_limits_aggregate_and_target():
    from copy import deepcopy
    from dataclasses import replace
    from tree_planner.contracts.scenario import EvaluationCase, WinterLimit
    from tree_planner.search import _placement

    physics = pytest.importorskip("tree_planner.physics")
    d = deps()
    d["scenario"]["input"]["numerics"].update(
        evaluator="canopy-cpu-reference",
        evaluator_version="takeover-v1",
        solar_algorithm="pvlib-spa-geometric",
        solar_version="0.15.2",
        ray_offset_m=1e-6,
        intersection_tolerance_m=1e-10,
        feasibility_tolerance=1e-9,
    )
    d["scene"].update(
        format_version="canopy-physical-scene/1",
        spatial_spacing_m=1.0,
        triangles=[],
        existing_trees=[],
        samples=[
            {
                "sample_id": "s",
                "position_enu_m": [0.0, 0.0, 0.0],
                "normal_enu": [0.0, 0.0, 1.0],
                "area_m2": 1.0,
                "target_id": "target",
                "area_basis": "surface",
            }
        ],
    )
    p = prepare(d)
    winter = deepcopy(d["scenario"]["input"]["evaluation_cases"][0])
    winter.update(case_id="synthetic-winter", role="winter_check")
    d["scenario"]["input"]["evaluation_cases"].append(winter)
    limits = [
        WinterLimit(case_id="synthetic-winter", target_id=None, maximum_loss_m2_h=0),
        WinterLimit(case_id="synthetic-winter", target_id="target", maximum_loss_m2_h=0),
    ]
    inp = p.scenario.input.model_copy(
        update={
            "evaluation_cases": p.scenario.input.evaluation_cases
            + (EvaluationCase.model_validate(winter),),
            "constraints": p.scenario.input.constraints.model_copy(
                update={"winter_limits": tuple(limits)}
            ),
        }
    )
    p = replace(p, scenario=p.scenario.model_copy(update={"input": inp}))
    verdict = check(
        p,
        (_placement(p.site.candidate_catalogue[0]),),
        lambda placements: physics.compute(d, placements),
    )
    winter_records = [r for r in verdict.records if r["rule"].startswith("winter loss")]
    assert len(winter_records) == 2
    assert all(r["observed_value"] > 0 and r["status"] == "fail" for r in winter_records)
    assert not verdict.feasible


def test_maximisation_uses_weighted_utility_target_uses_physical():
    d = deps()
    d["scenario"]["input"]["constraints"]["max_tree_count"] = 1

    def weighted(placements):
        cid = placements[0]["candidate_id"] if placements else None
        physical = {"c0": 5.0, "c1": 2.0, "c2": 0.0, None: 0.0}[cid]
        utility = {"c0": 5.0, "c1": 8.0, "c2": 0.0, None: 0.0}[cid]
        return {
            "cases": [
                {
                    "case_id": "summer",
                    "role": "benefit",
                    "quantity_kind": "geometric",
                    "physical_m2_h": physical,
                    "weighted_m2_h": utility,
                    "targets": [],
                }
            ]
        }

    max_result = search(prepare(d), weighted)
    assert max_result.best.placements[0]["candidate_id"] == "c1"
    assert max_result.best.score == 8
    d["scenario"]["input"]["objective"].update(kind="minimise_cost_for_target", target_gain_m2_h=4)
    target_result = search(prepare(d), weighted)
    assert target_result.best.placements[0]["candidate_id"] == "c0"
    assert target_result.best.score == 5


def test_final_checker_rejects_compromised_search_admission(monkeypatch):
    import tree_planner.search as search_module

    p = prepare(deps())

    def compromised(problem, placements, evaluate):
        return len(placements) * 5, evaluate(list(placements))

    monkeypatch.setattr(search_module, "_admissible", compromised)
    result = search_module.search(p, calc)
    assert result.best.cost_pence > p.scenario.input.constraints.budget_pence
    verdict = search_module.check(p, result.best.placements, calc)
    assert not verdict.feasible
    assert "budget" in verdict.reasons


def test_valid_concave_u_region_and_manual_placement():
    d = deps()
    d["site"]["planting_regions"] = [
        dict(
            feature_id="plant",
            geometry_ref="g",
            evidence_status="synthetic",
            source_ids=[],
            assumption_ids=["synthetic"],
        )
    ]
    d["scenario"]["input"]["constraints"]["accepted_planting_region_ids"] = ["plant"]
    d["scene"]["regions"] = {
        "plant": [[0, 0], [3, 0], [3, 3], [2, 3], [2, 1], [1, 1], [1, 3], [0, 3]]
    }
    p = prepare(d)
    manual = dict(
        placement_id="manual",
        location_id="manual",
        position_enu_m=[0.5, 0.5, 0],
        profile_id="synthetic-profile",
        candidate_id=None,
        pinned=False,
    )
    assert check(p, (manual,), lambda _: calc([])).feasible


def test_manual_requires_explicit_region_and_supports_pins():
    d = deps()
    manual = dict(
        placement_id="manual",
        location_id="manual",
        position_enu_m=[0.5, 0.5, 0],
        profile_id="synthetic-profile",
        candidate_id=None,
        pinned=True,
    )
    assert not check(prepare(d), (manual,), lambda _: calc([])).feasible
    d["site"]["planting_regions"] = [
        dict(
            feature_id="plant",
            geometry_ref="g",
            evidence_status="synthetic",
            source_ids=[],
            assumption_ids=["synthetic"],
        )
    ]
    d["scene"]["regions"] = {"plant": [[-1, -1], [10, -1], [10, 3], [-1, 3]]}
    rules = d["scenario"]["input"]["constraints"]
    rules["accepted_planting_region_ids"] = ["plant"]
    rules["pinned_placements"] = [manual]
    p = prepare(d)

    def evaluate(items):
        return calc([i for i in items if i["candidate_id"] is not None])

    assert check(p, (manual,), evaluate).feasible
    result = search(p, evaluate)
    assert result.best.placements[0] == manual
    assert check(p, result.best.placements, evaluate).feasible


def test_manual_pin_with_real_physics():
    physics = pytest.importorskip("tree_planner.physics")
    d = deps()
    d["scenario"]["input"]["numerics"].update(
        evaluator="canopy-cpu-reference",
        evaluator_version="takeover-v1",
        solar_algorithm="pvlib-spa-geometric",
        solar_version="0.15.2",
        ray_offset_m=1e-6,
        intersection_tolerance_m=1e-10,
        feasibility_tolerance=1e-9,
    )
    d["site"]["planting_regions"] = [
        dict(
            feature_id="plant",
            geometry_ref="g",
            evidence_status="synthetic",
            source_ids=[],
            assumption_ids=["synthetic"],
        )
    ]
    manual = dict(
        placement_id="manual",
        location_id="manual",
        position_enu_m=[0.5, 0, 0],
        profile_id="synthetic-profile",
        candidate_id=None,
        pinned=True,
    )
    d["scenario"]["input"]["constraints"].update(
        accepted_planting_region_ids=["plant"], pinned_placements=[manual]
    )
    d["scene"].update(
        regions={"plant": [[-1, -1], [10, -1], [10, 1], [-1, 1]]},
        format_version="canopy-physical-scene/1",
        spatial_spacing_m=1.0,
        triangles=[],
        existing_trees=[],
        samples=[
            {
                "sample_id": "s",
                "position_enu_m": [0.0, 0.0, 0.0],
                "normal_enu": [0.0, 0.0, 1.0],
                "area_m2": 1.0,
                "target_id": "target",
                "area_basis": "surface",
            }
        ],
    )
    p = prepare(d)

    def evaluate(items):
        return physics.compute(d, items)

    result = search(p, evaluate)
    assert result.best.placements[0] == manual
    assert check(p, result.best.placements, evaluate).feasible
    assert result.best.evaluation["cases"][0]["physical_m2_h"] > 0
