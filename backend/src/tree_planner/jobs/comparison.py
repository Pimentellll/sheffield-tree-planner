"""Revalidate both admitted comparison graphs on live completion, read and cache."""

from tree_planner.canonical import content_hash
from tree_planner.contracts import ScenarioRef
from tree_planner.contracts.operations import EvaluateLayoutArguments, SearchLayoutsArguments


def changed_fields(left, right, prefix=""):
    if isinstance(left, dict) and isinstance(right, dict):
        return [
            p
            for key in sorted(set(left) | set(right))
            for p in changed_fields(left.get(key), right.get(key), prefix + key + ".")
        ]
    return [] if left == right else [prefix.rstrip(".")]


def validate_comparison(db, result, identity, snapshot, validate):
    context = snapshot(db, "comparison", identity["content_hashes"].get("comparison-context"))
    if (
        context.get("format_version") != "canopy-comparison-context/1"
        or context["arguments"] != identity["arguments"]
    ):
        raise ValueError("Unadmitted comparison context")
    primary = context["base"]
    if primary["scenario"] != identity["scenario"]:
        raise ValueError("Comparison primary changed")
    metadata = result.comparison
    if (
        metadata is None
        or metadata.mode != context["arguments"]["mode"]
        or tuple(
            changed_fields(
                primary["scenario"]["input"], context["alternative"]["scenario"]["input"]
            )
        )
        != metadata.changed_inputs
    ):
        raise ValueError("Comparison metadata differs from admitted inputs")
    admitted = set()
    for label in ("base", "alternative"):
        deps, hashes = context[label], context[label + "_hashes"]
        scenario = deps["scenario"]
        ref = ScenarioRef(**{k: scenario[k] for k in ("scenario_id", "revision", "scope")})
        requested_ref = context["arguments"][
            "base_scenario_ref" if label == "base" else "alternative_scenario_ref"
        ]
        if ref.model_dump(mode="json") != requested_ref:
            raise ValueError("Comparison side reference differs from request")
        admitted.add(ref)
        if content_hash(scenario) != hashes["scenario"]:
            raise ValueError("Comparison scenario hash mismatch")
        entries = tuple(e for e in result.layouts if e.scenario_ref == ref)
        if not entries:
            raise ValueError("Comparison scenario unevaluated")
        for entry in entries:
            rules = scenario["input"]["constraints"]
            cost = sum(
                deps["profiles"][p.profile_id]["cost_pence"] for p in entry.layout.placements
            )
            if cost != entry.cost_pence:
                raise ValueError("Comparison profile cost differs from actual placements")
            records = [
                c
                for c in result.constraints
                if c.scenario_ref == ref and c.layout_id == entry.layout.layout_id
            ]
            if entry.feasibility == "feasible":
                required = {
                    "budget",
                    "candidate and profile",
                    "location and terrain",
                    "regions",
                    "pins",
                    "spacing and conflicts",
                }
                if rules["max_tree_count"] is not None:
                    required.add("count")
                if cost > rules["budget_pence"] or (
                    rules["max_tree_count"] is not None
                    and len(entry.layout.placements) > rules["max_tree_count"]
                ):
                    raise ValueError("Comparison feasible layout exceeds budget/count")
                if not required <= {c.rule for c in records if c.status == "pass"}:
                    raise ValueError("Comparison feasibility lacks independent constraint evidence")
                for limit in rules["winter_limits"]:
                    name = "winter loss:" + (limit["target_id"] or "aggregate")
                    checked = [
                        c
                        for c in records
                        if c.case_id == limit["case_id"] and c.rule == name and c.status == "pass"
                    ]
                    if (
                        len(checked) != 1
                        or checked[0].observed_value is None
                        or checked[0].observed_value > limit["maximum_loss_m2_h"]
                    ):
                        raise ValueError("Comparison winter feasibility lacks passing evidence")
            for survey in rules["survey_requirements"]:
                if not any(c.rule == "survey:" + survey and c.status == "unknown" for c in records):
                    raise ValueError("Comparison survey requirement lost its unknown status")
            for case in scenario["input"]["evaluation_cases"]:
                physical = [
                    m
                    for m in result.metrics
                    if m.scenario_ref == ref
                    and m.layout_id == entry.layout.layout_id
                    and m.case_id == case["case_id"]
                    and m.metric_id == "additional_shade"
                ]
                missing = [
                    m
                    for m in result.missing_metrics
                    if m.scenario_ref == ref
                    and m.layout_id == entry.layout.layout_id
                    and m.case_id == case["case_id"]
                    and m.metric_id == "additional_shade"
                ]
                if not missing and {m.target_id for m in physical} != {None, *case["target_ids"]}:
                    raise ValueError(
                        "Comparison case lacks physical metrics or explicit missing reason"
                    )

        def subset(values):
            return tuple(v for v in values if v.scenario_ref == ref)

        fixed = context["arguments"]["mode"] == "fixed_layout"
        operation = "evaluate_layout" if fixed else "search_layouts"
        arguments = (
            EvaluateLayoutArguments(layout_ref=scenario["input"]["proposed_layout_ref"])
            if fixed
            else SearchLayoutsArguments()
        )
        projected = result.model_copy(
            update=dict(
                input_snapshot_ref=ref,
                layouts=entries,
                metrics=subset(result.metrics),
                missing_metrics=subset(result.missing_metrics),
                constraints=subset(result.constraints),
                source_ids=tuple(s for s in result.source_ids if s in deps["sources"]),
            )
        )
        validate(
            db,
            projected,
            dict(
                scenario=scenario,
                content_hashes=hashes,
                operation=operation,
                arguments=arguments.model_dump(mode="json"),
            ),
        )
    if any(e.scenario_ref not in admitted for e in result.layouts) or any(
        e.scenario_ref not in admitted
        for e in (*result.metrics, *result.constraints, *result.missing_metrics)
    ):
        raise ValueError("Comparison contains unadmitted scenario")
    if set(result.source_ids) != set(context["base"]["sources"]) | set(
        context["alternative"]["sources"]
    ):
        raise ValueError("Comparison contains unadmitted sources")
    refs = {
        label: ScenarioRef(
            **{k: context[label]["scenario"][k] for k in ("scenario_id", "revision", "scope")}
        )
        for label in ("base", "alternative")
    }
    metrics = {m.metric_instance_id: m for m in result.metrics}
    for delta in metadata.deltas:
        if (
            metrics[delta.base_metric_instance_id].scenario_ref != refs["base"]
            or metrics[delta.alternative_metric_instance_id].scenario_ref != refs["alternative"]
        ):
            raise ValueError("Comparison delta side mismatch")
