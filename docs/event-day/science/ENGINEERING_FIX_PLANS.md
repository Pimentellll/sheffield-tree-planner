# Engineering fix plans for Ben — problems found in the science review

**Revised 13 Nov 2026 (issue #57 reconciliation):** checked against `origin/main` `033d56d` (PRs #66, #67, #70, #71, #76, #77, #78, #80 merged) and the branches listed in [README §Reconciliation](README.md#reconciliation-after-ca1662d-13-nov). "PR #70 @ `8d24e73`" below is its merged head, now `docs/implementation/NEMOTRON_AGENT_RUNTIME_AUDIT_20261113.md` on main. Nothing was executed.

**Re-checked 13 Nov 2026 against `origin/main` `be9d544`** (read-only; nothing was executed): between `033d56d` and `be9d544` the only backend source changes are `agents/observation_views.py` (added, PR #75, imported by nothing) and `site/source_inventory.py` (PRs #86, #94); the runtime audit and `deploy/` are unchanged; no native `/api/chat` client is on any pushed ref. One citation moved (`docs/EVENT_DAY_EXECUTION_2026-11-13.md` L251 is now L253). Ben's steps are unchanged, and the individual line citations inside FIX-1 to FIX-4 were not re-read one by one.

> **Reconciliation note (13 Nov, after PR #70 @ `8d24e73`):** FIX-1a/FIX-2/FIX-3 were written for the `/v1` route. PR #70 (R03, R05, R25, §9) records that Ben's active lane is the native Ollama `/api/chat` client (#54/#62), with `/v1` plus an alias or `OLLAMA_CONTEXT_LENGTH` as the fallback. That native client is not on any pushed ref we inspected. Everything below applies unchanged **if the release uses the `/v1` client**. On the native `/api/chat` lane the equivalents are:
>
> - **FIX-1a:** no Modelfile alias is created (#62). Send `options.num_ctx` 8192 and `options.num_predict` (the 1,024 output reservation) on every request. If the installed Ollama supports `"truncate": false` and `"shift": false`, send both and treat the error as a fail-closed `context_exceeded` with no dispatch (PR #70 §9 step 4). Record `/api/version` and `/api/ps` (organiser tag only loaded).
> - **FIX-1b and its tests 1–4:** bound the server-reported `prompt_eval_count` at 7,168 (8,192 − 1,024) instead of `usage.prompt_tokens`, and record `eval_count` and `done`/`done_reason`. Missing counts fail closed. A prompt-count bound is a second check, not proof that nothing was truncated (§9 step 4). Under Ollama prompt (prefix) caching, `prompt_eval_count` may count only newly evaluated tokens, and so may `usage.prompt_tokens` on the `/v1` fallback if it comes from the same counter (unverified); establish the field's behaviour on the DGX, or use the model's tokenizer count of the full request or a cold-cache request, before relying on it (acceptance X-06; PR #70 §9; ledger H-06). 7,168 is the engineering guard and a guard trip is a host failure; the validity rule is server-reported prompt + output ≤ 8,192 per request (acceptance X-06).
> - **FIX-1 acceptance evidence:** the requested `options.num_ctx`/`num_predict` and `/api/ps` showing only the organiser tag replace the `ollama show canopy-nemotron-nano-8k --modelfile` line; FIX-1 guard evidence on C2 is every request's `prompt_eval_count` ≤ 7,168. Organiser validity is judged separately per acceptance X-06 (prompt + output ≤ 8,192, with the requested/loaded context ≥ that sum).
> - **FIX-2:** `per_request_usage` takes `prompt_eval_count`, `eval_count` and `done_reason` from each native response, and each receipt records which transport produced it. Derive `/api/version` and `/api/ps` from the server root, not by `removesuffix("/v1")`. Record `think` and `options` (including `num_ctx`) instead of `reasoning_effort`; the frozen prompt bytes and hashes do not change. `CANOPY_LOCAL_MODEL` is the organiser tag, with no alias.
> - **FIX-3 step 1:** the smoke passes when `message.tool_calls[0].function.name` is a registered tool, `function.arguments` is an object that the client normaliser converts to canonical JSON text, `done` is true with an allow-listed `done_reason`, and `prompt_eval_count`/`eval_count` are present. Record `options.num_ctx` and `num_predict`. A JSON-object `arguments` value is not a failure on this lane.
> - **FIX-3 steps 3–4:** `ollama-runtime.md` records the transport and request options instead of a Modelfile and alias; `application.env.example` names the native base URL and the organiser tag, not `canopy-nemotron-nano-8k`. The same condition applies to the #64 checklist.
> - **Model naming (either lane):** the form's "AI models used" field and acceptance X-02 must record the **organiser base tag** behind any alias (`ollama show <alias> --modelfile`, `FROM` line), never the team-made alias.
>
> Ben owns the implementation; these are proposed adjustments, not edits to his plan.

**Owner of implementation:** Ben (backend, agent integration, Spark). **Author of plans:** Arnav (scientific review). **Status:** plans only. No code in this repository was changed by this document, and nothing here has been run.
**Basis:** read-only inspection of `main` @ `630ee65`. If your unpushed integration already solves a problem, skip the code steps and only produce that fix's acceptance evidence.

| Fix | Problem (from [README findings](README.md#findings-that-need-team-attention-read-first)) | Priority | Files (Ben-owned) | Estimate | Blocks |
|---|---|---|---|---|---|
| [FIX-1](#fix-1--enforce-and-prove-the-8192-token-request-limit) [#62](https://github.com/Pimentellll/sheffield-tree-planner/issues/62) | 8,192-token rule can't be set or proven over Ollama `/v1`; search observations previously reached ~11.5–12.4k tokens (earlier laptop Qwen runs; not Spark evidence) | **P0** | `backend/src/tree_planner/agents/__init__.py`, `backend/tests/agents/test_protocol.py`, Spark Ollama config | 45–60 min | #55 C2, organiser compliance |
| [FIX-2](#fix-2--five-case-spark-driver) [#63](https://github.com/Pimentellll/sheffield-tree-planner/issues/63) | No driver runs custom prompts with a chosen tool set and saves receipts | **P0** | new `backend/tests/agents/test_five_case_spark.py` | 30–40 min | #55 entirely |
| [FIX-3](#fix-3--record-and-configure-the-real-ollama-runtime) [#64](https://github.com/Pimentellll/sheffield-tree-planner/issues/64) | Committed deployment profile is vLLM/HF BF16, not the organiser's Ollama tag | **P0** | `deploy/spark/application.env.example`, new `deploy/spark/ollama-runtime.md`, `docs/DGX_SPARK.md` | 15 min | #60 model field, X-02 |
| [FIX-4](#fix-4--optional-relocation-to-another-catalogue-position) [#65](https://github.com/Pimentellll/sheffield-tree-planner/issues/65) | `compare_locations` to another catalogue position is always infeasible | P1, **optional; after P0 only** | `backend/src/tree_planner/search/__init__.py`, `evaluators/physical_runtime.py`, tests | 30–45 min | Nothing for submission |

**Order:** FIX-3 step 1–3 (smoke test) → FIX-1 → FIX-2 → hand the window to Arnav → FIX-4 **post-submission** *(13 Nov reconciliation: the five-case run and the filmed release must be one SHA, protocol §2 / acceptance X-03, and C3 is pre-registered as variant A; if FIX-4 is added to any release SHA, C1–C5 must be re-run on that SHA)*. Every fix keeps AGENTS.md rules: no hard-constraint relaxation, no fabricated outputs, tests added for changed behaviour, evidence recorded in BUILD/#54.

---

## FIX-1 — Enforce and prove the 8,192-token request limit

### Problem
- `LocalClient.complete` posts to `{base}/chat/completions` (Ollama's OpenAI-compatible route). Ollama states that the OpenAI API has no way to set a model's context size, so `options.num_ctx` cannot be sent per request. The effective context is whatever the server or model defaults to.
- The client's pre-flight bound is `max_input_bytes` (bytes). `max_input_tokens` requires a trusted counter that nothing configures.
- `AgentLoop._dispatch` appends the **entire** `Job` and `Result` JSON to the conversation. A search Result (two layouts × three cases × targets × metrics, plus every constraint record and provenance) is what pushed earlier laptop runs (16k-context Qwen, not Spark evidence; `docs/EVENT_DAY_EXECUTION_2026-11-13.md` L253 on `be9d544`) to ~11.5–12.4k prompt tokens; local laptop/WSL Qwen runs from Arnav's paused integration session reported 11.8–12.8k (his 12:26 GMT #54 handoff to Ben; not Spark evidence).
- If the server context is 8,192 and a prompt is longer, Ollama may truncate silently. If the server context is larger, requests can exceed the organiser cap without any error.

### Solution (three parts, all required)

> Applies only if the release uses the `/v1` client. For the native `/api/chat` lane, see the [reconciliation note](#engineering-fix-plans-for-ben--problems-found-in-the-science-review) at the top of this file.

**1a. Pin the server-side context to 8,192 for the model you evaluate (Spark, no code).**

```bash
ollama show nemotron-3-nano:30b            # confirm "tools" appears under Capabilities
cat > /tmp/Modelfile.canopy <<'EOF'
FROM nemotron-3-nano:30b
PARAMETER num_ctx 8192
EOF
ollama create canopy-nemotron-nano-8k -f /tmp/Modelfile.canopy
ollama show canopy-nemotron-nano-8k --modelfile | grep num_ctx   # expect: PARAMETER num_ctx 8192
```

The alias shares the same weights; record both names. If organisers forbid creating models on their Ollama, ask whether `OLLAMA_CONTEXT_LENGTH=8192` can be set on their service instead. If neither is allowed, keep 1b and 1c and report the server default from `/api/ps` as a limitation. Before loading it, unload anything else (`ollama ps`, then `ollama stop <other>`) so only one model is loaded.

**1b. Fail closed on the server-reported prompt size (client change).**

Use the `usage.prompt_tokens` the server returns. That is a real count, not a byte heuristic, so it fits the docstring rule "No byte heuristic is ever reported as a token count".

In `ClientConfig`, add an optional field (default `None` keeps current behaviour and every existing test):

```python
    max_reported_prompt_tokens: int | None = None
```

and in `__post_init__`:

```python
        if self.max_reported_prompt_tokens is not None and (
            type(self.max_reported_prompt_tokens) is not int or self.max_reported_prompt_tokens <= 0
        ):
            raise ValueError("reported prompt-token budget must be explicit and positive")
```

In `LocalClient.complete`, inside the `try`, after `message` has been validated and before `return message`:

```python
            if cfg.max_reported_prompt_tokens is not None:
                usage = payload.get("usage")
                reported = usage.get("prompt_tokens") if isinstance(usage, dict) else None
                if (
                    type(reported) is not int
                    or reported < 0
                    or reported > cfg.max_reported_prompt_tokens
                ):
                    raise ProtocolError("reported prompt tokens exceed budget or unavailable")
            self.last_usage = payload.get("usage")
```

Also set `self.last_usage = None` in `__init__`. (`payload` is the parsed response at that point; `ProtocolError` is not caught by the `except` tuple, so it propagates and `AgentLoop` returns `failed` with this reason.)

**Value to use on the Spark: `max_reported_prompt_tokens = 7168`** (= 8192 − `max_tokens` 1024). Reason: with `num_ctx` 8192, a truncated over-long prompt is reported at or near the context size. Requiring the prompt to leave room for the full output budget catches likely truncation as well as any request that cannot fit prompt + answer in 8,192. Keep `max_input_bytes` as a coarse pre-flight guard. After the first live call, compute bytes-per-token from the recorded request and usage, and set `max_input_bytes ≈ 0.9 × 7168 × bytes_per_token`. Record it as a heuristic guard, never as a token count.

**1c. Send the model a compact observation; keep the full Result authoritative.**

In `backend/src/tree_planner/agents/__init__.py`, add module-level helpers:

```python
_VIEW_METRICS = frozenset({"additional_shade", "weighted_shade_utility", "winter_sun_loss"})


def _job_view(job: Job) -> dict:
    return {
        "job_id": job.job_id,
        "operation": job.operation,
        "status": job.status,
        "run_id": job.run_id,
        "error": None if job.error is None else job.error.model_dump(mode="json"),
    }


def _result_view(result: Result) -> dict:
    """Compact model-facing view. The full Result stays in AgentLoop.results and
    is the only source for the host-generated conclusion."""
    by_instance = {m.metric_instance_id: m for m in result.metrics}
    deltas = []
    if result.comparison is not None:
        for d in result.comparison.deltas:
            a = by_instance.get(d.base_metric_instance_id)
            b = by_instance.get(d.alternative_metric_instance_id)
            if a is None or b is None or a.target_id is not None:
                continue
            deltas.append({
                "metric_id": a.metric_id, "case_id": a.case_id,
                "base_layout_id": a.layout_id, "alternative_layout_id": b.layout_id,
                "value": d.value, "unit": d.unit,
            })
    return {
        "run_id": result.run_id,
        "operation": result.operation,
        "analytical_outcome": result.analytical_outcome,
        "layouts": [
            {
                "layout_id": e.layout.layout_id, "role": e.role, "selected": e.selected,
                "feasibility": e.feasibility, "reasons": list(e.reasons),
                "cost_pence": e.cost_pence, "tree_count": e.tree_count,
                "placements": [
                    {"placement_id": p.placement_id, "candidate_id": p.candidate_id,
                     "position_enu_m": list(p.position_enu_m)}
                    for p in e.layout.placements
                ],
            }
            for e in result.layouts
        ],
        "metrics": [
            {"layout_id": m.layout_id, "case_id": m.case_id, "metric_id": m.metric_id,
             "value": m.value, "unit": m.unit, "horizon_years": m.horizon_years}
            for m in result.metrics
            if m.target_id is None and m.metric_id in _VIEW_METRICS
        ],
        "constraints_not_passed": [
            {"layout_id": c.layout_id, "case_id": c.case_id, "rule": c.rule, "status": c.status,
             "observed_value": c.observed_value, "limit": c.limit, "unit": c.unit}
            for c in result.constraints
            if c.status != "pass"
        ],
        "constraints_passed": sum(c.status == "pass" for c in result.constraints),
        "deltas": deltas,
        "limitations": list(result.limitations),
        "view": "compact: aggregate-target metrics only; full Result retained by host",
    }
```

Then in `AgentLoop._dispatch`, replace only the two async return statements:

```python
                return {"job": _job_view(job), "result": _result_view(result)}
            return {"job": _job_view(job)}
```

Leave `inspect_site`/`prepare_scenario` observations unchanged: `test_protocol_only_injection_and_pinned_site` relies on raw untrusted text passing through as data. Nothing else changes: `self.jobs`/`self.results` still hold full objects, `_current_results` and `_conclusion` still use them, and every ID the model may cite (`job_id`, `run_id`) is still in the view.

**Why this is scientifically safe:** the model loses nothing it may legitimately report (units, cases, feasibility, costs, failed or unknown constraints, deltas, limitations). It no longer sees per-target duplicates, provenance hashes or passing-constraint evidence lists. The user-facing figures remain host-generated from full Results.

### Tests to add (`backend/tests/agents/test_protocol.py`, using the existing `httpx.MockTransport` pattern near line 264)
1. `max_reported_prompt_tokens=7168`; response `usage.prompt_tokens=7000` → returns message; `last_usage` equals the usage dict.
2. Same config; `prompt_tokens=7200` → `ProtocolError("reported prompt tokens exceed budget or unavailable")`.
3. Same config; response without `usage` → the same `ProtocolError`.
4. Config unset → a response without `usage` still returns (backward compatible).
5. `_result_view` on a Result captured from `create_physical_runtime(winter=True)` search: contains every `layout_id`, `run_id`, and every `additional_shade` aggregate metric; `json.dumps(view)` is **shorter** than `json.dumps(result.model_dump(mode="json"))`. Record both byte lengths in BUILD.
6. Re-run `backend/tests/agents` and `backend/tests/benchmarks` to confirm no other test depended on the full observation.

### Acceptance evidence (Spark, release SHA)
> Applies only if the release uses the `/v1` client; native `/api/chat` equivalents are in the reconciliation note at the top of this file.

- `ollama show canopy-nemotron-nano-8k --modelfile` output with `num_ctx 8192`, and `/api/ps` showing that model only.
- FIX-1 guard evidence: C2 of the five-case run completes with every response's `usage.prompt_tokens` ≤ 7168 (from the receipt). 7,168 is the FIX-1 engineering guard, not the validity rule; organiser validity is checklist row **X-06** (server-reported prompt + output ≤ 8,192 per request), with **X-05**, in [SCIENTIFIC_ACCEPTANCE](SCIENTIFIC_ACCEPTANCE.md).
- Unit-test output for tests 1–6 on the Spark.

### Risks
- If `/v1` responses on this Ollama version lack `usage`, test 3's behaviour makes every call fail. Then switch only the guard off, record "usage unavailable" (X-06 = blocked), and rely on 1a + 1c. Do **not** fabricate counts.
- The compact view could still exceed budget with many layouts. The seed has at most three, so it is fine for the event.

---

## FIX-2 — Five-case Spark driver

### Problem
`backend/tests/agents/test_live_local.py` exposes **one** operation per test, hard-codes its prompt and uses the one-tree *reference* runtime. Nothing on `main` can run the five frozen prompts with a shared four-tool set on the physical runtime and save receipts. Arnav must not write the harness or run it on a laptop.

### Solution
Add an opt-in pytest module `backend/tests/agents/test_five_case_spark.py` (skipped unless its environment variables are set). It reuses `RecordingClient` (`import test_live_local as live`, as `test_live_failures.py` already does). It reads the frozen inputs from [`five_case_prompts.json`](five_case_prompts.json) and checks the hashes in that file before any model call. It **records**; it does not assert behavioural pass/fail, because Arnav scores the receipts.

```python
"""Opt-in DGX five-case evaluation (docs/event-day/science/AGENT_EVALUATION_PROTOCOL.md).
Set CANOPY_LOCAL_MODEL_BASE, CANOPY_LOCAL_MODEL, CANOPY_FIVE_CASE_DIR. Never mocked."""
import hashlib, json, os, platform, re, socket, subprocess
from pathlib import Path
from threading import Event, Thread
from time import monotonic, sleep

import httpx, pytest, uvicorn
import test_live_local as live
from tree_planner.agents import AgentLoop, ClientConfig
from tree_planner.agents.http import HTTPDispatcher
from tree_planner.evaluators.physical_runtime import create_physical_runtime

SPEC = Path(__file__).resolve().parents[3] / "docs/event-day/science/five_case_prompts.json"
sha = lambda t: hashlib.sha256(t.encode("utf-8")).hexdigest()


def fill_context(service, ref, template):
    sc = service.scenarios.get_scenario(ref); inp = sc.input
    site = service.scenarios.get_site(inp.site_id, inp.scene_revision, inp.semantic_revision)
    lref = inp.proposed_layout_ref
    layout = service.scenarios.get_layout(lref.layout_id, lref.revision)
    values = {
        "{scenario_id}": sc.scenario_id, "{revision}": str(sc.revision),
        "{site_id}": inp.site_id, "{scene_revision}": str(inp.scene_revision),
        "{layout_id}": lref.layout_id, "{layout_revision}": str(lref.revision),
        "{placement_id} at {position}": "; ".join(
            f"{p.placement_id} at {list(p.position_enu_m)}" for p in layout.placements),
        "{candidate list}": ", ".join(
            f"{c.candidate_id} {list(c.position_enu_m)}"
            for c in sorted(site.candidate_catalogue, key=lambda c: c.candidate_id)),
        "{budget_pence}": str(inp.constraints.budget_pence),
        "{max_tree_count}": str(inp.constraints.max_tree_count),
    }
    text = template
    for key, value in values.items():
        text = text.replace(key, value)
    assert not re.search(r"\{[a-z_ ]+\}", text), "unfilled host-context placeholder"
    return text


def test_five_cases_on_spark(tmp_path):
    base, model = os.environ.get("CANOPY_LOCAL_MODEL_BASE"), os.environ.get("CANOPY_LOCAL_MODEL")
    out = os.environ.get("CANOPY_FIVE_CASE_DIR")
    if not (base and model and out):
        pytest.skip("explicit Spark model and output directory not configured")
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    assert sha(spec["host_context_template"]) == spec["host_context_template_sha256"]
    for case in spec["cases"]:
        assert sha(case["prompt"]) == case["prompt_sha256"], case["id"]
    out = Path(out); out.mkdir(parents=True, exist_ok=False)

    runtime = create_physical_runtime(tmp_path / "runtime", winter=True)
    # Start runtime.app on a loopback socket exactly as live.live_runtime does
    # (uvicorn.Server on 127.0.0.1:0, wait for server.started, stop in finally).
    ...
    service = runtime.app.state.service
    accepted = service.scenarios.get_scenario(runtime.scenario_ref)
    context = fill_context(service, runtime.scenario_ref, spec["host_context_template"])
    env = {
        "git_sha": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
        "git_dirty": bool(subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()),
        "machine": platform.machine(), "platform": platform.platform(),
        "ollama_version": httpx.get(base.removesuffix("/v1") + "/api/version", timeout=5).json(),
        "host_context_filled_sha256": sha(context),
    }
    c = spec["client"]
    for case in spec["cases"]:
        config = ClientConfig(base, model, timeout_s=c["timeout_s"], max_input_bytes=65536,
                              max_response_bytes=1048576, max_tokens=c["max_tokens"],
                              reasoning_effort=c["reasoning_effort"], temperature=c["temperature"],
                              max_reported_prompt_tokens=7168)        # FIX-1b
        client = live.RecordingClient(config)
        started = monotonic()
        with HTTPDispatcher(api, accepted_ref=runtime.scenario_ref, timeout_s=15,
                            max_response_bytes=1048576) as dispatcher:
            loop = AgentLoop(client, dispatcher, accepted, set(spec["operations"]),
                             deadline=monotonic() + c["loop_deadline_s"], stop=Event(),
                             poll_interval_s=c["poll_interval_s"], action_budget=c["action_budget"])
            outcome = loop.run(context + "\n" + case["prompt"])
        usage = []
        for x in client.recording.exchanges:
            try:
                usage.append(json.loads(x.get("response_text") or "{}").get("usage"))
            except ValueError:
                usage.append(None)
        receipt = {  # same fields as live receipt, plus:
            "case": case["id"], "prompt_sha256": case["prompt_sha256"], "env": env,
            "operations": sorted(spec["operations"]), "elapsed_s": monotonic() - started,
            "per_request_usage": usage,
            "outcome": {...},                      # copy live.run_actual_model's outcome block
            "messages": loop.messages, "http": dispatcher.trace,
            "completions": client.completions, "model_http": client.recording.exchanges,
            "accepted_ref": runtime.scenario_ref.model_dump(mode="json"),
        }
        (out / f"{case['id']}.json").write_text(json.dumps(receipt, indent=2, allow_nan=False,
            default=lambda v: v.model_dump(mode="json")), encoding="utf-8")
    (out / "SHA256SUMS").write_text("".join(
        f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in sorted(out.glob("C*.json"))))
```

Fill the two `...` by copying the server start/stop block of `live.live_runtime` and the `outcome` dictionary from `live.run_actual_model`. Do not change `AgentLoop`. `api` is `base_url + "/api/v1"` of the started server.

**Design decisions (keep them):**
- **One runtime and one accepted scenario for all five cases**, run in order C1→C5, as the protocol requires. Later cases may receive cached deliveries; the Result's `execution_mode` records this.
  > *Reconciliation note (13 Nov):* per `docs/CONTRACTS.md` L163, a cached delivery is recorded in `job.delivery.execution_mode`; `Result.provenance.execution_mode` keeps the source computation's mode (acceptance A-04). Record both; Ben's step is otherwise unchanged.
- No behavioural asserts. The test passes when all five receipts and `SHA256SUMS` are written; failures of the model are data, not test errors.
- `exist_ok=False` so a rerun can never overwrite earlier receipts (use a new directory per attempt).

### How to run (Spark, in Arnav's window)

```bash
export CANOPY_LOCAL_MODEL_BASE=http://127.0.0.1:11434/v1
export CANOPY_LOCAL_MODEL=canopy-nemotron-nano-8k      # from FIX-1a
export CANOPY_FIVE_CASE_DIR=$HOME/canopy-evidence/five-case-$(date -u +%Y%m%dT%H%M%SZ)
.venv/bin/python -m pytest backend/tests/agents/test_five_case_spark.py -q -s
```

### Acceptance evidence
`C1.json` … `C5.json` and `SHA256SUMS` in the output directory. Each contains a clean `git_sha`, `machine` = `aarch64`, the Ollama version, per-request usage and the raw exchanges. Hand the directory path to Arnav, who scores it with the [protocol §7 template](AGENT_EVALUATION_PROTOCOL.md#7-evidence-recording-template-copy-one-block-per-run).

---

## FIX-3 — Record and configure the real Ollama runtime

### Problem
`deploy/spark/model-profile.json` and `application.env.example` describe a vLLM container serving the Hugging Face BF16 checkpoint as `tree-planner-local` on port 8000 (`candidate_not_device_tested`). The organisers supply Ollama on `127.0.0.1:11434` with tags such as `nemotron-3-nano:30b`. The form's "AI models used" field and the video must name what actually ran.

### Solution
> Steps 1 and 4 apply only if the release uses the `/v1` client. If Ben's native `/api/chat` client ships (#54/#62), use the pass criteria in the reconciliation note at the top of this file; a JSON-object `arguments` value is not a failure there.

1. **Smoke-test tool calling on the Spark** (loopback; no public port):

```bash
curl -s http://127.0.0.1:11434/v1/chat/completions -H 'content-type: application/json' -d '{
 "model":"canopy-nemotron-nano-8k","stream":false,"temperature":0,"reasoning_effort":"none","max_tokens":256,
 "messages":[{"role":"user","content":"Call the ping tool with x=1."}],
 "tools":[{"type":"function","function":{"name":"ping","description":"test",
   "parameters":{"type":"object","properties":{"x":{"type":"integer"}},"required":["x"]}}}]}' | python3 -m json.tool
```

   Pass when: `choices[0].message.tool_calls[0].function.arguments` is a JSON **string**; `finish_reason` is `tool_calls` or `stop` (both accepted by `LocalClient`); and `usage.prompt_tokens` is present. If the server rejects `reasoning_effort`, remove it from the client config and record that.
2. **Repeat step 1 for `nemotron-3.5-lightning:30b`** only if you want the alternative tag. Load one model at a time.
3. **Create `deploy/spark/ollama-runtime.md`** with the observed `ollama --version`, `ollama list`, `ollama show <tag>` (parameters, quantization, capabilities), the Modelfile from FIX-1a, the alias name, and the smoke-test output (redact hostnames/IPs). Date and SHA it.
4. **Edit `deploy/spark/application.env.example`:** `LLM_BASE_URL=http://127.0.0.1:11434/v1` and `LLM_MODEL=canopy-nemotron-nano-8k`, with a comment that this is the organiser-supplied Ollama path.
5. **Add one line to `docs/DGX_SPARK.md`:** the vLLM `model-profile.json` is a pre-event candidate and was not used at the event (if true). Do not delete it; it is provenance.

### Acceptance evidence
`ollama-runtime.md` committed on the release branch; checklist row **X-02** can then be verified by Arnav. The form's model field is filled from it.

---

## FIX-4 — Optional: relocation to another catalogue position

**Do this only after FIX-1–3 and the five-case run, and only before the 16:00 freeze. It is not needed for submission.** If it is not done, the protocol's C3 expected answer ("not a permitted alternative") stays correct and the video should show search instead.

### Problem
`search.relocate()` keeps the placement's `candidate_id` and `location_id` and changes only `position_enu_m`. `check()` then always records `candidate mismatch` for any move, including a move onto another catalogue position. So `compare_locations` cannot show a feasible alternative even when one exists in the catalogue.

### Solution
When the requested position is exactly a catalogue candidate with the same profile, rebind the placement to that candidate and evaluate it normally (non-diagnostic). Otherwise keep today's diagnostic behaviour.

In `backend/src/tree_planner/search/__init__.py`:

```python
def relocate(problem, placements, placement_id, alternative_position_enu_m, evaluate):
    """Keep placement identity/profile; rebind to an exact same-profile catalogue
    candidate when the target is one, otherwise diagnose the requested position."""
    items = [dict(p) for p in placements]
    indices = [i for i, p in enumerate(items) if p["placement_id"] == placement_id]
    if len(indices) != 1:
        raise ValueError("unresolved placement")
    i = indices[0]
    target = [
        c for c in problem.site.candidate_catalogue
        if list(c.position_enu_m) == list(alternative_position_enu_m)
        and c.profile_id == items[i]["profile_id"]
    ]
    if items[i]["candidate_id"] is not None and len(target) == 1:
        c = target[0]
        items[i].update(position_enu_m=list(c.position_enu_m),
                        candidate_id=c.candidate_id, location_id=c.location_id)
        return Comparison(tuple(items), check(problem, items, evaluate),
                          ("position_enu_m", "candidate_id", "location_id"))
    items[i]["position_enu_m"] = alternative_position_enu_m
    return Comparison(
        tuple(items), check(problem, items, evaluate, diagnostic=True), ("position_enu_m",)
    )
```

In `backend/src/tree_planner/evaluators/physical_runtime.py` (`compare_locations` branch), replace the hard-coded

```python
            changed = ["placements." + request.arguments.placement_id + ".position_enu_m"]
```

with

```python
            changed = [
                "placements." + request.arguments.placement_id + "." + field
                for field in alternative.changed_inputs
            ]
```

Spacing, budget, count, region and winter checks still apply through `check()`. For example, moving tree-1 onto a position already occupied by another placement fails spacing.

### Tests
- `backend/tests/search/test_search.py`: a relocation onto a same-profile catalogue position is `feasible` with `changed_inputs == ("position_enu_m", "candidate_id", "location_id")`. The existing off-catalogue case (`[6, 0, 0]`) remains diagnostic and infeasible.
- `backend/tests/evaluators/test_physical_runtime.py`: the `compare_locations` Result for `[2, 0, 0]` on the seed has an alternative with `feasibility == "feasible"`, deltas present, and `changed_inputs` listing the three fields.
- Run `backend/tests/search backend/tests/evaluators backend/tests/jobs backend/tests/contracts`; regenerate types only if a contract changed (none should).

### Coordination
- Tell **Alex**: a relocation can now be feasible, and the UI must not still label every relocation "diagnostic".
- Tell **Arnav before the five-case run**. Per the protocol PASS/FAIL AMENDMENT of 13 Nov (protocol §8), FIX-4 is **post-submission** and C3 is scored only as variant A; if FIX-4 is on any release SHA anyway, C1–C5 are re-run on that SHA and C3 is reported as run under a changed contract (no pre-registered grade exists for it), not re-graded as C3-B.
- Update the PHYSICAL_RUNTIME.md sentence "A known candidate moved away from its catalogue coordinate is computed only in explicit diagnostic mode" to mention catalogue rebinding.

---

## Not assigned (by design)
- **Agent-run endpoint and agent UI**: the endpoint is Ben's (#54/#73) and the agent-evidence UI is Arnav's (#74), per the 13 Nov decision; no duplicate issue is opened. *Update (13 Nov decision): the agent-evidence UI (#74) is Arnav's; Alex keeps the rest of the UI (#56/#58), including placing the panel in his shell (runtime audit R02 on main).*
- **Multi-hour time bins** in the seed would make shade figures more meaningful, but would change every number, cache identity and test expectation on event day. Deferred; the narration uses "one midday sun position, counted for one hour" instead (acceptance N-02; ledger S-05).
- **Narration wording** (measured→computed, weighted vs area, pence vs £) is content work for Arnav and Alex; see the [ledger](EVIDENCE_AND_CLAIMS_LEDGER.md).
