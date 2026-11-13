"""Model-facing observation views (#68).

Every successful observation here is produced at test time by the real synthetic physical
runtime (real jobs, real Results), built the same way AgentLoop._dispatch builds its
async observation. Several tests drive the unchanged AgentLoop with a scripted (SYNTHETIC)
client, including the citation rule in AUTHORITY. The compare_scenarios observation is
produced through the job API: AgentLoop cannot currently complete compare_scenarios
against this runtime (it submits under the hypothetical scenario, which the runtime
rejects), so that case checks the view's handling of two-scenario Results only, in the
one orientation the runtime produces. Inputs derived from real records for edge cases are
labelled SYNTHETIC inline where they are built (failed Job, superseded Jobs including a
queued one, cached delivery with source_job_id == job_id, progress on a queued Job,
missing metric, relabelled target-row quantity, non-ASCII text, scaled-up search,
aggregation-basis labels) and are passed as NOT validated at delivery. No successful
runtime result is hand-authored and nothing here is model evidence.
"""

from __future__ import annotations

import copy
import json
import threading
import time
import uuid

import pytest

from tree_planner.agents import AgentLoop
from tree_planner.agents.observation_views import (
    AUTHORITY,
    CONVENTIONS,
    JOB_ONLY_LEVEL,
    LEVELS,
    VIEW_SCHEMA,
    ObservationBudgetError,
    ObservationViewError,
    compact_async_observation,
    observation_bytes,
    view_sizes,
)
from tree_planner.api.service import AgentDispatcher
from tree_planner.contracts import Job, JobRequest, Result, ScenarioInput, Selection
from tree_planner.evaluators.physical_runtime import create_physical_runtime

BIG = 10_000_000
REAL = ("evaluate", "search", "compare", "compare_scenarios")


# --------------------------------------------------------------------------- real inputs


def _runtime(path):
    runtime = create_physical_runtime(path, start_worker=False, winter=True)
    return runtime, runtime.app.state.service


def _submit(runtime, service, operation, arguments):
    request = JobRequest.model_validate(
        {
            "request_id": f"obs-view-{uuid.uuid4().hex}",
            "scenario_ref": runtime.scenario_ref.model_dump(mode="json"),
            "operation": operation,
            "arguments": arguments,
        }
    )
    return service.submit(request)


def _completed(runtime, service, operation, arguments):
    """Run one real job synchronously; return it as AgentLoop's async observation."""
    job = _submit(runtime, service, operation, arguments)
    runtime.app.state.run_one()
    job = service.jobs.get_job(job.job_id)
    assert job.status == "completed", job
    result = service.jobs.read_run(job.run_id)
    # Same construction as AgentLoop._dispatch for a delivered async result.
    return {"job": job.model_dump(mode="json"), "result": result.model_dump(mode="json")}


def _context(service, runtime):
    scenario = service.scenarios.get_scenario(runtime.scenario_ref)
    inp = scenario.input
    layout_ref = inp.proposed_layout_ref.model_dump(mode="json")
    layout = service.scenarios.get_layout(
        inp.proposed_layout_ref.layout_id, inp.proposed_layout_ref.revision
    )
    site = service.scenarios.get_site(inp.site_id, inp.scene_revision, inp.semantic_revision)
    return layout_ref, layout.placements[0], site.candidate_catalogue


@pytest.fixture(scope="module")
def real(tmp_path_factory):
    runtime, service = _runtime(tmp_path_factory.mktemp("obs-views") / "runtime")
    layout_ref, placement, catalogue = _context(service, runtime)
    other = next(
        c
        for c in catalogue
        if tuple(c.position_enu_m) != tuple(placement.position_enu_m)
        and c.plantability_status != "excluded"
    )
    move = {"layout_ref": layout_ref, "placement_id": placement.placement_id}
    observations = {
        "evaluate": _completed(runtime, service, "evaluate_layout", {"layout_ref": layout_ref}),
        "search": _completed(runtime, service, "search_layouts", {}),
        "compare": _completed(
            runtime,
            service,
            "compare_locations",
            {**move, "alternative_position_enu_m": list(other.position_enu_m)},
        ),
        "compare_same_position": _completed(
            runtime,
            service,
            "compare_locations",
            {**move, "alternative_position_enu_m": list(placement.position_enu_m)},
        ),
    }
    # A real two-scenario comparison, prepared as test_physical_runtime.py does.
    base = service.scenarios.get_scenario(runtime.scenario_ref)
    data = copy.deepcopy(base.input.model_dump(mode="json"))
    data["constraints"]["budget_pence"] = 0
    alternative = service.scenarios.prepare_scenario(
        ScenarioInput.model_validate(data), base_ref=runtime.scenario_ref
    )
    observations["compare_scenarios"] = _completed(
        runtime,
        service,
        "compare_scenarios",
        {
            "base_scenario_ref": runtime.scenario_ref.model_dump(mode="json"),
            "alternative_scenario_ref": {
                "scenario_id": alternative.scenario_id,
                "revision": alternative.revision,
                "scope": alternative.scope,
            },
            "layout_refs": [layout_ref],
            "mode": "fixed_layout",
        },
    )
    return observations


def view(observation, budget=BIG, validated=None):
    if validated is None:
        validated = "result" in observation
    return compact_async_observation(
        observation, budget_bytes=budget, result_validated_at_delivery=validated
    )


def rows(table):
    return [dict(zip(table["columns"], row)) for row in table["rows"]]


def assert_omissions_reference_the_record(v, observation):
    holders = [{"job_id": observation["job"]["job_id"]}]
    if "result" in observation:
        holders.append({"run_id": observation["result"]["run_id"]})
    for entry in v["omitted"]:
        assert entry["authoritative"] in holders, entry
        assert type(entry["count"]) is int and entry["count"] > 0, entry
        assert entry["unit"] in {"records", "field_values"}, entry


# --------------------------------------------------------------------------- SYNTHETIC derivations


def synthetic_scaled_search(observation, extra_layouts):
    """SYNTHETIC: add copies of the real non-selected search layout under new IDs.

    Values are copied from the real Result, never invented; the outcome is re-validated
    against the Result contract so the view sees a contract-valid input.
    """
    data = copy.deepcopy(observation)
    result = data["result"]
    source = next(e for e in result["layouts"] if not e["selected"])
    source_id = source["layout"]["layout_id"]
    metrics = [m for m in result["metrics"] if m["layout_id"] == source_id]
    constraints = [c for c in result["constraints"] if c["layout_id"] == source_id]
    for i in range(extra_layouts):
        new_id = f"{source_id}-synthetic-copy-{i}"
        entry = copy.deepcopy(source)
        entry["layout"]["layout_id"] = new_id
        result["layouts"].append(entry)
        for k, metric in enumerate(metrics):
            clone = dict(metric, layout_id=new_id)
            clone["metric_instance_id"] = f"{result['run_id']}:synthetic-{i}-{k}"
            result["metrics"].append(clone)
        result["constraints"].extend(dict(c, layout_id=new_id) for c in constraints)
    Result.model_validate(result)
    return data


def synthetic_job_state(observation, **changes):
    """SYNTHETIC: a real Job dump with lifecycle fields changed, validated as a Job."""
    job = dict(copy.deepcopy(observation["job"]), **changes)
    Job.model_validate(job)
    return {"job": job}


# --------------------------------------------------------------------------- AgentLoop glue


class PumpingDispatcher:
    """Test glue: the in-process task-pinned dispatcher plus a synchronous job pump."""

    def __init__(self, runtime, service):
        self.runtime = runtime
        self.inner = AgentDispatcher(service, accepted_ref=runtime.scenario_ref)

    def dispatch(self, envelope):
        value = self.inner.dispatch(envelope)
        self.runtime.app.state.run_one()
        return value

    def poll(self, job_id):
        return self.inner.poll(job_id)

    def result(self, run_id):
        return self.inner.result(run_id)

    def selection(self, ref, slot):
        return self.inner.selection(ref, slot)


class StepClient:
    """SYNTHETIC protocol fixture: scripted tool calls, then a scripted final answer.

    ``final_ids(messages)`` chooses evidence_ids from the loop's own messages."""

    def __init__(self, steps, final_ids):
        self.steps, self.final_ids = steps, final_ids

    def complete(self, messages, tools, *, timeout_s=None):
        done = sum(m["role"] == "tool" for m in messages)
        if done < len(self.steps):
            name, arguments = self.steps[done]
            call = {
                "id": f"call-{done + 1}",
                "type": "function",
                "function": {"name": name, "arguments": json.dumps(arguments)},
            }
            return {"role": "assistant", "content": None, "tool_calls": [call]}
        final = {"narrative": "synthetic", "evidence_ids": self.final_ids(messages)}
        return {"role": "assistant", "content": json.dumps(final)}


def _run_loop(runtime, service, steps, final_ids, operations):
    accepted = service.scenarios.get_scenario(runtime.scenario_ref)
    loop = AgentLoop(
        StepClient(steps, final_ids),
        PumpingDispatcher(runtime, service),
        accepted,
        set(operations),
        deadline=time.monotonic() + 120,
        stop=threading.Event(),
        poll_interval_s=0.01,
    )
    return loop, loop.run("Synthetic scripted task.")


def tool_observations(messages):
    return [json.loads(m["content"]) for m in messages if m["role"] == "tool"]


def cite_by_authority(messages, current_ref):
    """Apply AUTHORITY literally to compacted views of the loop's own tool messages: per
    view_slot the latest view (highest selection_seq) in the current scenario; its job_id,
    plus its run_id when a result is shown."""
    latest = {}
    for observation in tool_observations(messages):
        if "job" not in observation:
            continue
        v = view(observation)
        assert v["authority"] == AUTHORITY
        job = v["job"]
        if job["scenario_ref"] != current_ref:
            continue
        slot = job["view_slot"]
        if slot not in latest or job["selection_seq"] > latest[slot]["job"]["selection_seq"]:
            latest[slot] = v
    ids = []
    for v in latest.values():
        ids.append(v["job"]["job_id"])
        if "result" in v:
            ids.append(v["result"]["run_id"])
    return ids


def _reselection_steps(service, runtime):
    """evaluate, then two compare_locations in the same 'comparison' slot."""
    layout_ref, placement, catalogue = _context(service, runtime)
    other = next(
        c
        for c in catalogue
        if tuple(c.position_enu_m) != tuple(placement.position_enu_m)
        and c.plantability_status != "excluded"
    )
    move = {"layout_ref": layout_ref, "placement_id": placement.placement_id}
    return [
        ("evaluate_layout", {"layout_ref": layout_ref}),
        ("compare_locations", {**move, "alternative_position_enu_m": list(other.position_enu_m)}),
        (
            "compare_locations",
            {**move, "alternative_position_enu_m": list(placement.position_enu_m)},
        ),
    ]


# --------------------------------------------------------------------------- shape and content


def test_view_consumes_the_actual_agent_loop_observation(tmp_path):
    """Drive the unchanged AgentLoop and compact the exact tool message it sent."""
    runtime, service = _runtime(tmp_path / "runtime")
    layout_ref, _, _ = _context(service, runtime)
    accepted = service.scenarios.get_scenario(runtime.scenario_ref)

    class ScriptedClient:
        """SYNTHETIC protocol fixture: scripted assistant turns, not inference."""

        def complete(self, messages, tools, *, timeout_s=None):
            tool_messages = [m for m in messages if m["role"] == "tool"]
            if not tool_messages:
                arguments = json.dumps({"layout_ref": layout_ref})
                return {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "type": "function",
                            "function": {"name": "evaluate_layout", "arguments": arguments},
                        }
                    ],
                }
            run_id = json.loads(tool_messages[-1]["content"])["result"]["run_id"]
            final = {"narrative": "synthetic", "evidence_ids": [run_id]}
            return {"role": "assistant", "content": json.dumps(final)}

    loop = AgentLoop(
        ScriptedClient(),
        PumpingDispatcher(runtime, service),
        accepted,
        {"evaluate_layout"},
        deadline=time.monotonic() + 60,
        stop=threading.Event(),
        poll_interval_s=0.01,
    )
    outcome = loop.run("Evaluate the current proposal.")
    assert outcome.status == "completed", outcome
    tool_message = next(m for m in loop.messages if m["role"] == "tool")
    observation = json.loads(tool_message["content"])
    assert set(observation) == {"job", "result"}
    assert observation["result"] == loop.results[0].model_dump(mode="json")
    assert len(tool_message["content"].encode("utf-8")) == observation_bytes(observation)

    compact = view(observation)
    assert compact["view"] == VIEW_SCHEMA and compact["level"] == "full"
    assert compact["result"]["run_id"] == loop.results[0].run_id
    assert compact["result"]["currentness"] == "validated_at_delivery"
    assert loop.results[0].model_dump(mode="json") == observation["result"]


# --------------------------------------------------------------------------- citation rule


def test_authority_citations_are_accepted_after_a_same_slot_reselection(tmp_path):
    """The IDs AUTHORITY tells the model to cite are exactly ones the unchanged AgentLoop
    accepts, including after a second job in the same view_slot made the first run stale."""
    runtime, service = _runtime(tmp_path / "runtime")
    current = runtime.scenario_ref.model_dump(mode="json")
    loop, outcome = _run_loop(
        runtime,
        service,
        _reselection_steps(service, runtime),
        lambda messages: cite_by_authority(messages, current),
        {"evaluate_layout", "compare_locations"},
    )
    assert outcome.status == "completed", outcome
    evaluate, first, second = tool_observations(loop.messages)
    first_job, second_job = view(first)["job"], view(second)["job"]
    assert first_job["view_slot"] == second_job["view_slot"] == "comparison"
    assert second_job["selection_seq"] > first_job["selection_seq"]
    # The replaced comparison still looks current in its own view: superseded_by_revision
    # cannot flag a same-slot reselection, which is why AUTHORITY uses selection_seq.
    assert first_job["superseded_by_revision"] is None and first_job["result_attached"] is True
    assert list(outcome.evidence_ids) == [
        evaluate["job"]["job_id"],
        evaluate["result"]["run_id"],
        second["job"]["job_id"],
        second["result"]["run_id"],
    ]
    # The protocol (C1) and the live test score the current run_id; it is cited.
    assert {r.run_id for r in outcome.results} == {
        evaluate["result"]["run_id"],
        second["result"]["run_id"],
    } <= set(outcome.evidence_ids)


@pytest.mark.parametrize(
    "choose,status",
    [
        (lambda e, f, s: [f["result"]["run_id"]], "failed"),
        (lambda e, f, s: [s["job"]["job_id"], s["result"]["run_id"], f["result"]["run_id"]], "failed"),
        (lambda e, f, s: [], "failed"),
        # The loop also accepts a replaced job_id; AUTHORITY leaves it out because the
        # protocol scores the current run_id.
        (lambda e, f, s: [f["job"]["job_id"]], "completed"),
    ],
    ids=["stale-run-id", "current-plus-stale-run-id", "nothing-while-evidence-exists", "replaced-job-id"],
)
def test_citations_outside_authority_show_why_the_rule_is_needed(tmp_path, choose, status):
    runtime, service = _runtime(tmp_path / "runtime")
    loop, outcome = _run_loop(
        runtime,
        service,
        _reselection_steps(service, runtime),
        lambda messages: choose(*tool_observations(messages)),
        {"evaluate_layout", "compare_locations"},
    )
    assert outcome.status == status, outcome
    if status == "failed":
        assert outcome.reason == "ProtocolError: unknown or malformed evidence IDs"


def test_a_reselection_outside_the_loop_is_invisible_to_the_view(tmp_path):
    """Residual risk, recorded: another client submitting the same slot during the session
    makes the in-view run_id stale, and nothing in the model's view can show it."""
    runtime, service = _runtime(tmp_path / "runtime")
    layout_ref, _, _ = _context(service, runtime)
    current = runtime.scenario_ref.model_dump(mode="json")
    outside = {}

    def final_ids(messages):
        chosen = cite_by_authority(messages, current)
        # SYNTHETIC: a second evaluate_layout submitted outside the loop before it answers.
        outside["job"] = _submit(runtime, service, "evaluate_layout", {"layout_ref": layout_ref})
        return chosen

    loop, outcome = _run_loop(
        runtime,
        service,
        [("evaluate_layout", {"layout_ref": layout_ref})],
        final_ids,
        {"evaluate_layout"},
    )
    selection = Selection.model_validate(
        AgentDispatcher(service, accepted_ref=runtime.scenario_ref).selection(
            runtime.scenario_ref, "evaluation"
        )
    )
    assert selection.accepted_job_id == outside["job"].job_id
    (evaluate,) = tool_observations(loop.messages)
    assert outcome.evidence_ids == () and outcome.status == "failed", outcome
    assert outcome.reason == "ProtocolError: unknown or malformed evidence IDs"
    assert view(evaluate)["job"]["superseded_by_revision"] is None


@pytest.mark.parametrize("name", REAL)
def test_full_view_keeps_every_value_and_identity(real, name):
    observation = real[name]
    full_job, full_result = observation["job"], observation["result"]
    v = view(observation)
    job, result = v["job"], v["result"]
    assert v["level"] == "full"
    assert (job["job_id"], job["status"], job["result_attached"]) == (
        full_job["job_id"],
        "completed",
        True,
    )
    assert "state" not in job
    assert job["scenario_ref"] == full_result["input_snapshot_ref"] == result["scenario_ref"]
    assert job["input_fingerprint"] == result["input_fingerprint"] == full_job["input_fingerprint"]
    for key in ("run_id", "source_job_id", "operation", "analytical_outcome", "arguments"):
        assert result[key] == full_result[key], key
    assert "execution_mode" not in result  # current mode lives on job.delivery only
    assert job["delivery"]["execution_mode"] == full_job["delivery"]["execution_mode"]
    source_mode = full_result["provenance"]["execution_mode"]
    assert result["provenance"]["source_execution_mode"] == source_mode
    assert result["source_ids"] == full_result["source_ids"]
    assert result["limitations"] == full_result["limitations"]
    assert result["assumptions"] == full_result["assumptions"]
    assert result["provenance"]["source_hashes"] == full_result["provenance"]["source_hashes"]
    for k in ("tool_version", "evaluator_version", "search_version", "solar_version", "seed"):
        assert result["provenance"][k] == full_result["provenance"][k], k
    for k in ("view_slot", "selection_seq", "run_id", "cancel_requested", "superseded_by_revision"):
        assert job[k] == full_job[k], k
    assert job["delivery"]["source_job_id"] == full_job["delivery"]["source_job_id"]
    # Result scenario fields repeat result.scenario_ref; the omission says so.
    repeat = {o["path"]: o for o in v["omitted"]}[
        "result.scenario_id, result.scenario_revision, result.scope"
    ]
    assert (repeat["count"], repeat["unit"]) == (3, "field_values")
    assert (full_result["scenario_id"], full_result["scenario_revision"], full_result["scope"]) == (
        result["scenario_ref"]["scenario_id"],
        result["scenario_ref"]["revision"],
        result["scenario_ref"]["scope"],
    )

    default = full_result["input_snapshot_ref"]

    def key(scenario_ref, layout_id, metric_id, case_id, target_id, horizon):
        return (scenario_ref["scenario_id"], scenario_ref["revision"], layout_id, metric_id,
                case_id, target_id, horizon)

    shown = {
        key(r.get("scenario_ref?") or default, r["layout_id"], r["metric_id"], r["case_id"],
            r["target_id"], r["horizon_years"]): r
        for r in rows(result["metrics"])
    }
    assert len(shown) == len(result["metrics"]["rows"]) == len(full_result["metrics"])
    for m in full_result["metrics"]:
        r = shown[key(m["scenario_ref"], m["layout_id"], m["metric_id"], m["case_id"],
                      m["target_id"], m["horizon_years"])]
        for field in ("value", "unit", "quantity_kind", "weighting", "area_basis",
                      "aggregation_basis"):
            assert r[field] == m[field], field
    assert len(result["constraints"]["rows"]) == len(full_result["constraints"])

    for shown_layout, full_layout in zip(result["layouts"], full_result["layouts"], strict=True):
        assert shown_layout["layout_id"] == full_layout["layout"]["layout_id"]
        assert shown_layout["kind"] == full_layout["layout"]["kind"]
        assert type(shown_layout["cost_pence"]) is int
        assert shown_layout["cost_pence"] == full_layout["cost_pence"]
        for field in ("role", "selected", "feasibility", "reasons", "tree_count"):
            assert shown_layout[field] == full_layout[field], field
        assert len(shown_layout["placements"]) == len(full_layout["layout"]["placements"])
        assert shown_layout.get("scenario_ref", default) == full_layout["scenario_ref"]
    assert_omissions_reference_the_record(v, observation)


@pytest.mark.parametrize("name", ["compare", "compare_scenarios"])
def test_comparison_deltas_resolve_to_the_recorded_metrics(real, name):
    full = real[name]["result"]
    default = full["input_snapshot_ref"]
    by_instance = {m["metric_instance_id"]: m for m in full["metrics"]}
    deltas = rows(view(real[name])["result"]["comparison"]["deltas"])
    assert len(deltas) == len(full["comparison"]["deltas"]) > 0
    for shown, recorded in zip(deltas, full["comparison"]["deltas"], strict=True):
        a = by_instance[recorded["base_metric_instance_id"]]
        b = by_instance[recorded["alternative_metric_instance_id"]]
        assert shown["delta"] == recorded["value"] and shown["unit"] == recorded["unit"]
        assert (shown["base_value"], shown["alternative_value"]) == (a["value"], b["value"])
        assert (shown["base_layout_id"], shown["alternative_layout_id"]) == (
            a["layout_id"],
            b["layout_id"],
        )
        for field in ("quantity_kind", "weighting", "area_basis"):
            assert shown[field] == a[field] == b[field], field
        assert shown["base_aggregation_basis"] == a["aggregation_basis"]
        assert shown["alternative_aggregation_basis"] == b["aggregation_basis"]
        assert (shown["base_scenario_ref"] or default) == a["scenario_ref"]
        assert (shown["alternative_scenario_ref"] or default) == b["scenario_ref"]


@pytest.mark.parametrize("name", ["compare", "compare_scenarios"])
def test_delta_aggregation_basis_is_shown_per_side(real, name):
    data = copy.deepcopy(real[name])
    result = data["result"]
    # SYNTHETIC: distinct aggregation_basis labels on the two sides of one real delta (the
    # runtime leaves aggregation_basis null, which would make this check vacuous).
    by_id = {m["metric_instance_id"]: m for m in result["metrics"]}
    first = result["comparison"]["deltas"][0]
    by_id[first["base_metric_instance_id"]]["aggregation_basis"] = "synthetic-basis-base"
    by_id[first["alternative_metric_instance_id"]]["aggregation_basis"] = "synthetic-basis-alt"
    Result.model_validate(result)
    shown = rows(view(data, validated=False)["result"]["comparison"]["deltas"])[0]
    assert (shown["base_aggregation_basis"], shown["alternative_aggregation_basis"]) == (
        "synthetic-basis-base",
        "synthetic-basis-alt",
    )


def test_two_scenario_comparison_keeps_each_side_scenario_identity(real):
    observation = real["compare_scenarios"]
    full = observation["result"]
    default = full["input_snapshot_ref"]
    others = {
        json.dumps(e["scenario_ref"], sort_keys=True)
        for e in full["layouts"]
        if e["scenario_ref"] != default
    }
    assert others  # the real result spans the accepted and the hypothetical scenario
    for level in LEVELS:
        v = view(observation, view_sizes(observation, result_validated_at_delivery=True)[level])
        assert v["level"] == level
        result = v["result"]
        deltas = rows(result["comparison"]["deltas"])
        assert all(d["alternative_scenario_ref"] is not None for d in deltas)
        assert all(d["base_scenario_ref"] is None for d in deltas)
        tagged = [r for r in rows(result["metrics"]) if r.get("scenario_ref?")]
        assert all(json.dumps(r["scenario_ref?"], sort_keys=True) in others for r in tagged)
        assert {json.dumps(x.get("scenario_ref", default), sort_keys=True) for x in result["layouts"]} == {
            json.dumps(e["scenario_ref"], sort_keys=True) for e in full["layouts"]
        }


def test_valid_zero_is_shown_as_zero_not_omitted(real):
    observation = real["compare_same_position"]
    recorded = [d["value"] for d in observation["result"]["comparison"]["deltas"]]
    assert 0.0 in recorded  # real relocation onto the same position
    essential = view_sizes(observation, result_validated_at_delivery=True)["essential"]
    for budget in (BIG, essential):
        shown = rows(view(observation, budget)["result"]["comparison"]["deltas"])
        assert [d["delta"] for d in shown] == recorded


def test_missing_metric_is_reported_as_missing_not_zero(real):
    data = copy.deepcopy(real["evaluate"])
    result = data["result"]
    # SYNTHETIC: drop one real aggregate weighted metric and declare it missing.
    dropped = next(
        m
        for m in result["metrics"]
        if m["metric_id"] == "weighted_shade_utility" and m["target_id"] is None
    )
    result["metrics"].remove(dropped)
    result["missing_metrics"].append(
        {
            "scenario_ref": dropped["scenario_ref"],
            "layout_id": dropped["layout_id"],
            "case_id": dropped["case_id"],
            "metric_id": dropped["metric_id"],
            "reason": "synthetic test: not computed",
        }
    )
    Result.model_validate(result)
    v = view(data, validated=False)["result"]
    assert v["currentness"] == "not_validated_by_caller"
    assert {
        "layout_id": dropped["layout_id"],
        "case_id": dropped["case_id"],
        "metric_id": dropped["metric_id"],
        "reason": "synthetic test: not computed",
    } in v["missing_metrics"]
    assert not any(
        (r["layout_id"], r["metric_id"], r["case_id"], r["target_id"])
        == (dropped["layout_id"], dropped["metric_id"], dropped["case_id"], None)
        for r in rows(v["metrics"])
    )


def test_target_rows_are_kept_when_no_aggregate_of_the_same_quantity_is_shown(real):
    data = copy.deepcopy(real["evaluate"])
    result = data["result"]
    # SYNTHETIC: relabel one aggregate additional_shade row as blocking_equivalent, so its
    # geometric target rows no longer have a matching aggregate quantity.
    aggregate = next(
        m
        for m in result["metrics"]
        if m["metric_id"] == "additional_shade"
        and m["target_id"] is None
        and m["quantity_kind"] == "geometric"
        and any(
            t["metric_id"] == "additional_shade"
            and t["target_id"] is not None
            and (t["layout_id"], t["case_id"], t["horizon_years"])
            == (m["layout_id"], m["case_id"], m["horizon_years"])
            for t in result["metrics"]
        )
    )
    aggregate["quantity_kind"] = "blocking_equivalent"
    Result.model_validate(result)
    sizes = view_sizes(data, result_validated_at_delivery=False)
    essential = view(data, sizes["essential"], validated=False)
    assert essential["level"] == "essential"
    kept_targets = [
        r
        for r in rows(essential["result"]["metrics"])
        if r["metric_id"] == "additional_shade"
        and r["target_id"] is not None
        and r["quantity_kind"] == "geometric"
        and (r["layout_id"], r["case_id"], r["horizon_years"])
        == (aggregate["layout_id"], aggregate["case_id"], aggregate["horizon_years"])
    ]
    assert kept_targets


# --------------------------------------------------------------------------- budget levels


def test_large_search_degrades_level_by_level_with_explicit_omissions(real):
    data = synthetic_scaled_search(real["search"], extra_layouts=40)
    sizes = view_sizes(data, result_validated_at_delivery=False)
    assert sizes["observation"] > sizes["full"] > sizes["reduced"] > sizes["essential"]

    reduced = view(data, sizes["reduced"], validated=False)
    assert reduced["level"] == "reduced" and observation_bytes(reduced) <= sizes["reduced"]
    assert reduced["result"]["constraints"]["passed_not_listed_by_layout"]
    assert "assumptions" not in reduced["result"]
    assert_omissions_reference_the_record(reduced, data)

    essential = view(data, sizes["essential"], validated=False)
    assert essential["level"] == "essential"
    assert observation_bytes(essential) == sizes["essential"]
    assert_omissions_reference_the_record(essential, data)
    result, full = essential["result"], data["result"]
    selected = {e["layout"]["layout_id"] for e in full["layouts"] if e["selected"]}
    assert selected
    for layout in result["layouts"]:
        assert ("placements" in layout) == (layout["layout_id"] in selected)
    assert len(result["layouts"]) == len(full["layouts"])  # every candidate still listed
    assert {r["layout_id"] for r in rows(result["metrics"])} <= selected
    non_focus = sum(m["layout_id"] not in selected for m in full["metrics"])
    omitted = {o["path"]: o for o in essential["omitted"]}
    assert omitted["result.metrics (layouts not in focus)"]["count"] == non_focus
    assert omitted["result.metrics[].metric_instance_id (shown rows)"]["count"] == len(
        result["metrics"]["rows"]
    )
    shown_non_pass = [r for r in rows(result["constraints"]) if r["status"] != "pass"]
    assert len(shown_non_pass) == sum(c["status"] != "pass" for c in full["constraints"])
    assert result["constraints"]["status_counts"] == {
        s: sum(c["status"] == s for c in full["constraints"]) for s in ("pass", "fail", "unknown")
    }
    assert result["analytical_outcome"] == full["analytical_outcome"]
    assert [x["cost_pence"] for x in result["layouts"]] == [e["cost_pence"] for e in full["layouts"]]

    with pytest.raises(ObservationBudgetError) as raised:
        view(data, sizes["essential"] - 1, validated=False)
    assert raised.value.required_bytes == sizes["essential"]
    assert raised.value.budget_bytes == sizes["essential"] - 1


def test_impossibly_small_budget_refuses_explicitly(real):
    for name in REAL:
        with pytest.raises(ObservationBudgetError) as raised:
            view(real[name], 64)
        sizes = view_sizes(real[name], result_validated_at_delivery=True)
        assert raised.value.required_bytes == min(sizes[level] for level in LEVELS)


def test_every_view_is_whole_finite_json_within_budget(real):
    for name in REAL:
        sizes = view_sizes(real[name], result_validated_at_delivery=True)
        for level in LEVELS:
            v = view(real[name], sizes[level])
            assert v["level"] == level, (name, level)
            text = json.dumps(v, ensure_ascii=False, allow_nan=False)
            assert json.loads(text) == v
            assert len(text.encode("utf-8")) == observation_bytes(v) <= sizes[level]
            assert_omissions_reference_the_record(v, real[name])


def test_byte_accounting_is_utf8_not_characters(real):
    data = copy.deepcopy(real["evaluate"])
    # SYNTHETIC: a non-ASCII limitation string added to a real Result.
    data["result"]["limitations"].append("Synthetic test note: ±0.5 °C is not modelled — ünïcode")
    Result.model_validate(data["result"])
    v = view(data, validated=False)
    text = json.dumps(v, ensure_ascii=False, allow_nan=False)
    assert observation_bytes(v) == len(text.encode("utf-8")) > len(text)
    assert "±0.5 °C" in v["result"]["limitations"][-1]
    exact = observation_bytes(v)
    assert view(data, exact, validated=False)["level"] == "full"
    assert view(data, exact - 1, validated=False)["level"] != "full"


def test_reports_real_byte_sizes(real, capsys):
    report = {name: view_sizes(real[name], result_validated_at_delivery=True) for name in REAL}
    for name, sizes in report.items():
        assert sizes["full"] < sizes["observation"], name
        assert sizes["essential"] < sizes["reduced"] < sizes["full"], name
    with capsys.disabled():
        print("\nobservation view UTF-8 bytes (real synthetic-runtime observations):")
        for name, sizes in report.items():
            print(f"  {name:17} " + "  ".join(f"{k}={v}" for k, v in sizes.items()))


# --------------------------------------------------------------------------- job states


def test_pending_and_cancelled_jobs_are_reported_without_results(tmp_path):
    runtime, service = _runtime(tmp_path / "runtime")
    layout_ref, _, _ = _context(service, runtime)
    queued = _submit(runtime, service, "evaluate_layout", {"layout_ref": layout_ref})
    pending_observation = {"job": queued.model_dump(mode="json")}
    pending = view(pending_observation)
    assert pending["level"] == JOB_ONLY_LEVEL
    assert pending["job"]["status"] == queued.status and pending["job"]["run_id"] is None
    assert pending["job"]["result_attached"] is False
    assert "result" not in pending
    assert_omissions_reference_the_record(pending, pending_observation)

    service.jobs.cancel(queued.job_id)
    cancelled_job = service.jobs.get_job(queued.job_id)
    assert cancelled_job.status == "cancelled"
    cancelled = view({"job": cancelled_job.model_dump(mode="json")})
    assert cancelled["job"]["status"] == "cancelled" and cancelled["job"]["cancel_requested"]
    assert cancelled["job"]["error"]["code"] == "CANCELLED"
    assert cancelled["job"]["run_id"] is None and cancelled["job"]["result_attached"] is False


def test_job_only_views_have_one_level_and_refuse_with_their_size(real):
    observation = {"job": real["evaluate"]["job"]}
    sizes = view_sizes(observation, result_validated_at_delivery=False)
    assert set(sizes) == {"observation", JOB_ONLY_LEVEL}
    # Documented: a Job-only view can exceed the raw Job dump (authority + omission list).
    assert sizes[JOB_ONLY_LEVEL] < 2000
    with pytest.raises(ObservationBudgetError) as raised:
        view(observation, sizes[JOB_ONLY_LEVEL] - 1)
    assert raised.value.required_bytes == sizes[JOB_ONLY_LEVEL]


def test_failed_and_superseded_jobs_keep_their_status(real, tmp_path):
    runtime, service = _runtime(tmp_path / "runtime")
    layout_ref, _, _ = _context(service, runtime)
    job = _submit(runtime, service, "evaluate_layout", {"layout_ref": layout_ref})
    queued = {"job": job.model_dump(mode="json")}
    # SYNTHETIC: a real queued Job dump relabelled as failed.
    failed = synthetic_job_state(
        queued,
        status="failed",
        finished_at_utc=queued["job"]["created_at_utc"],
        error={
            "code": "NUMERICAL_FAILURE",
            "message": "synthetic failure for the view test",
            "retryable": False,
            "field_errors": [],
            "details": {"stage": "synthetic"},
        },
    )
    shown = view(failed)["job"]
    assert shown["status"] == "failed" and shown["error"]["code"] == "NUMERICAL_FAILURE"
    assert shown["error"]["retryable"] is False and shown["run_id"] is None
    assert shown["error"]["details"] == {"stage": "synthetic"}
    assert shown["result_attached"] is False and "state" not in shown

    revision = real["evaluate"]["job"]["scenario_revision"] + 1
    # SYNTHETIC: a real completed Job dump marked superseded by a later revision.
    superseded = synthetic_job_state(real["evaluate"], superseded_by_revision=revision)
    shown = view(superseded)["job"]
    # Supersession is an orthogonal marker (CONTRACTS, BUILD D04), never a state.
    assert shown["status"] == "completed" and shown["result_attached"] is False
    assert shown["superseded_by_revision"] == revision and "state" not in shown

    # JobStore.activate marks queued/running jobs superseded too; the view keeps the
    # contract status unchanged and shows the marker beside it.
    # SYNTHETIC: a real queued Job dump marked superseded.
    queued_superseded = synthetic_job_state(queued, superseded_by_revision=revision)
    shown = view(queued_superseded)["job"]
    assert shown["status"] == job.status and shown["superseded_by_revision"] == revision
    assert shown["result_attached"] is False and "state" not in shown

    # The citation rule restates AgentLoop's accepted IDs (tested through AgentLoop above).
    authority = view(superseded)["authority"]
    for phrase in ("job.view_slot", "job.selection_seq", "job.scenario_ref",
                   "prepare_scenario", "job.job_id", "result.run_id", "evidence_ids"):
        assert phrase in authority, phrase

    # The loop never attaches a Result to a superseded Job; such input is refused.
    with_result = {"job": superseded["job"], "result": real["evaluate"]["result"]}
    for validated in (True, False):
        with pytest.raises(ObservationViewError):
            view(with_result, validated=validated)


def test_a_cached_delivery_never_looks_live(real):
    data = copy.deepcopy(real["evaluate"])
    # SYNTHETIC: the same real Job/Result, delivered from cache instead of live.
    data["job"]["delivery"]["execution_mode"] = "cached"
    Job.model_validate(data["job"])
    v = view(data, validated=False)
    assert v["job"]["delivery"]["execution_mode"] == "cached"
    recorded = real["evaluate"]["result"]["provenance"]["execution_mode"]
    assert v["result"]["provenance"]["source_execution_mode"] == recorded
    assert "execution_mode" not in v["result"]
    # The model-facing conventions say which field carries the current delivery mode.
    assert "job.delivery.execution_mode" in v["conventions"] == CONVENTIONS


def test_job_progress_is_shown_as_recorded(tmp_path):
    runtime, service = _runtime(tmp_path / "runtime")
    layout_ref, _, _ = _context(service, runtime)
    job = _submit(runtime, service, "evaluate_layout", {"layout_ref": layout_ref})
    progress = {"completed": 2, "total": 5, "phase": "synthetic-phase", "unit": "bins"}
    # SYNTHETIC: progress values on a real queued Job.
    observation = synthetic_job_state({"job": job.model_dump(mode="json")}, progress=progress)
    assert view(observation)["job"]["progress"] == progress


def test_currentness_is_reported_as_supplied_and_never_invented(real):
    assert view(real["evaluate"])["result"]["currentness"] == "validated_at_delivery"
    unvalidated = view(real["evaluate"], validated=False)["result"]["currentness"]
    assert unvalidated == "not_validated_by_caller"
    with pytest.raises(ObservationViewError):
        view({"job": real["evaluate"]["job"]}, validated=True)


# --------------------------------------------------------------------------- safety


def test_deterministic_and_input_is_never_modified(real):
    for name in REAL:
        snapshot = copy.deepcopy(real[name])
        sizes = view_sizes(real[name], result_validated_at_delivery=True)
        for level in LEVELS:
            first = json.dumps(view(real[name], sizes[level]), ensure_ascii=False)
            second = json.dumps(view(real[name], sizes[level]), ensure_ascii=False)
            assert first == second
        assert real[name] == snapshot
        assert Result.model_validate(real[name]["result"]) == Result.model_validate(
            snapshot["result"]
        )


def test_unknown_or_inconsistent_shapes_fail_explicitly(real):
    evaluate, search = real["evaluate"], real["search"]
    nan_result = copy.deepcopy(evaluate)
    nan_result["result"]["metrics"][0]["value"] = float("nan")
    bad_status = copy.deepcopy(evaluate)
    bad_status["job"]["status"] = "done"
    queued_with_result = {
        "job": dict(
            evaluate["job"],
            status="queued",
            run_id=None,
            delivery=None,
            started_at_utc=None,
            finished_at_utc=None,
        ),
        "result": evaluate["result"],
    }
    for observation in (
        [],
        {},
        {"result": evaluate["result"]},
        {**evaluate, "extra": 1},
        {"job": search["job"], "result": evaluate["result"]},
        queued_with_result,
        bad_status,
        nan_result,
        {"job": "not a job"},
    ):
        with pytest.raises(ObservationViewError):
            view(observation, validated=False)


@pytest.mark.parametrize("budget", [0, -1, True, 1.5, "1000"])
def test_budget_must_be_a_positive_integer(real, budget):
    with pytest.raises(ValueError) as raised:
        compact_async_observation(
            real["evaluate"], budget_bytes=budget, result_validated_at_delivery=True
        )
    assert type(raised.value) is ValueError


def test_validation_flag_must_be_a_bool(real):
    with pytest.raises(ValueError):
        compact_async_observation(
            real["evaluate"], budget_bytes=BIG, result_validated_at_delivery="yes"
        )
