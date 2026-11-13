#!/usr/bin/env python3
"""Service latency benchmark against a RUNNING CANOPY server. Standard library only.

Complements, and does not duplicate, the agent evaluation ladder
(backend/tests/benchmarks/agent_eval.py), which owns agent success, tool correctness and
evidence scoring. This script measures, with sample counts and distributions:

  * deterministic jobs over real HTTP: evaluate, search, compare_locations, compare_scenarios
    (submit -> poll -> completed; POST /jobs with 20 ms polling, so this is service latency,
    not the agent's tool-phase latency);
  * raw local-model inference, streamed: first call, warm calls, time to first token and
    generation rate, on a short prompt without tools (a serving baseline, not an agent turn);
  * host memory, and GPU memory where nvidia-smi reports it, during the model phase.

Everything is sequential: one job and one model request at a time. Run it ON THE HOST THAT
SERVES THE MODEL: the model URL is the server's own loopback URL, so through an SSH tunnel
it would time whatever answers on this machine's port instead. The receipt is written after
every phase and records the machine it ran on; a laptop receipt is not Spark evidence.

  python3 deploy/spark/bench.py --api http://127.0.0.1:8765 --out bench.json
Exit status: 0 measured; 1 a deterministic operation failed or no model call succeeded when
a model is configured; 2 the server could not be reached.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import threading
import time
import urllib.error
import urllib.request
import uuid


def dist(values):
    values = sorted(v for v in values if v is not None)
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "min": round(values[0], 4),
        "median": round(statistics.median(values), 4),
        "p90": round(values[min(len(values) - 1, round(0.9 * (len(values) - 1)))], 4),
        "max": round(values[-1], 4),
        "mean": round(statistics.fmean(values), 4),
    }


class Api:
    def __init__(self, base):
        self.base = base.rstrip("/")
        self.headers = {"Origin": self.base, "Content-Type": "application/json"}

    def call(self, method, path, body=None, timeout=60):
        """Returns (status, json). Status 0 means the request itself failed."""
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(self.base + path, method=method, headers=self.headers, data=data)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read() or b"{}")
            except ValueError:
                return e.code, {}
        except (urllib.error.URLError, OSError, ValueError) as e:
            return 0, {"transport_error": f"{type(e).__name__}: {e}"[:200]}

    def job(self, ref, operation, arguments, timeout=300):
        t0 = time.perf_counter()
        code, job = self.call(
            "POST",
            "/api/v1/jobs",
            dict(request_id=f"bench-{uuid.uuid4().hex}", scenario_ref=ref, operation=operation, arguments=arguments),
        )
        if code != 202 or "status" not in job:
            return {"ok": False, "error": f"HTTP {code} {job.get('code') or job.get('transport_error')}", "wall_s": None}
        while job.get("status") in ("queued", "running") and time.perf_counter() - t0 < timeout:
            time.sleep(0.02)
            code, latest = self.call("GET", "/api/v1/jobs/" + job["job_id"])
            if code == 200:
                job = latest
        wall = time.perf_counter() - t0
        ok = job.get("status") == "completed" and bool(job.get("run_id"))
        return {"ok": ok, "wall_s": wall, "status": job.get("status"), "error": None if ok else str(job.get("status"))}


class MemorySampler(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.stop_event = threading.Event()
        self.min_available = None
        self.max_gpu_mib = None
        self.host_samples = 0
        self.gpu_samples = 0

    def run(self):
        while not self.stop_event.wait(1.0):
            try:
                with open("/proc/meminfo") as handle:
                    for line in handle:
                        if line.startswith("MemAvailable:"):
                            v = int(line.split()[1]) * 1024
                            self.min_available = v if self.min_available is None else min(self.min_available, v)
                            self.host_samples += 1
            except OSError:
                pass
            try:
                out = subprocess.run(
                    ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=5,
                ).stdout.strip().splitlines()
                if out and out[0].strip().isdigit():
                    g = int(out[0])
                    self.max_gpu_mib = g if self.max_gpu_mib is None else max(self.max_gpu_mib, g)
                    self.gpu_samples += 1
            except (OSError, subprocess.SubprocessError):
                pass


def environment(api):
    def run(cmd):
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=15).stdout.strip()[:1500]
        except Exception as exc:
            return f"unavailable: {type(exc).__name__}"

    mem = {}
    try:
        with open("/proc/meminfo") as handle:
            for line in handle:
                k, v = line.split(":", 1)
                if k in ("MemTotal", "MemAvailable"):
                    mem[k] = int(v.split()[0]) * 1024
    except OSError:
        pass
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    commit = None
    if os.path.exists(os.path.join(here, "COMMIT")):
        with open(os.path.join(here, "COMMIT")) as handle:
            commit = handle.read().strip()
    return {
        "machine": platform.machine(), "platform": platform.platform(), "cpu_count": os.cpu_count(),
        "memory_bytes": mem, "bundle_commit": commit,
        "gpu": run(["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.used", "--format=csv,noheader"]),
        "health": api.call("GET", "/api/v1/health")[1],
        "agent_status": api.call("GET", "/api/v1/agent/status")[1],
    }


def head_scenario(api):
    code, session = api.call("GET", "/canopy-dev-session.json")
    if code != 200 or "scenario_ref" not in session:
        raise RuntimeError("no UI session route: start the server with --frontend-dist (canopyctl start)")
    sid, rev = session["scenario_ref"]["scenario_id"], session["scenario_ref"]["revision"]
    while api.call("GET", f"/api/v1/scenarios/{sid}?revision={rev + 1}")[0] == 200:
        rev += 1
    scenario = api.call("GET", f"/api/v1/scenarios/{sid}?revision={rev}")[1]
    return {"scenario_id": sid, "revision": rev, "scope": "accepted"}, scenario


def deterministic(api, ref, scenario, runs):
    inp = scenario["input"]
    layout_ref = inp["proposed_layout_ref"]
    layout = api.call("GET", f"/api/v1/layouts/{layout_ref['layout_id']}?revision={layout_ref['revision']}")[1]
    site = api.call(
        "GET",
        f"/api/v1/sites/{inp['site_id']}?scene_revision={inp['scene_revision']}&semantic_revision={inp['semantic_revision']}",
    )[1]
    placement = layout["placements"][0]
    other = next(
        (
            c for c in site["candidate_catalogue"]
            if c["position_enu_m"] != placement["position_enu_m"] and c["plantability_status"] != "excluded"
        ),
        None,
    )
    ops = {"evaluate_layout": {"layout_ref": layout_ref}, "search_layouts": {}}
    if other:
        ops["compare_locations"] = {
            "layout_ref": layout_ref, "placement_id": placement["placement_id"],
            "alternative_position_enu_m": other["position_enu_m"],
        }
    available = set(api.call("GET", "/api/v1/health")[1].get("available_operations", []))
    out = {"catalogue_candidates": len(site["candidate_catalogue"])}

    def measure(op, args, n):
        samples = [api.job(ref, op, args) for _ in range(n)]
        return {
            "success": sum(s["ok"] for s in samples), "attempts": n,
            "wall_s": dist([s["wall_s"] for s in samples if s["ok"]]),
            "wall_s_first": samples[0]["wall_s"] if samples and samples[0]["ok"] else None,
            "errors": sorted({str(s["error"]) for s in samples if not s["ok"]}),
        }

    for op, args in ops.items():
        out[op] = measure(op, args, runs) if op in available else {"skipped": "operation not registered"}
    if "compare_scenarios" in available:
        proposed = json.loads(json.dumps(inp))
        proposed["constraints"]["budget_pence"] = max(1, inp["constraints"]["budget_pence"] - 1)
        code, hyp = api.call(
            "POST", "/api/v1/operations",
            {"request_id": f"bench-{uuid.uuid4().hex}", "operation": "prepare_scenario",
             "arguments": {"base_scenario_ref": ref, "proposed_edits": proposed}},
        )
        if code == 200:
            args = {
                "base_scenario_ref": ref,
                "alternative_scenario_ref": {"scenario_id": hyp["scenario_id"], "revision": hyp["revision"], "scope": "hypothetical"},
                "layout_refs": [layout_ref], "mode": "fixed_layout",
            }
            out["compare_scenarios"] = measure("compare_scenarios", args, max(1, runs // 2))
            out["compare_scenarios"]["accepted_revision_unchanged"] = head_scenario(api)[0] == ref
        else:
            out["compare_scenarios"] = {"skipped": f"prepare_scenario HTTP {code} {hyp.get('code')}"}
    return out


def raw_inference(status, runs, thinking, reasoning_effort):
    """Streamed chat completions to the server's own loopback model URL (same host only)."""
    if not (status.get("configured") and status.get("reachable") and status.get("model_listed")):
        return {"skipped": status.get("reason") or "no reachable model configured"}
    url = status["model_base_url"].rstrip("/") + "/chat/completions"
    payload = {
        "model": status["model"], "stream": True, "max_tokens": 128, "temperature": 0,
        "stream_options": {"include_usage": True},
        "messages": [{"role": "user", "content": "In one sentence, what does a tree's shade do on a hot day?"}],
    }
    if thinking is not None:
        payload["chat_template_kwargs"] = {"enable_thinking": thinking}
    if reasoning_effort:
        payload["reasoning_effort"] = reasoning_effort
    samples = []
    for i in range(runs):
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        t0 = time.perf_counter()
        ttft, tokens, chunks, error = None, None, 0, None
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                for raw in r:
                    line = raw.decode("utf-8", "replace").strip()
                    if not line.startswith("data:") or line.endswith("[DONE]"):
                        continue
                    event = json.loads(line[5:])
                    for choice in event.get("choices") or []:
                        delta = choice.get("delta") or {}
                        if delta.get("content") or delta.get("reasoning_content") or delta.get("reasoning"):
                            chunks += 1
                            if ttft is None:
                                ttft = time.perf_counter() - t0
                    if event.get("usage"):
                        tokens = event["usage"].get("completion_tokens")
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"[:200]
        total = time.perf_counter() - t0
        gen = total - ttft if ttft is not None else None
        samples.append({
            "index": i, "total_s": total, "ttft_s": ttft, "completion_tokens": tokens, "chunks": chunks,
            "tokens_per_s_after_first_token": (tokens / gen) if tokens and gen and gen > 0 else None, "error": error,
        })
    ok = [s for s in samples if not s["error"]]
    warm = [s for s in samples[1:] if not s["error"]]
    return {
        "model": status["model"], "model_base_url": status["model_base_url"], "attempts": runs, "success": len(ok),
        "request": {"max_tokens": 128, "tools": False, "enable_thinking": thinking, "reasoning_effort": reasoning_effort},
        "first_call": samples[0] if samples else None,
        "first_call_note": "first request from this script; a true cold start only if the model was just loaded",
        "warm_total_s": dist([s["total_s"] for s in warm]),
        "warm_ttft_s": dist([s["ttft_s"] for s in warm]),
        "warm_tokens_per_s_after_first_token": dist([s["tokens_per_s_after_first_token"] for s in warm]),
        "errors": sorted({s["error"] for s in samples if s["error"]}),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--api", default="http://127.0.0.1:8765")
    parser.add_argument("--out", required=True)
    parser.add_argument("--det-runs", type=int, default=10)
    parser.add_argument("--inference-runs", type=int, default=6)
    parser.add_argument("--enable-thinking", choices=("true", "false"), default=None)
    parser.add_argument("--reasoning-effort", default=None)
    args = parser.parse_args()
    api = Api(args.api)
    receipt = {"kind": "canopy-bench/2", "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "complete": False}

    def flush():
        with open(args.out, "w") as handle:
            json.dump(receipt, handle, indent=2)

    if api.call("GET", "/api/v1/health")[0] != 200:
        receipt["error"] = "server unreachable"
        flush()
        print("FAIL server unreachable at", args.api)
        return 2
    receipt["environment"] = environment(api)
    flush()
    failed = False
    try:
        ref, scenario = head_scenario(api)
        receipt["scenario_ref"] = ref
        print(f"machine {receipt['environment']['machine']} · commit {receipt['environment']['bundle_commit']} · scenario rev {ref['revision']}")
        receipt["deterministic"] = deterministic(api, ref, scenario, args.det_runs)
    except Exception as exc:
        receipt["deterministic"] = {"error": f"{type(exc).__name__}: {exc}"[:300]}
        failed = True
    flush()
    for op, r in receipt["deterministic"].items():
        if isinstance(r, dict) and "wall_s" in r:
            failed = failed or r["success"] != r["attempts"]
            print(f"  {op:18} {r['success']}/{r['attempts']} ok  wall_s {r['wall_s']}  first {r['wall_s_first']}")
        elif isinstance(r, dict):
            print(f"  {op:18} {r}")
    sampler = MemorySampler()
    sampler.start()
    thinking = None if args.enable_thinking is None else args.enable_thinking == "true"
    try:
        receipt["raw_inference"] = raw_inference(
            receipt["environment"]["agent_status"], args.inference_runs, thinking, args.reasoning_effort
        )
    except Exception as exc:
        receipt["raw_inference"] = {"error": f"{type(exc).__name__}: {exc}"[:300]}
    sampler.stop_event.set()
    raw = receipt["raw_inference"]
    if "skipped" in raw:
        print("  raw inference      skipped:", raw["skipped"])
    else:
        failed = failed or not raw.get("success")
        print("  raw inference     ", {k: v for k, v in raw.items() if k not in ("first_call", "request")})
    receipt["memory_during_model_phase"] = {
        "host_samples": sampler.host_samples, "gpu_samples": sampler.gpu_samples,
        "min_mem_available_bytes": sampler.min_available, "max_gpu_memory_used_mib": sampler.max_gpu_mib,
        "note": "1 s sampling of /proc/meminfo and nvidia-smi; on unified-memory devices read both",
    }
    print("  memory            ", receipt["memory_during_model_phase"])
    receipt["limits"] = [
        "Synthetic authored site with a fixed catalogue; candidate-count scaling is not exercised over HTTP.",
        "Sequential load only; no concurrency or GPU stress.",
        "Raw inference uses a short prompt without tools; agent turns carry far larger prompts (see agent_eval).",
        "Agent success, tool correctness and evidence are measured by backend/tests/benchmarks/agent_eval.py, not here.",
    ]
    receipt["complete"] = True
    flush()
    print("receipt:", args.out)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
