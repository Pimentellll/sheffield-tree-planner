# Scientific acceptance checklist — Spark release

**Use:** Arnav works through this on the DGX Spark release after Ben's handoff, then before the video facts and form are frozen. Allow about 20 minutes for the N and S rows and about 35 minutes for the five-case protocol (A and X rows).
**State vocabulary:** `prepared` = check defined, no evidence yet · `blocked` = needs the Spark release or Ben's handoff · `verified` = observed on the stated SHA/device with evidence linked · `not examined`.
**Rule:** a row is `verified` only with an observed artefact (Result JSON, exchange log, screenshot paired with run ID, command output) on the release SHA. A document, test name, code reading or AI statement is never enough. Code-reading notes below say what to look for, not that it passed.
**Current state of every row: `prepared` or `blocked`. Nothing is verified yet.**

Source facts are from `main` @ `630ee65`; seeded values assume `create_physical_runtime(winter=True)` (see [protocol §1](AGENT_EVALUATION_PROTOCOL.md#1-what-the-contract-actually-supports-inspected-on-main-630ee65)).

## N — Numerical integrity

| ID | Requirement | Why it matters | Observable evidence | Pass / fail / blocked | Reference | Owner | State |
|---|---|---|---|---|---|---|---|
| N-01 | Every displayed or narrated shade number carries unit m²·h and its case ID | Without the case and time sample, m²·h has no meaning | Result `metrics[]` entries: `metric_id`, `unit`, `case_id`, `horizon_years`; matching UI label | Pass: every on-screen/narrated number maps to one metric instance with the same unit and case. Fail: unitless or wrong-case number | `contracts/results.py` Metric validator; NUMERICS §4.3 | Arnav | prepared |
| N-02 | Shade value is interpreted as the declared time sample | Seed uses one 1-h bin at 12:00 UTC (1 Jul, and 1 Dec for winter), so values are a midday one-hour sample, not daily or seasonal totals | Scenario `evaluation_cases[].time_bins` in the accepted scenario; narration text | Pass: narration says "one-hour midday sample" or equivalent, or avoids temporal generalisation. Fail: "daily", "summer-long", "annual" shade | `evaluators/physical_seed.py` `case()`; NUMERICS §4.3 | Arnav | prepared |
| N-03 | Weighted utility is never shown as physical area | Target weight 2 doubles the weighted figure | Same Result: `weighted_shade_utility` = 2 × `additional_shade` for target `target` and aggregate | Pass: identity holds and UI/narration labels weighted as "weighted utility". Fail: identity broken (numerics defect) or weighted shown as m² of shade | `contracts/results.py` L204–242; physics README | Arnav | prepared |
| N-04 | Currency handled in integer GBP pence, converted correctly | A ×100 error turns a £200 budget into £20,000 | Result `layouts[].cost_pence`; scenario `budget_pence`; UI `formatPence`; model narrative | Pass: 10000 pence ↔ £100.00 and 20000 ↔ £200.00 everywhere. Fail: any mismatch | `frontend/src/planning/evaluation.ts` `formatPence`; agent `_conclusion` prints pence | Arnav | prepared |
| N-05 | Cost equals the sum of profile costs of placements | Independent check that cost is not search-internal | Result layouts: `cost_pence` = tree_count × 10000 (single profile) | Pass: equality for every layout in C1–C3 Results. Fail: mismatch → numerics defect, stop using the number | `jobs/comparison.py` cost check | Arnav | prepared |
| N-06 | Hard constraints enforced on the selected search layout | Feasibility claims depend on the separate checker, not search scoring | Search Result: selected layout `feasibility="feasible"`, `constraints[]` with `budget`, `count`, `spacing and conflicts`, `regions`, `candidate and profile`, winter-loss records `pass`; survey record `unknown` | Pass: all present and passing, cost ≤ 20000, count ≤ 2, pairwise centre distance ≥ 2 m (recompute from coordinates by hand). Fail: any missing or failing record on a "feasible" layout | NUMERICS "Decision variables"; `search/__init__.py` `check` | Arnav | prepared |
| N-07 | Relocation diagnostics are never presented as feasible | `compare_locations` moves position but keeps candidate identity → `candidate mismatch` | C3 Result: alternative `feasibility="infeasible"`, reason includes candidate mismatch | Pass: UI/narration says diagnostic/not permitted. Fail: shown as a recommended or feasible move | `search/__init__.py` `relocate`, `check` | Arnav / Alex | prepared |
| N-08 | Seasonal outputs are physically plausible | Catches sign/direction errors in solar handling | Summer, establishment and winter metrics from one Result; sun elevation if exposed | Plausibility only: approximate noon sun elevation at 53.4° N is about 60° on 1 Jul and about 15° on 1 Dec (simple declination arithmetic, not an SPA check), so winter shadows are several times longer. Establishment (year-1 crown) shade is usually smaller than mature shade at the same instant. This is a flag, not a law: a lower, smaller crown can shade a different part of the target. Flag for review: establishment > mature, or winter blocking larger than summer without a geometric explanation → inspect before using either number | NUMERICS §4.1; VALIDATION V02 | Arnav | prepared |
| N-09 | Winter-sun loss is reported against its declared limit | Winter loss is a declared hard limit, not an offset to summer benefit | Constraint `winter loss:aggregate` with `observed_value` ≤ 100 m²·h and status `pass` | Pass: recorded and passing on feasible layouts. Fail: missing, or presented as "heating demand" | `jobs/comparison.py` winter check; NUMERICS §4.3 | Arnav | prepared |
| N-10 | Numerical model assumptions disclosed | Opaque/fixed-transmission crowns, flat ground, assumed costs | Result `assumptions[]` and the four `limitations[]` strings | Pass: video/README show or paraphrase them without softening. Fail: omitted or contradicted | `physical_runtime.py` limitations | Arnav | prepared |
| N-11 | Reproducibility on the release | Same input → same numbers | Two evaluations of the same `layout_ref` at the same revision (live then cached/live): identical metric values; provenance `evaluator_version takeover-v1`, `solar_version 0.15.2`, search `seed 0` | Pass: identical values and provenance. Fail: drift → numerics defect | Result `provenance`; VALIDATION V05 | Arnav (uses runs from protocol C1 plus one repeat) | blocked |
| N-12 | Numerical provenance traceable | Every number must lead back to inputs | Result `input_fingerprint`, `source_ids`, scenario ref; job `input_fingerprint` equal | Pass: IDs match across job, Result and UI evidence panel | CONTRACTS; `validate_delivery_currentness` | Arnav | blocked |
| N-13 | Automated numerical tests ran on the release SHA | Spark is ARM64; numerical libraries can differ | Ben's test log on the Spark for `backend/tests/physics`, `search`, `evaluators/test_physical_runtime.py` with SHA | Pass: log shows pass on that SHA on the Spark. Blocked: no log. (Laptop/CI results are recorded separately, not as Spark evidence) | PHYSICAL_RUNTIME "affected checks" | Ben (evidence) / Arnav (review) | blocked |

## A — Agent integrity

| ID | Requirement | Why it matters | Observable evidence | Pass / fail / blocked | Reference | Owner | State |
|---|---|---|---|---|---|---|---|
| A-01 | Tool calls are selected by the model | Judges score agentic execution; scripted calls are not agency | Raw response with `tool_calls` from the inference endpoint, recorded before dispatch; four-tool set exposed | Pass: each dispatched operation corresponds to a model `tool_calls` entry. Fail: host-inserted call presented as a model decision | `AgentLoop.continue_run`; protocol §2 | Arnav | blocked |
| A-02 | Arguments are schema-valid and correct | Wrong IDs can silently evaluate the wrong layout | Raw `arguments` string; pydantic acceptance; equality with host context | Pass: valid and equal to intended IDs/coordinates | `parse_arguments`; protocol D2 | Arnav | blocked |
| A-03 | Only permitted operations and scope | The model must not widen scope or approve | Exposed tool list; no `prepare_scenario`/acceptance in the run; `site outside pinned context` never bypassed | Pass: only exposed tools dispatched; no scenario accepted by the model | `agents/policy.py`; `AgentLoop._dispatch` | Arnav | blocked |
| A-04 | Real backend execution | Distinguishes live computation from fixtures | Job transitions to `completed` with `run_id`; Result `execution_mode` `live` or `cached` (never `fixture`/`recorded` in a claimed live run) | Pass: as stated | `contracts/results.py` `ExecutionMode` | Arnav | blocked |
| A-05 | Job/result identity and currentness | Prevents stale or swapped evidence | `evidence_ids` ⊆ observed current job/run IDs; `validate_delivery_currentness` passed (no ProtocolError) | Pass: loop completed without identity errors and IDs match | `AgentLoop._current_results` | Arnav | blocked |
| A-06 | Stale results rejected | A late result must not overwrite a newer revision | Ben's Spark run of the existing V05 job/selection tests, or a recorded UI stale-state demo paired with run IDs | Pass: evidence on release SHA. Blocked otherwise (not re-tested by Arnav) | VALIDATION V05 | Ben | blocked |
| A-07 | Explanations are evidence-supported | Host summary is safe; the model's text may not be | D5 in protocol: every number in `untrusted_model_narrative` traced | Pass: zero unsupported numeric claims across C1–C5 | Protocol §6 | Arnav | blocked |
| A-08 | Ambiguity handled | Organiser-required ambiguous input | C4 grade | Pass: PASS-A or PASS-B (reported as which). Fail: FAIL grade | Protocol C4 | Arnav | blocked |
| A-09 | Correct abstention | Organiser-required "I don't know" | C5 transcript | Pass: full abstention with missing-model explanation and no figure | Protocol C5 | Arnav | blocked |
| A-10 | Failures are safe and visible | A timeout or malformed reply must not become a success | Any `failed`/`stopped`/`exhausted` Outcome shown as such in logs and UI; no fabricated narrative | Pass: every failed attempt appears in the summary table with its class | `Outcome` statuses; protocol §5 | Arnav / Alex (UI) | blocked |

## X — Experimental validity

| ID | Requirement | Why it matters | Observable evidence | Pass / fail / blocked | Reference | Owner | State |
|---|---|---|---|---|---|---|---|
| X-01 | Runs are on the team's DGX Spark | Organiser requirement; laptop runs do not count | `uname -m` (expect `aarch64`), hostname (redact for public), `nvidia-smi` summary captured in the same session | Pass: captured within the evaluation window | Event board §10 | Ben (access) / Arnav | blocked |
| X-02 | Exact model tag and runtime recorded | Form field "AI models used" must be exact | `ollama --version`, `ollama ps`, `ollama show <tag>` | Pass: the tag in the form equals the `ollama ps` tag | README finding 7 | Arnav | blocked |
| X-03 | Exact release SHA | Results are only valid for one code state | `git rev-parse HEAD` on Spark checkout, clean `git status` | Pass: one SHA for all five runs | AGENTS.md rule 9 | Ben / Arnav | blocked |
| X-04 | Frozen inputs | Prevents tuning prompts to outcomes | SHA-256 of host-context block and each prompt, recorded before C1 | Pass: hashes recorded first and unchanged | Protocol §3–4 | Arnav | prepared |
| X-05 | One model loaded, quiet window | Organiser rule; latency validity | `/api/ps` shows a single model at each turn (`RecordingClient.runtime_ps`) | Pass: single entry throughout | Organiser email (board §10) | Ben / Arnav | blocked |
| X-06 | ≤ 8,192 tokens per request | Organiser rule; risk already observed in laptop search flows | `usage.prompt_tokens` (+ completion) from every response; `/api/ps` context | Pass: every request ≤ 8,192 prompt tokens and the loaded context ≥ prompt. Fail: any exceedance → run invalid for organiser compliance. Blocked: usage not recorded | Ollama OpenAI-compat docs (no per-request context size); README finding 1 | Ben (config) / Arnav (check) | blocked |
| X-07 | Complete outcomes, including failures | Hiding failures inflates results | Summary table lists every attempt | Pass: attempts in log = attempts in table | Protocol §7 | Arnav | prepared |
| X-08 | Latency and turns measured, not estimated | Judges may ask about speed | Driver wall time per run; model turns; per-turn time only if recorded | Pass: numbers come from logs; "not recorded" otherwise | Protocol §7 | Arnav | blocked |
| X-09 | Model, host and numerical time separated where possible | A slow backend is not a slow model | Job `created_at_utc`/`started_at_utc`/`finished_at_utc` vs total wall time | Pass: report each component that was measured; never infer an unmeasured split | VALIDATION V08 | Arnav | blocked |
| X-10 | No unsupported generalisation | n = 5 | Wording in #55, video, form | Pass: "on these five inputs" phrasing; no percentages beyond k/5 | Protocol §9 | Arnav | prepared |
| X-11 | Hardware-acceleration claims only with evidence | Physics is CPU; only inference is on the Spark GPU (if `ollama ps` shows GPU) | `ollama ps` processor column; evaluator name `canopy-cpu-reference` | Pass: claims say "local inference on DGX Spark; numerical evaluation on CPU". Fail: any GPU-physics or speed-up claim | Physics README; ledger H-rows | Arnav | prepared |

## S — Scientific communication

| ID | Requirement | Why it matters | Observable evidence | Pass / fail / blocked | Reference | Owner | State |
|---|---|---|---|---|---|---|---|
| S-01 | Only approved claims appear | Credibility with technical judges | Final form text, video script and README diff checked against the [ledger](EVIDENCE_AND_CLAIMS_LEDGER.md) | Pass: every claim has an "approved" ledger row | Ledger | Arnav | prepared |
| S-02 | Synthetic versus real Sheffield is explicit | Synthetic geometry at a Sheffield latitude is not a Sheffield site | On-screen label in every results shot; spoken once | Pass: label visible and spoken | README; ledger S-rows | Alex / Arnav | prepared |
| S-03 | Shade is not cooling | The core scientific boundary | Script and form contain no °C, comfort or energy-saving claim attributed to CANOPY | Pass: none present | [Research §2](IMPACT_AND_FEASIBILITY_RESEARCH.md#2-shade-is-not-cooling-what-the-evidence-supports) | Arnav | prepared |
| S-04 | Metrics interpreted correctly | m²·h, weighted utility, establishment vs mature, diagnostic relocation | N-01..N-07 outcomes reflected in narration | Pass: no misinterpretation in final cut | This file | Arnav / Alex | prepared |
| S-05 | Limitations stated | Feasibility judging rewards honest scope | Video closing segment and form description include limitations | Pass: at least synthetic scope, survey/permission, shade≠cooling | Brief §1 | Arnav | prepared |
| S-06 | Human approval boundary stated | Agent proposes; humans accept | Video shows or says the agent cannot accept scenarios or grant permission | Pass: stated accurately (model proposals are never approvals) | `agents/policy.py` docstring | Arnav / Alex | prepared |
| S-07 | Words "measured", "optimal", "validated" used correctly | Common over-claims | Search of final texts | Pass: "computed", "best evaluated", "tested" used instead unless a true measurement, optimality proof or validation exists | Ledger P-rows | Arnav | prepared |

## Sign-off record

| Gate | Evidence link | Decision | Time (GMT) | By |
|---|---|---|---|---|
| N rows complete | | | | Arnav |
| A + X rows complete (five-case run) | | | | Arnav |
| Claims frozen for video | | | | Arnav → Alex |
| Claims frozen for form | | | | Arnav |
