"""Deterministic finite search and independent model-feasibility primitives.

The evaluator is supplied by the caller and must calculate complete layouts. No
search output establishes survey clearance or global optimality.
"""

from dataclasses import dataclass
from itertools import combinations
import math

from tree_planner.contracts import SiteBundle, Scenario, TreeProfile, Placement
from tree_planner.site.service import catalogue_fingerprint

SEARCH_VERSION = "takeover-v1"


@dataclass(frozen=True)
class Problem:
    site: object
    scenario: object
    profiles: dict
    regions: dict
    flat_ground_z_m: float


@dataclass(frozen=True)
class Verdict:
    feasible: bool
    reasons: tuple
    cost_pence: int
    evaluation: dict | None
    records: tuple


@dataclass(frozen=True)
class Choice:
    placements: tuple
    score: float
    cost_pence: int
    evaluation: dict


@dataclass(frozen=True)
class SearchResult:
    reference: Choice | None
    best: Choice | None
    outcome: str
    trace: tuple
    evaluated: int
    proof_verified: bool = False


@dataclass(frozen=True)
class Comparison:
    placements: tuple
    verdict: Verdict
    changed_inputs: tuple
    mode: str = "controlled_relocation"


def prepare(deps):
    site = SiteBundle.model_validate(deps["site"])
    scenario = Scenario.model_validate(deps["scenario"])
    profiles = {k: TreeProfile.model_validate(v) for k, v in deps["profiles"].items()}
    inp = scenario.input
    if (
        site.site_id,
        site.scene_revision,
        site.semantic_revision,
        site.profile_library_revision,
        site.candidate_catalogue_revision,
        site.candidate_catalogue_fingerprint,
    ) != (
        inp.site_id,
        inp.scene_revision,
        inp.semantic_revision,
        inp.profile_library_revision,
        inp.candidate_catalogue_revision,
        inp.candidate_catalogue_fingerprint,
    ):
        raise ValueError("site/scenario identity mismatch")
    if catalogue_fingerprint(site.candidate_catalogue) != site.candidate_catalogue_fingerprint:
        raise ValueError("candidate catalogue fingerprint mismatch")
    if any(
        k != p.profile_id or p.library_revision != inp.profile_library_revision
        for k, p in profiles.items()
    ):
        raise ValueError("profile identity mismatch")
    if any(c.profile_id not in profiles for c in site.candidate_catalogue):
        raise ValueError("unresolved candidate profile")
    rules = inp.constraints
    known = {f.feature_id for f in site.planting_regions}
    excluded = {f.feature_id for f in site.exclusions}
    if (
        not set(rules.accepted_planting_region_ids) <= known
        or not set(rules.excluded_region_ids) <= excluded
    ):
        raise ValueError("unresolved region feature")
    scene = deps.get("scene", {})
    ground = scene.get("flat_ground_z_m")
    if (
        scene.get("terrain") is not None
        or type(ground) not in (int, float)
        or not math.isfinite(ground)
    ):
        raise ValueError("unsupported or missing terrain")
    regions = scene.get("regions", {})
    for key in (*rules.accepted_planting_region_ids, *rules.excluded_region_ids):
        poly = regions.get(key)
        if (
            not isinstance(poly, list)
            or len(poly) < 3
            or any(
                not isinstance(p, list)
                or len(p) != 2
                or any(type(x) not in (int, float) or not math.isfinite(x) for x in p)
                for p in poly
            )
        ):
            raise ValueError("unresolved or invalid region polygon")
        if (
            abs(
                sum(
                    poly[i][0] * poly[(i + 1) % len(poly)][1]
                    - poly[(i + 1) % len(poly)][0] * poly[i][1]
                    for i in range(len(poly))
                )
            )
            < 1e-12
        ):
            raise ValueError("degenerate region polygon")
        if len({tuple(v) for v in poly}) != len(poly):
            raise ValueError("repeated polygon vertex")

        def orient(a, b, c):
            return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

        for i in range(len(poly)):
            for j in range(i + 1, len(poly)):
                if j == i + 1 or (i == 0 and j == len(poly) - 1):
                    continue
                a, b = poly[i], poly[(i + 1) % len(poly)]
                c, d = poly[j], poly[(j + 1) % len(poly)]
                o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
                if o1 * o2 <= 0 and o3 * o4 <= 0:
                    raise ValueError("self-intersecting polygon")
    candidate_ids = {c.candidate_id for c in site.candidate_catalogue}
    if any(
        a not in candidate_ids or b not in candidate_ids
        for a, b in rules.incompatible_candidate_pairs
    ):
        raise ValueError("unresolved incompatible candidate")
    return Problem(site, scenario, profiles, regions, ground)


def _inside(point, poly):
    x, y = point[:2]
    inside = False
    for i, (x1, y1) in enumerate(poly):
        x2, y2 = poly[(i + 1) % len(poly)]
        cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
        if (
            abs(cross) <= 1e-10
            and min(x1, x2) - 1e-10 <= x <= max(x1, x2) + 1e-10
            and min(y1, y2) - 1e-10 <= y <= max(y1, y2) + 1e-10
        ):
            return True
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def _placement(c, pinned=False):
    return dict(
        placement_id="candidate:" + c.candidate_id,
        location_id=c.location_id,
        position_enu_m=list(c.position_enu_m),
        profile_id=c.profile_id,
        candidate_id=c.candidate_id,
        pinned=pinned,
    )


def check(problem, placements, evaluate, *, diagnostic=False):
    """Recompute all hard conditions from full placements; evaluator failures propagate."""
    rules = problem.scenario.input.constraints
    candidates = {c.candidate_id: c for c in problem.site.candidate_catalogue}
    reasons = []
    cost = 0
    parsed = []
    for raw in placements:
        try:
            p = Placement.model_validate(raw)
            parsed.append(p)
        except ValueError:
            reasons.append("invalid placement")
            continue
        if (
            abs(p.position_enu_m[2] - problem.flat_ground_z_m)
            > problem.scenario.input.numerics.intersection_tolerance_m
        ):
            reasons.append("terrain attachment")
        profile = problem.profiles.get(p.profile_id)
        if profile is None:
            reasons.append("unresolved profile")
            continue
        cost += profile.cost_pence
        c = candidates.get(p.candidate_id)
        if c is None or (p.location_id, p.position_enu_m, p.profile_id) != (
            c.location_id,
            c.position_enu_m,
            c.profile_id,
        ):
            reasons.append("candidate mismatch")
        elif c.plantability_status == "excluded":
            reasons.append("excluded candidate")
        if p.profile_id not in rules.allowed_profile_ids:
            reasons.append("profile not allowed")
        if rules.accepted_planting_region_ids and not any(
            _inside(p.position_enu_m, problem.regions[k])
            for k in rules.accepted_planting_region_ids
        ):
            reasons.append("outside planting regions")
        if any(_inside(p.position_enu_m, problem.regions[k]) for k in rules.excluded_region_ids):
            reasons.append("excluded region")
        for rule in rules.spacing_rules:
            if rule.clearance_state not in profile.states:
                reasons.append("missing clearance state")
        for case in problem.scenario.input.evaluation_cases:
            state = profile.states.get(case.profile_state)
            if state is None or state.horizon_years != case.horizon_years:
                reasons.append("missing case state")
    if len({p.placement_id for p in parsed}) != len(parsed):
        reasons.append("duplicate placement")
    if len({p.location_id for p in parsed}) != len(parsed) or len(
        {p.position_enu_m for p in parsed}
    ) != len(parsed):
        reasons.append("duplicate location")
    if cost > rules.budget_pence:
        reasons.append("budget")
    if rules.max_tree_count is not None and len(parsed) > rules.max_tree_count:
        reasons.append("count")
    for pin in rules.pinned_placements:
        if pin not in parsed:
            reasons.append("missing pin")
    conflicts = {frozenset(pair) for pair in rules.incompatible_candidate_pairs}
    for a, b in combinations(parsed, 2):
        if frozenset((a.candidate_id, b.candidate_id)) in conflicts:
            reasons.append("incompatible pair")
        if any(
            math.dist(a.position_enu_m, b.position_enu_m) < rule.minimum_centre_separation_m
            for rule in rules.spacing_rules
        ):
            reasons.append("spacing")
    evaluation = None
    winter_records = []
    if not reasons or diagnostic:
        evaluation = evaluate([p.model_dump(mode="json") for p in parsed])
        for limit in rules.winter_limits:
            case = next(
                (
                    c
                    for c in evaluation["cases"]
                    if c["case_id"] == limit.case_id and c["role"] == "winter_check"
                ),
                None,
            )
            if case is None:
                raise ValueError("winter case missing")
            if limit.target_id is not None:
                case = next((t for t in case["targets"] if t["target_id"] == limit.target_id), None)
                if case is None:
                    raise ValueError("winter target missing")
            val = case["physical_m2_h"]
            if not math.isfinite(val) or val < 0:
                raise ValueError("invalid winter loss")
            failed = val > limit.maximum_loss_m2_h
            if failed:
                reasons.append("winter limit")
            winter_records.append(
                dict(
                    case_id=limit.case_id,
                    rule="winter loss"
                    + (":" + limit.target_id if limit.target_id else ":aggregate"),
                    limit=limit.maximum_loss_m2_h,
                    observed_value=val,
                    unit="m2_h",
                    status="fail" if failed else "pass",
                    evidence=["computed winter case"],
                )
            )

    def record(rule, failed, limit=None, observed=None, unit=None):
        return dict(
            case_id=None,
            rule=rule,
            limit=limit,
            observed_value=observed,
            unit=unit,
            status="fail" if failed else "pass",
            evidence=["independent finite-model check"],
        )

    records = [record("budget", "budget" in reasons, rules.budget_pence, cost, "GBP_pence")]
    if rules.max_tree_count is not None:
        records.append(record("count", "count" in reasons, rules.max_tree_count, len(parsed)))
    groups = {
        "candidate and profile": (
            "invalid placement",
            "candidate mismatch",
            "excluded candidate",
            "unresolved profile",
            "profile not allowed",
            "missing case state",
        ),
        "location and terrain": ("duplicate placement", "duplicate location", "terrain attachment"),
        "regions": ("outside planting regions", "excluded region"),
        "pins": ("missing pin",),
        "spacing and conflicts": ("spacing", "incompatible pair", "missing clearance state"),
    }
    records.extend(
        record(name, any(r in reasons for r in failures)) for name, failures in groups.items()
    )
    if evaluation is None:
        winter_records.extend(
            dict(
                case_id=limit.case_id,
                rule="winter loss" + (":" + limit.target_id if limit.target_id else ":aggregate"),
                limit=limit.maximum_loss_m2_h,
                observed_value=None,
                unit="m2_h",
                status="unknown",
                evidence=[],
            )
            for limit in rules.winter_limits
        )
    records.extend(winter_records)
    records.extend(
        dict(
            case_id=None,
            rule="survey:" + survey,
            limit=None,
            observed_value=None,
            unit=None,
            status="unknown",
            evidence=[],
        )
        for survey in rules.survey_requirements
    )
    return Verdict(not reasons, tuple(reasons), cost, evaluation, tuple(records))


def _admissible(problem, placements, evaluate):
    """Search-side admission, deliberately separate from the final full checker."""
    rules = problem.scenario.input.constraints
    try:
        items = [Placement.model_validate(p) for p in placements]
    except ValueError:
        return None
    if (
        len({p.placement_id for p in items}) != len(items)
        or len({p.location_id for p in items}) != len(items)
        or len({p.position_enu_m for p in items}) != len(items)
    ):
        return None
    if any(pin not in items for pin in rules.pinned_placements):
        return None
    if rules.max_tree_count is not None and len(items) > rules.max_tree_count:
        return None
    candidates = {c.candidate_id: c for c in problem.site.candidate_catalogue}
    spend = 0
    for p in items:
        c = candidates.get(p.candidate_id)
        profile = problem.profiles.get(p.profile_id)
        if (
            c is None
            or profile is None
            or c.plantability_status == "excluded"
            or p.profile_id not in rules.allowed_profile_ids
        ):
            return None
        if (p.location_id, p.position_enu_m, p.profile_id) != (
            c.location_id,
            c.position_enu_m,
            c.profile_id,
        ):
            return None
        if (
            abs(p.position_enu_m[2] - problem.flat_ground_z_m)
            > problem.scenario.input.numerics.intersection_tolerance_m
        ):
            return None
        if rules.accepted_planting_region_ids and not any(
            _inside(p.position_enu_m, problem.regions[k])
            for k in rules.accepted_planting_region_ids
        ):
            return None
        if any(_inside(p.position_enu_m, problem.regions[k]) for k in rules.excluded_region_ids):
            return None
        if any(r.clearance_state not in profile.states for r in rules.spacing_rules):
            return None
        for case in problem.scenario.input.evaluation_cases:
            state = profile.states.get(case.profile_state)
            if state is None or state.horizon_years != case.horizon_years:
                return None
        spend += profile.cost_pence
    if spend > rules.budget_pence:
        return None
    conflicts = {frozenset(pair) for pair in rules.incompatible_candidate_pairs}
    for a, b in combinations(items, 2):
        if frozenset((a.candidate_id, b.candidate_id)) in conflicts:
            return None
        if any(
            math.dist(a.position_enu_m, b.position_enu_m) < r.minimum_centre_separation_m
            for r in rules.spacing_rules
        ):
            return None
    result = evaluate([p.model_dump(mode="json") for p in items])
    for limit in rules.winter_limits:
        case = next(
            (
                c
                for c in result["cases"]
                if c["case_id"] == limit.case_id and c["role"] == "winter_check"
            ),
            None,
        )
        if case is None:
            raise ValueError("winter case missing")
        if limit.target_id is not None:
            case = next((t for t in case["targets"] if t["target_id"] == limit.target_id), None)
            if case is None:
                raise ValueError("winter target missing")
        loss = case["physical_m2_h"]
        if not math.isfinite(loss) or loss < 0:
            raise ValueError("invalid winter loss")
        if loss > limit.maximum_loss_m2_h:
            return None
    return spend, result


def _score(problem, result):
    obj = problem.scenario.input.objective
    cases = [
        c for c in result["cases"] if c["case_id"] == obj.primary_case_id and c["role"] == "benefit"
    ]
    if len(cases) != 1 or cases[0]["quantity_kind"] != obj.quantity_kind:
        raise ValueError("missing or incompatible objective case")
    field = "weighted_m2_h" if obj.kind == "maximise_shade_under_budget" else "physical_m2_h"
    score = cases[0][field]
    if type(score) not in (int, float) or not math.isfinite(score) or score < 0:
        raise ValueError("invalid objective")
    return float(score)


def search(problem, evaluate, stop=None, exact_limit=0):
    """Deterministic marginal search, single-swap improvement, and finite reference."""
    rules = problem.scenario.input.constraints
    obj = problem.scenario.input.objective
    if type(exact_limit) is not int or not 0 <= exact_limit <= 20:
        raise ValueError("exact_limit must be between 0 and 20")
    candidates = sorted(problem.site.candidate_catalogue, key=lambda c: c.candidate_id)
    pins = tuple(p.model_dump(mode="json") for p in rules.pinned_placements)
    trace = []
    evaluated = 0

    def probe(items):
        nonlocal evaluated
        if stop is not None and stop():
            raise InterruptedError("search stopped")
        admission = _admissible(problem, items, evaluate)
        evaluated += 1
        if admission is None:
            return None
        cost, evaluation = admission
        return Choice(tuple(items), _score(problem, evaluation), cost, evaluation)

    def rank(c):
        if obj.kind == "minimise_cost_for_target":
            met = c.score >= obj.target_gain_m2_h
            return (int(met), -c.cost_pence if met else c.score, c.score if met else -c.cost_pence)
        return (c.score, -c.cost_pence)

    current = probe(pins)
    if current is None:
        raise ValueError("pinned layout fails hard constraints")
    reference = current
    eligible = False
    # A distinct deterministic reference: first feasible additions in candidate order.
    for c in candidates:
        if c.candidate_id in {p["candidate_id"] for p in reference.placements}:
            continue
        q = probe(reference.placements + (_placement(c),))
        if q is not None:
            eligible = True
            if q.score > reference.score:
                reference = q
    while True:
        options = []
        ids = {p["candidate_id"] for p in current.placements}
        for c in candidates:
            if c.candidate_id in ids:
                continue
            q = probe(current.placements + (_placement(c),))
            if q is not None and rank(q) > rank(current):
                options.append(q)
        if not options:
            break
        current = max(options, key=rank)
        trace.append(("add", tuple(p["candidate_id"] for p in current.placements), current.score))
    improved = True
    while improved:
        improved = False
        options = []
        for i, p in enumerate(current.placements):
            if p["pinned"]:
                continue
            reduced = current.placements[:i] + current.placements[i + 1 :]
            q = probe(reduced)
            if q is not None and rank(q) > rank(current):
                options.append(q)
            for c in candidates:
                if c.candidate_id in {x["candidate_id"] for x in reduced}:
                    continue
                q = probe(reduced + (_placement(c),))
                if q is not None and rank(q) > rank(current):
                    options.append(q)
        if options:
            current = max(options, key=rank)
            improved = True
            trace.append(
                ("improve", tuple(p["candidate_id"] for p in current.placements), current.score)
            )
    if rank(reference) > rank(current):
        current = reference
    if exact_limit and len(candidates) <= exact_limit:
        for size in range(len(candidates) + 1):
            for subset in combinations(candidates, size):
                pin_ids = {p["candidate_id"] for p in pins}
                q = probe(
                    pins + tuple(_placement(c) for c in subset if c.candidate_id not in pin_ids)
                )
                if q is not None and rank(q) > rank(current):
                    current = q
    if obj.kind == "minimise_cost_for_target" and current.score < obj.target_gain_m2_h:
        outcome = "no_eligible_candidates" if not eligible else "search_exhausted_without_target"
    else:
        outcome = "feasible_candidate" if current.placements else "feasible_zero_planting"
    return SearchResult(reference, current, outcome, tuple(trace), evaluated)


def relocate(problem, placements, placement_id, alternative_position_enu_m, evaluate):
    """Keep identity/profile/configuration fixed and diagnose the requested position."""
    items = [dict(p) for p in placements]
    indices = [i for i, p in enumerate(items) if p["placement_id"] == placement_id]
    if len(indices) != 1:
        raise ValueError("unresolved placement")
    i = indices[0]
    items[i]["position_enu_m"] = alternative_position_enu_m
    return Comparison(
        tuple(items), check(problem, items, evaluate, diagnostic=True), ("position_enu_m",)
    )
