# Event-day science package — CANOPY Sheffield (13 Nov 2026)

**Owner:** Arnav (scientific credibility, independent evaluation, claims, submission copy).
**Status:** documentation **prepared**; nothing in this folder is a test result. No model, test, benchmark or code was run to write it.
**Repository state inspected:** `main` at `630ee651dc6d256dd7980a4f8da3df149d88c1a1` (13 Nov 11:57 UTC), read-only. Branches `release/verified-event-day`, `feat/ben/reconcile-hackathon` and `demo/hackathon` were all **behind `main` with nothing ahead**, so `main` was the newest pushed code at inspection.

| Document | Use it for | Priority |
|---|---|---|
| [SCIENTIFIC_ACCEPTANCE.md](SCIENTIFIC_ACCEPTANCE.md) | The checklist Arnav runs against the Spark release after Ben's handoff | P0 |
| [AGENT_EVALUATION_PROTOCOL.md](AGENT_EVALUATION_PROTOCOL.md) | Five frozen NVIDIA-required model inputs, bound to the real tool contract, with scoring and an evidence template | P0 |
| [EVIDENCE_AND_CLAIMS_LEDGER.md](EVIDENCE_AND_CLAIMS_LEDGER.md) | What may and may not be said in the video, form and README | P0 |
| [JUDGING_AND_SUBMISSION_BRIEF.md](JUDGING_AND_SUBMISSION_BRIEF.md) | Form description (success and partial versions), Alex's fact sheet, narration outline, architecture text, judge Q&A | P0 |
| [ENGINEERING_FIX_PLANS.md](ENGINEERING_FIX_PLANS.md) | Solutions and step-by-step implementation instructions for Ben (FIX-1..4), tracked as GitHub issues assigned to Ben | P0 |
| [five_case_prompts.json](five_case_prompts.json) | Frozen prompts, host-context template, tool set and client settings with SHA-256 hashes, read by FIX-2's driver | P0 |
| [IMPACT_AND_FEASIBILITY_RESEARCH.md](IMPACT_AND_FEASIBILITY_RESEARCH.md) | Sources for the problem, the shade-is-not-cooling boundary, agent-evaluation method and the adoption pathway | P1 |

These documents **extend, not replace**: [event board §9–§12](../../EVENT_DAY_EXECUTION_2026-11-13.md), [content and handoffs](../../EVENT_DAY_CONTENT_AND_CLAUDE_HANDOFFS_2026-11-13.md), [issue index](../../EVENT_DAY_ISSUE_INDEX_2026-11-13.md), [NUMERICS](../../NUMERICS.md), [VALIDATION](../../VALIDATION.md), [SOURCES](../../SOURCES.md) and the [deep research dossier](../../references/DEEP_RESEARCH_DOSSIER.md). [BUILD](../../BUILD.md) stays the canonical engineering record; nothing here edits it.

## Reconciliation matrix

| Area | Already exists (reused) | Implemented on `main`? | Independently evidenced? | Gap this package closes |
|---|---|---|---|---|
| Problem framing (Sheffield Council, Forest Research) | Handoffs §1, dossier §1 | n/a | Public sources, already cited | Adds the 2021 Street Tree Partnership Strategy, UK shade-measurement study and delivery-constraint guidance; one place for the impact story |
| Numerical method | NUMERICS, physics README, PHYSICAL_RUNTIME | Yes: CPU direct-beam evaluator, pvlib SPA, overlap-aware search, separate constraint checker | Unit/integration tests reported on PR #52 (not re-run here); **no Spark run, no real-site validation** | Acceptance checks that tie each number to its unit, time bin and assumption |
| Five model inputs | Board §11 (FIVE-01..05), handoffs §4 | Agent loop yes; **no five-case driver on `main`** | No | Prompts rebound to the actual tool schemas, fixed toolset, corrected expected outcomes, model-vs-host failure rules, evidence template |
| B11 harness | `backend/tests/benchmarks/runner.py`, board §9 audit | Yes (scripted fixed arm only) | Manual and adaptive arms reported blocked | Not extended; the five-case protocol is deliberately separate and small |
| Newer `agent_eval.py`, agent-run manager, `deploy/spark/bench.py` | Mentioned in board §12 | **Not on any pushed branch** | No | Treated as unavailable unless Ben integrates them |
| Agent UI panel | Alex's UI | **No:** `CompareScreen.tsx` states the backend exposes no planning-agent endpoint yet | No | Video plan states what may be filmed in each case |
| Claims control | Handoffs §2/§5 | n/a | n/a | A structured ledger with approved and prohibited wording |
| Form copy | Handoffs §2 | n/a | n/a | Two final versions (Spark success / partial), NVIDIA-technology field rules |

## Findings that need team attention (read first)

1. **The 8,192-token rule cannot be enforced or proven by the current client settings alone.** `LocalClient` posts to the OpenAI-compatible `/v1/chat/completions` route. Ollama documents that this API has no way to set context size, so `num_ctx` cannot be set per request, and the server default may differ from 8,192. The client's input bound is in **bytes** (`max_input_bytes`), and its token bound needs a trusted counter, which no code on `main` configures. **Compliance must be shown from the `usage.prompt_tokens` value in every recorded response being ≤ 8,192, plus the loaded context from `/api/ps`.** Ben owns any fix. → [Acceptance X-06](SCIENTIFIC_ACCEPTANCE.md), [Protocol §5](AGENT_EVALUATION_PROTOCOL.md#5-host-versus-model-failure-classification).
2. **Moving a catalogue tree with `compare_locations` always produces an infeasible diagnostic in the current contract.** `relocate()` keeps the placement's `candidate_id`/`location_id` and moves only its position, so the independent checker records `candidate mismatch`. The old FIVE-03 expectation ("a valid permitted alternative") is therefore wrong. The correct answer is that the moved position is *not* a permitted alternative in this catalogue model. → [Protocol case C3](AGENT_EVALUATION_PROTOCOL.md#c3--compare-an-alternative-placement).
3. **The synthetic "summer shade" is a one-hour, single-instant snapshot.** The seeded scenario has one time bin per case (1 Jul 12:00 UTC, 1 h; winter 1 Dec 12:00 UTC, 1 h). An `additional_shade` value in m²·h is therefore shaded area × 1 h at about solar noon. It is not daily, seasonal or annual shade. The narration must say "a one-hour midday sample" or simply "computed geometric shade for the declared time sample". → [Ledger S-05](EVIDENCE_AND_CLAIMS_LEDGER.md).
4. **Say "computed", not "measured", for shade.** Existing drafts ask the agent for "measured shade". Nothing is measured; the values are computed by the deterministic model on synthetic geometry. The frozen prompts here avoid the word.
5. **Weighted utility is not area.** The seed sets target weight 2, so `weighted_shade_utility` (weighted m²·h) should be exactly 2 × `additional_shade` for the single target. Showing the weighted number as "shade area" would double the apparent benefit. → [Acceptance N-03](SCIENTIFIC_ACCEPTANCE.md).
6. **Watch pence versus pounds.** The agent's host-generated summary prints `cost=… pence` (seed: £100 per tree = 10000 pence; budget £200 = 20000 pence). A model narrative that says "£20,000" is a numerical error. → [Acceptance N-04](SCIENTIFIC_ACCEPTANCE.md).
7. **The committed deployment profile is not the evaluated model.** `deploy/spark/model-profile.json` describes a vLLM container serving the Hugging Face BF16 checkpoint as `tree-planner-local` (status `candidate_not_device_tested`). The organisers supply Ollama tags (`nemotron-3-nano:30b`, `nemotron-3.5-lightning:30b`). The form's model field must come from `ollama ps`/`ollama show` on the Spark, not from that file.
8. **The existing live test does not test tool selection.** `backend/tests/agents/test_live_local.py` gives the model exactly one operation and an instruction naming it. That proves the transport path, not model choice. The protocol fixes one four-tool set for all five cases.

**Solutions:** findings 1, 7 and 8 are solved by FIX-1, FIX-3 and FIX-2 in [ENGINEERING_FIX_PLANS](ENGINEERING_FIX_PLANS.md). Finding 2 has an optional code fix (FIX-4); the protocol is already correct without it. Findings 3–6 are wording rules in the [ledger](EVIDENCE_AND_CLAIMS_LEDGER.md).

## Tasks blocked on DGX availability

All of [Protocol](AGENT_EVALUATION_PROTOCOL.md) execution; acceptance rows marked `blocked` in [SCIENTIFIC_ACCEPTANCE](SCIENTIFIC_ACCEPTANCE.md); every ledger row with "Spark" in the verification column; the Spark-success version of the form description.

## Exact handoff needed from Ben (copy into #54)

1. Release SHA running on the Spark and the command or service that started it.
2. `ollama --version`, `ollama ps` (model name, size, processor, context) and `ollama show <tag>` (parameters, quantization) at evaluation time.
3. The base URL the agent uses (expected `http://127.0.0.1:11434/v1`), and `OLLAMA_CONTEXT_LENGTH` or Modelfile `num_ctx` if set.
4. Which driver can run a **custom prompt with a chosen tool set** through the unchanged `AgentLoop` and save raw request/response exchanges (`RecordingClient` style). If none exists, say so; the protocol stays blocked rather than being improvised.
5. The accepted scenario reference (`scenario_id`, `revision`), `site_id`, `scene_revision`, `layout_ref`, placement IDs and catalogue coordinates. These fill the protocol's host-context block.
6. A 30–40 minute window with no other model loaded and no other job running.
7. Known defects at handoff.
