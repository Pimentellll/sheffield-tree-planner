# Architecture and limits for the video

**Revised 13 Nov 2026 (issue #57 reconciliation):** checked against `origin/main` `ca1662d`, PR #70 @ `8d24e73`, PR #71 @ `d9f1586` and the branches listed in [README §Reconciliation](README.md#reconciliation-after-ca1662d-13-nov). Nothing was executed.

**For:** Alex (diagram, limitations card and on-screen labels for #58). Judges see it only through the video. **Status:** prepared from read-only inspection of the code and refs named below. No model, test, server, build or benchmark was run to write it, and nothing here is a result. Every claim it allows must also match a row in the [claims ledger](EVIDENCE_AND_CLAIMS_LEDGER.md). It replaces the architecture text in [brief §5](JUDGING_AND_SUBMISSION_BRIEF.md#5-architecture-text-for-a-diagram).

**How to read the "Where it exists" column.** **On main** = present on `origin/main` `ca1662d` (path:line given). **Branch-only** = present only on a named branch or draft PR, not merged, not tested on the Spark. **Issue-reported** = Ben reported it in issue #54. Arnav has not verified it, so call it "reported", never "verified". **Planned** = specified in an issue or PR text only. Before filming, re-label every box from the **release SHA** Ben hands over. A branch-only or planned box becomes a plain box only when the release SHA contains it and the acceptance rows named in its label are `verified`.

## 1. Components

| Component | What it does | Where it exists | May appear in the diagram as | Required label |
|---|---|---|---|---|
| Workbench UI | Browser app: scene, proposed tree, accepted budget, jobs and the result evidence chain | **On main:** `frontend/` (React 19.2.0, three 0.181.0: `frontend/package.json` L16, L18). Served either by the Vite dev server with a dev proxy (`frontend/README.md` L9; `frontend/vite.config.ts` L35–43) or from one origin by `physical_server.py --frontend-dist` (`backend/src/tree_planner/evaluators/physical_server.py` L21, L29–33). On main, no screen shows an agent: `frontend/src/panels/CompareScreen.tsx` L236 says "This backend exposes no planning-agent endpoint yet" | "CANOPY workbench (React + Three.js)" | A synthetic-site label in frame whenever results are shown: the UI's own "Synthetic test site: not Sheffield" / "SYNTHETIC TEST SITE", or the caption in §6 (ledger S-08; brief §3) |
| Backend API and typed contracts | Typed scenario revisions, source/rights records, human acceptance and a domain-operation endpoint. It binds to 127.0.0.1 only | **On main:** `api/app.py` L295–435 (health, version, sources, assets, sites, profiles, layouts, scenarios, `POST /api/v1/scenarios/accept` L386, `POST /api/v1/operations` L394, jobs, results). There is **no agent route**. Loopback bind: `physical_server.py` L35 | "FastAPI /api/v1 (127.0.0.1)" | — |
| Server-side scope policy | `/api/v1/operations` runs through `AgentDispatcher`, which pins the accepted task and rejects budget or constraint widening server-side | **On main:** `api/service.py` L283 (`AgentDispatcher`), L311/L320 (`validate_analysis`), L328/L340 (`validate_preparation`); `agents/policy.py` L19, L32 | "Operations dispatcher + policy (scope checks)" | Ledger G-02: "The agent can investigate but cannot change the accepted budget or approve a plan" |
| Job service | Asynchronous jobs in SQLite, current-selection slots, stale-result fencing | **On main:** `jobs/__init__.py` L6, L292 (SQLite), L281 (`job_selections`), L487–490 (superseded on new revision), L519–549 (`current()` identity check). Worker supervision is open in **#72** (a clock-regression worker failure was reported from a local run, not reproduced on the DGX) | "Job service (SQLite, stale-result fencing)" | Ledger G-06: say "stale results are rejected" only if acceptance A-06 has evidence |
| Deterministic CPU engine | pvlib SPA sun position → ray–crown shading on receivers → additional shade in m²·h → finite-catalogue search, re-checked by an independent constraint checker | **On main:** `physics/solar.py` L143 (`pvlib.solarposition.spa_python`); `physics/ray.py` L37 (`ellipsoid_path_length`); `physics/evaluator.py` L27 (`EVALUATOR = "canopy-cpu-reference"`); `search/__init__.py` L468 (`search`), L191 (`check`); objectives `contracts/scenario.py` L139 (`maximise_shade_under_budget`, `minimise_cost_for_target`; ledger O-06) | "CPU numerical engine (canopy-cpu-reference)" | "CPU numerical engine". No GPU arrow (ledger H-02). "Best evaluated layout among the catalogue positions", not "optimal" (ledger O-01) |
| AgentLoop (planning agent) | Host-controlled loop: typed tool schemas, argument checks, job polling, identity/currentness check, host summary built from stored Results | **On main as a library only:** `agents/__init__.py` L288 (`AgentLoop`), L61 (`ClientConfig`), L120 (`LocalClient`); `agents/http.py` L25 (`HTTPDispatcher`, which calls `/api/v1/operations` over loopback). The only code that constructs it is tests: `backend/tests/agents/test_live_failures.py` L52, `test_live_local.py` L144 (opt-in: skips unless `CANOPY_LOCAL_MODEL_BASE`, `CANOPY_LOCAL_MODEL` and `CANOPY_NUMERICS_SOURCE` are set, L76–80), `test_protocol.py` L131, `test_summary.py` L55. No backend route and no browser control starts it. There is no five-case driver on main (#63, FIX-2) | Today: "Agent loop (library; run from a host test/driver)", drawn **outside** the FastAPI box | Ledger G-01 (figures come from stored results). Outcome values, ledger G-11: `completed`, `needs_evidence`, `draft_prepared`, `metadata_only`, `stopped`, `exhausted`, `failed` (`agents/__init__.py` L503–632) |
| Agent-run API and agent panel | Starts and reads agent runs from the browser | **Branch-only:** reference branch `ref/arnav/integration-spark-demo` @ `6ff381e` (the same commit as Arnav's local `integration/arnav/spark-demo`). It was published at 13:51 as a reference with no PR (#54) and branches from `demo/hackathon` `4d89113` (an older ancestor of main), not from `ca1662d`. Routes `/api/v1/agent/status`, `/api/v1/agent/runs`, `/api/v1/agent/runs/{run_id}`, `/api/v1/agent/runs/{run_id}/stop` (`api/app.py` L456–470 @ `6ff381e`); `<AgentPanel>` (`frontend/src/App.tsx` L86 @ `6ff381e`). **Planned:** #73 specifies `POST /api/v1/agent-runs` with `/cancel` (PR #70 @ `8d24e73` L65–76), and #54 treats the reference branch as superseded by #73 | Only if the release SHA serves it, under the route spelling that SHA actually uses | Ledger G-08. If the release has no agent route, label the agent path "evaluation driver, not in the browser UI" |
| Model transport and runtime | Sends messages and tool schemas to the model and returns its tool calls | **On main:** `LocalClient` speaks only the OpenAI-style `/v1` route (`agents/__init__.py` L88 requires a base URL ending `/v1`, L172 posts `/chat/completions`). **Planned / issue-reported:** organiser-supplied Ollama on the Spark at 127.0.0.1:11434 (`docs/EVENT_DAY_EXECUTION_2026-11-13.md` L200). Ben is moving to a native `/api/chat` client with a normaliser and keeping `/v1` as the fallback (PR #70 @ `8d24e73` R03 L32, R25 L54, §9 L147–168). That adapter is **not published** on any ref. Whatever client ships must keep main's locality guards: loopback HTTP host only and no proxy or redirects (`agents/__init__.py` L73–90, L167–168). The committed `deploy/spark/model-profile.json` is a **vLLM** profile with `"status": "candidate_not_device_tested"` (L2), and `inference.compose.yml` L7 is a vLLM image. `application.env.example` L1 says "NOT loaded by an implemented backend yet" | Conditional diagram only: "organiser Ollama on the Spark (127.0.0.1:11434), model = exact `ollama ps` tag". **Never draw vLLM** | "Local model" only once ledger H-01 is approved (acceptance X-01, X-02). Name the transport that ran (`/api/chat` or `/v1`). Add "≤ 8,192 tokens per request" only under ledger H-06 (acceptance X-06) |
| DGX Spark baseline | Ben's reported deployment of a main-line release on the Spark | **Issue-reported in #54 (Ben):** release `d806d45` (an ancestor of `ca1662d`) was installed on DGX ARM64 and served through SSH on loopback, and a browser click produced a stored Result. Ben also reported a single native-Ollama **chat-only** smoke test of `nemotron-3.5-lightning:30b`, "**not** a domain-tool invocation". Arnav has not verified any of this | "DGX Spark (reported by Ben, #54)" | Ledger D-04 (issue-reported baseline; still SE pending). Ledger H-07: describe the Ollama result only as "a chat-only smoke test of `<tag>` on the Spark", never as the agent running |
| SSH tunnel / loopback topology | The laptop reaches loopback-only services on the Spark through SSH local forwards | **On main:** `deploy/spark/ssh_config.example` (host settings only; it defines no forward, L1 "Example only", L16 `ExitOnForwardFailure yes`). Forwards are documented in `docs/EVENT_DAY_EXECUTION_2026-11-13.md` L200 (organiser recipe: laptop 11435 → Spark 11434) and `docs/DGX_SPARK.md` L81 (older vLLM-era ports 8001/8080). The `canopyctl` launcher is **branch-only** (`6ff381e`) | "SSH tunnel (loopback only)" | Ledger H-03: a loopback URL is also what a tunnel presents, so "same machine" comes from X-01 captured on the agent host, not from the URL check |
| Real terrain context view (Weston Park) | Shows Environment Agency 1 m LiDAR of Weston Park on the Sheffield sites screen, view-only | **Branch-only:** `feat/alex/terrain-context-view` @ `b1bb0e5` and `feat/alex/design-parity` @ `a130bbd` (`OverviewScreen.tsx` L41 / L53); not an ancestor of main. The files are served **only by Vite dev-server middleware** (`frontend/vite.config.ts` L12, L18, L31 @ `b1bb0e5`, reading `CANOPY_TERRAIN_DIR`), so a built release shows nothing. Tag "VIEW ONLY · NOT ANALYSED" (`TerrainView.tsx` L168); "This surface is not loaded into the planner and no shade result refers to it" (L191) | "Terrain context (view only; dev server)". **Not** a backend component and **not** connected to the engine | Ledger W-01, W-04: tag in frame, "© Environment Agency copyright and/or database right 2022. All rights reserved." + "Open Government Licence v3.0" (`frontend/scripts/prepare_terrain.py` L34–35), "© OpenStreetMap contributors" for the discovery box (L143). **Decided 13 Nov: not filmed** (S-08 option A); treat it as "not on release" until the release SHA contains it |
| Agent evidence UI | Agent run history, Job → Result chain and an untrusted-narrative guard in the UI | **Planned / untested:** #74; draft PR #76 (`feat/arnav/agent-evidence-74` @ `c6a8b8f`, helpers only; green in GitHub-hosted CI only, never run against a live agent; its narrative guard misses forms such as "3C" or "1,5 °C"); design plan PR #71 @ `d9f1586`. Alex's `design-parity` `App.tsx` L148–152 holds a static "No agent endpoint on this backend yet" card in the same slot | Do not draw | Ledger G-08, G-12 |
| Compact model-facing observations | Keeps each model request within the context limit | **Planned / untested:** #68; draft PR #75 (`feat/arnav/observation-views-68` @ `2dc4c3f`; no completed CI run at this revision) | Do not draw | Ledger G-10, G-12 |

**Do not draw at all:** vLLM or the `deploy/spark/` inference container (ledger H-05); any GPU physics (H-02); NIM, TensorRT-LLM, NeMo, Warp, cuOpt; more than one agent (G-04); a 3D city mesh, tree identification or a map-first "City Explorer" (#66/#67 are specifications only; ledger W-03); a recorded street-tree inventory or tree count (#69, draft PR #77: CI-green on synthetic fixtures only, no real data acquired, rights `unknown` for all purposes; ledger W-02); "Optimisation Studio" or "Urban Intelligence" screens (draft PR #78 is a design reference with example figures only; nothing in it is a result).

## 2. Diagrams

### A. Shown today (on main `ca1662d`)

```text
 Laptop                                 Release host: DGX Spark per #54 (reported by Ben, not verified by Arnav)
 ┌───────────────────────────┐          ┌───────────────────────────────────────────────────────────────────────┐
 │ Browser                   │  SSH     │ everything bound to 127.0.0.1                                         │
 │ CANOPY workbench          │─tunnel──▶│ [FastAPI /api/v1: typed contracts, scenario revisions, rights records] │
 │ (React + Three.js)        │ loopback │   ├─ POST /scenarios/accept ........ human only (the agent has no      │
 └───────────────────────────┘          │   │                                  accept tool)                      │
                                        │   ├─ POST /operations → dispatcher + policy.py (scope checks)          │
                                        │   └─ Job service (SQLite jobs, selection slots, stale-result fencing)  │
                                        │         └─ CPU numerical engine (canopy-cpu-reference):                │
                                        │              pvlib SPA sun → ray–crown shading → m²·h                  │
                                        │              → finite-catalogue search + independent checker           │
                                        └───────────────────────────────────────────────────────────────────────┘

 [Agent loop: library on main; run only by opt-in tests] ──loopback HTTP──▶ /api/v1/operations, /jobs, /results
 No browser→agent arrow. No model box. No GPU-physics arrow. No vLLM.
```

### B. If the Spark release contains the agent route (conditional)

Use this only if the release SHA serves an agent-run route **and** the boxes marked `*` are on that SHA. If they are not, keep diagram A and add the agent as a separate box labelled "evaluation driver, not in the browser UI" that calls `AgentLoop → HTTPDispatcher → /api/v1/operations`.

```text
 [Browser: workbench + agent panel*] ──SSH tunnel (loopback)──▶ [DGX Spark, 127.0.0.1]
                                                                 ├─ FastAPI /api/v1 + job service + CPU numerical engine (as in A)
                                                                 └─ agent-run route*  (the spelling the release serves:
                                                                    /api/v1/agent-runs per #73, or /api/v1/agent/runs on the ref branch)
                                                                      └─ Agent loop (host-controlled)
                                                                           ├─ tool schemas: only the tools the host exposed (say how many)
                                                                           ├─ transport*: native /api/chat + normaliser | /v1 fallback
                                                                           │     └─▶ [organiser Ollama 127.0.0.1:11434, <exact `ollama ps` tag>]
                                                                           │         label "local model" only if ledger H-01 is approved
                                                                           └─ tool call → validate → HTTPDispatcher ──loopback──▶ /api/v1/operations
                                                                                → job → poll → identity/currentness check
                                                                                → host summary from stored Results
 Human: accepts scenarios in the UI and decides; the agent can only investigate.
 * draw only if present on the release SHA.  CPU numerical engine; no GPU-physics arrow; no vLLM.
```

## 3. Agent footage rules

- **Source.** On main `ca1662d` the UI has no agent panel (`CompareScreen.tsx` L236). Unless the release SHA has a panel, film the terminal receipt instead: raw `tool_calls`, `job_id`, Result `run_id`, `ollama ps`. Label it "terminal capture of the same run".
- **Model field.** On the reference branch the panel shows whatever `LLM_MODEL` is set to (`Agent.tsx` L134 @ `6ff381e`). That branch's `deploy/spark/application.env.example` L14–17 defaults to the vLLM alias `tree-planner-local` at `127.0.0.1:8000/v1`. If the panel reads `tree-planner-local`, the footage is not Ollama/Nemotron evidence. It must read the exact `ollama ps` tag.
- **Tool choice.** The reference panel defaults to an evaluate-only tool set (`Agent.tsx` L20, L70). Say "the model issued a tool call from the N tools the host exposed". Cite ledger M-01 ("chooses which tool") only from the five-case run with the four-tool set (acceptance A-01). A run that exposed only `evaluate_layout` supports "the model called the evaluate tool", not "chose a tool".
- **Not one of the five tests.** Panel runs use a different host context, a 420 s deadline, a 180 s completion timeout and up to one host-inserted format-repair turn (`agents/runs.py` L81–86, L598 @ `6ff381e`). Never narrate panel footage as "one of our five tests".
- **"Format repair" tag** (ledger G-09). When the panel shows "· 1 format repair", the model's final reply was malformed, so the host appended a fixed instruction and asked again (`runs.py` L47–51, L589–599 @ `6ff381e`). That run is host-assisted. Do not present it as an unassisted model success.
- **Contradicting footer.** The reference branch mounts the agent panel but its Compare screen still says "This backend exposes no planning-agent endpoint yet" (`CompareScreen.tsx` L236 @ `6ff381e`). Do not film that footer on such a build until the text is fixed.
- **Failure on camera.** Keep the failure visible or cut to the deterministic workflow. Never narrate a tool call that did not happen.

## 4. What the seeded demo scene contains

Source: `backend/src/tree_planner/evaluators/physical_seed.py` on main `ca1662d`. These are authored synthetic inputs, not results.

| Item | Value | Line |
|---|---|---|
| Site | `synthetic-physical-v1`, `site_kind="synthetic_test"`, origin 53.38° N, 1.47° W (Sheffield's latitude); real-site import is rejected (`site/import_pipeline.py` L148–149) | L64, L78, L80 |
| Ground | Flat, z = 0 (non-null terrain is unsupported: `physics/README.md` L22) | L19 |
| Buildings | **None** (`"triangles": []`) | L32 |
| Existing trees | **None** (scene and site bundle) | L33, L121 |
| Target | 13 × 15 = 195 receiver samples of 0.25 m² = 48.75 m², target weight 2 | L20–31, L218 |
| Candidates | Three catalogue positions at x = 0, −2, +2 m; the proposed layout is one tree at candidate-1 (x = 0) | L50–60, L190–207 |
| Tree geometry | Assumed: mature crown centre 4 m, radii 2/2/2.5 m, opaque; establishment crown centre 1.5 m, radius 0.5 m | L151–167 |
| Cost and budget | £100 per tree (10,000 pence, "Assumed upfront test cost"); budget £200 (20,000 pence); at most 2 trees | L182–183, L242, L244 |
| Spacing | Minimum 2 m between centres. Neighbouring positions are exactly 2 m apart and the check fails only below 2 m (`search/__init__.py` L261), so spacing cannot bind on this catalogue | L250 |
| Time bins | `summer` (mature, year 20) and `establishment` (year 1): one sun position at 2026-07-01 12:00 UTC, counted for 1 h | L217, L224–225 |
| Winter case | Exists **only** if the runtime was seeded with `winter=True`, i.e. the server was started with `--winter` (`physical_server.py` L20, L28; used in `README.md` L53/L66 and `frontend/README.md` L9). If present: 2026-12-01 12:00 UTC, 1 h, leaf-off transmission 0.7 assumed, limit 100 m²·h. Check that the accepted scenario lists a `winter` case before filming it | L169–174, L227–228, L259–261 |
| Can the winter limit bind? | **No.** The largest possible loss is 195 × 0.25 m² × 1 h = 48.75 m²·h, below 100 m²·h. Say "checked and passing", not "limited the choice" (ledger S-06) | — |
| Objective and engine | `maximise_shade_under_budget` on `summer`; `canopy-cpu-reference` `takeover-v1`, `pvlib-spa-geometric` 0.15.2, 0.5 m receiver spacing; search `overlap-greedy-local` | L264–281 |

Because the scene has no buildings and no existing trees, its baseline is unobstructed sky. No demo number can show existing shade being discounted. Say "the method discounts shade that buildings and existing trees already provide" as how the method works, not as something the demo shows (ledger I-02, S-01).

## 5. Limitations card (closing text)

> **Today:** synthetic test geometry on flat ground, with no buildings or existing trees in the demo scene; one sun position per case (12:00 UTC on 1 July; 1 December for the leaf-off winter check), counted for one hour; assumed crown sizes, leaf-off transmission and costs; three-candidate catalogue; CPU engine; **[if the five-case run completed:** "five recorded agent tests (k/5) on one synthetic scenario"**; otherwise:** "the five required agent tests were not completed on the Spark"**]**; no field validation; no temperature, energy, carbon, air-quality, flood or financial predictions; utilities, soil and permissions remain survey-required.

- Drop "1 December for the leaf-off winter check" if the filmed release has no `winter` case.
- Do not mention real Weston Park LiDAR: the terrain view is not filmed (decided 13 Nov, S-08 option A). Fallback only if that decision changes: append "Real Weston Park LiDAR appears only as an unanalysed view."
- The runtime's own limitation strings (`physical_runtime.py` L572–575) must not be softened (acceptance N-10).

## 6. Labels and attributions to show

| When | Label | Ledger / acceptance |
|---|---|---|
| Any computed result on screen | The UI's own "Synthetic test site: not Sheffield" / "SYNTHETIC TEST SITE" label in frame; if cropped, the caption "Synthetic geometry at Sheffield's latitude — not a surveyed site" | S-08 |
| Once, near the first shade number | "Computed direct-sun shade — not a temperature prediction" | S-03, S-09 |
| Narration of the setting | **Decided 13 Nov — (A):** "Shade results are computed on synthetic test geometry at Sheffield's latitude". (B), fallback only if the decision changes and W-01 is on the release SHA: "Every shade result is computed on synthetic test geometry. The Sheffield sites screen also shows a view-only Environment Agency LiDAR context of Weston Park; it is not used in any calculation." **Never** "real Sheffield site" | S-08, W-01 |
| Terrain view in frame (not filmed per the 13 Nov decision; fallback only) | "VIEW ONLY · NOT ANALYSED" tag, plus "© Environment Agency copyright and/or database right 2022. All rights reserved." and "Open Government Licence v3.0"; "© OpenStreetMap contributors" if the discovery box is visible (in frame or in the end credits) | W-01, W-04 |
| Engine box or narration | "CPU numerical engine"; never GPU physics | H-02 |
| Model | The exact `ollama ps` tag (base tag if an alias was used) and the transport used; "local model on our DGX Spark" only after H-01 is approved | H-01, X-01, X-02 |
| Terminal footage of an agent run | "terminal capture of the same run" | G-01 |
| Partial-outcome variant | Agent design shown as "design", not "demonstrated" | — |
| Search result | "best evaluated layout among the catalogue positions" | O-01 |

## 7. IDs on screen

Two different IDs can both appear as "run", and they must not be confused (#73; PR #70 @ `8d24e73` L81: "never alias them").

| ID | What it identifies | Where it appears | Use as evidence? |
|---|---|---|---|
| Result `run_id` | One numerical computation (a stored Result) | `GET /api/v1/results/{run_id}` (`api/app.py` L435); in the reference panel as "run …" against each tool call (`Agent.tsx` L146 @ `6ff381e`) | **Yes.** This is the ID that "every number comes from a stored Result" refers to. Record it in the ledger's evidence register |
| `agent_run_id` (agent session) | One agent investigation, which may contain several jobs | Specified by #73 / PR #70 @ `8d24e73` L65–81. On the reference branch it is a uuid4 hex stored in a field confusingly named `run_id` (`agents/runs.py` L207, L410 @ `6ff381e`) and shown in the panel header as "Run …" (`Agent.tsx` L134) | Only as the session identifier. Never present it as a Result `run_id` |
| `job_id` | One asynchronous job | `GET /api/v1/jobs/{job_id}` (`api/app.py` L422). The reference panel shows job **status** only (`Agent.tsx` L146), although `runs.py` L174 carries `job_id` | Take it from the run record or terminal receipt |

When a run's IDs are recorded, say which kind each one is (`run_id` or `agent_run_id`) in the ledger's evidence register.
