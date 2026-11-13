# Event-day science package — CANOPY Sheffield (13 Nov 2026)

**Revised 13 Nov 2026 (issue #57 reconciliation):** checked against `origin/main` `ca1662d`, PR #70 @ `8d24e73`, PR #71 @ `d9f1586` and the branches listed in [§Reconciliation](#reconciliation-after-ca1662d-13-nov). Nothing was executed.

**Owner:** Arnav (scientific credibility, independent evaluation, claims, submission copy).
**Status:** documentation **prepared**; nothing in this folder is a test result. No model, test, benchmark or code was run to write it.
**Repository state inspected:** `main` at `630ee651dc6d256dd7980a4f8da3df149d88c1a1` (13 Nov 11:57 UTC), read-only. Branches `release/verified-event-day`, `feat/ben/reconcile-hackathon` and `demo/hackathon` were all **behind `main` with nothing ahead**, so `main` was the newest pushed code at inspection.
**Repository state re-inspected (reconciliation):** `origin/main` at `ca1662d` (PR #61 merge), plus the open PRs, branches and issues listed in [§Reconciliation after ca1662d](#reconciliation-after-ca1662d-13-nov), read-only. Newer work on those refs is **not** on `main` (except PR #70, merged at `8d24e73` on 13 Nov 14:13 UTC, after this branch was cut). Draft PRs #76 and #77 are green in GitHub-hosted CI only (synthetic fixtures; not DGX, model or real-data evidence); #75 had no completed CI run at this revision.

| Document | Use it for | Priority |
|---|---|---|
| [SCIENTIFIC_ACCEPTANCE.md](SCIENTIFIC_ACCEPTANCE.md) | The checklist Arnav runs against the Spark release after Ben's handoff | P0 |
| [AGENT_EVALUATION_PROTOCOL.md](AGENT_EVALUATION_PROTOCOL.md) | Five frozen NVIDIA-required model inputs, bound to the real tool contract, with scoring and an evidence template | P0 |
| [EVIDENCE_AND_CLAIMS_LEDGER.md](EVIDENCE_AND_CLAIMS_LEDGER.md) | What may and may not be said in the video, form and README | P0 |
| [JUDGING_AND_SUBMISSION_BRIEF.md](JUDGING_AND_SUBMISSION_BRIEF.md) | Form description (success and partial versions), Alex's fact sheet, narration outline, short architecture summary (full text in the architecture doc below), judge Q&A | P0 |
| [ARCHITECTURE_AND_LIMITS_FOR_VIDEO.md](ARCHITECTURE_AND_LIMITS_FOR_VIDEO.md) | Architecture and limitations content for Alex's video: real components only, each box tagged on-main / branch-only / issue-reported / planned | P0 |
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

1. **The 8,192-token rule cannot be enforced or proven by the current client settings alone.** On `main` (`ca1662d`) the only client, `LocalClient`, posts to the OpenAI-compatible `/v1/chat/completions` route (base URL must end `/v1`, `agents/__init__.py` L88). Ollama documents that this API has no way to set context size, so `num_ctx` cannot be set per request, and the server default may differ from 8,192. The client's input bound is in **bytes** (`max_input_bytes`), and its token bound needs a trusted counter, which no code on `main` configures. **Update (PR #70 @ `8d24e73`, R03/R25):** Ben's **active lane is the native Ollama `/api/chat` client**, which is to send `options.num_ctx` 8,192 and `options.num_predict` on every request; `/v1` with a Modelfile alias or `OLLAMA_CONTEXT_LENGTH` (FIX-1a) is the **fallback** only. The native client is not on any pushed branch or on `integration/arnav/spark-demo`, so it is unverified. **Compliance must be shown per request from the server-reported counts of whichever transport ran, with the transport recorded:** native `prompt_eval_count` + `eval_count` with the requested `options.num_ctx`, or `/v1` `usage.prompt_tokens` + `completion_tokens`; plus the loaded context from `/api/ps`. Under Ollama prompt (prefix) caching, `prompt_eval_count` may count only newly evaluated tokens, so until its behaviour is checked on the DGX a low value does not prove compliance. **Validity rule (acceptance X-06):** 8,192 per request, prompt + output; FIX-1's 7,168-token prompt guard with 1,024 reserved for output is an engineering margin. A prompt-count bound alone does not prove nothing was truncated (PR #70 §9 step 4). Ben owns any fix. → [Acceptance X-06](SCIENTIFIC_ACCEPTANCE.md), [Protocol §5](AGENT_EVALUATION_PROTOCOL.md#5-host-versus-model-failure-classification), ledger H-06.
2. **Moving a catalogue tree with `compare_locations` always produces an infeasible diagnostic in the current contract.** `relocate()` keeps the placement's `candidate_id`/`location_id` and moves only its position, so the independent checker records `candidate mismatch`. The old FIVE-03 expectation ("a valid permitted alternative") is therefore wrong. The correct answer is that the moved position is *not* a permitted alternative in this catalogue model. → [Protocol case C3](AGENT_EVALUATION_PROTOCOL.md#c3--compare-an-alternative-placement).
3. **The synthetic "summer shade" is a one-hour, single-instant snapshot.** The seeded scenario has one time bin per case (1 Jul 12:00 UTC, 1 h; winter 1 Dec 12:00 UTC, 1 h). An `additional_shade` value in m²·h is therefore shaded area × 1 h at about solar noon. It is not daily, seasonal or annual shade. The narration must say "a one-hour midday sample" or simply "computed geometric shade for the declared time sample". → [Ledger S-05](EVIDENCE_AND_CLAIMS_LEDGER.md).
4. **Say "computed", not "measured", for shade.** Existing drafts ask the agent for "measured shade". Nothing is measured; the values are computed by the deterministic model on synthetic geometry. The frozen prompts here avoid the word.
5. **Weighted utility is not area.** The seed sets target weight 2, so `weighted_shade_utility` (weighted m²·h) should be exactly 2 × `additional_shade` for the single target. Showing the weighted number as "shade area" would double the apparent benefit. → [Acceptance N-03](SCIENTIFIC_ACCEPTANCE.md).
6. **Watch pence versus pounds.** The agent's host-generated summary prints `cost=… pence` (seed: £100 per tree = 10000 pence; budget £200 = 20000 pence). A model narrative that says "£20,000" is a numerical error. → [Acceptance N-04](SCIENTIFIC_ACCEPTANCE.md).
7. **The committed deployment profile is not the evaluated model.** `deploy/spark/model-profile.json` describes a vLLM container serving the Hugging Face BF16 checkpoint as `tree-planner-local` (status `candidate_not_device_tested`). The organisers supply Ollama tags (`nemotron-3-nano:30b`, `nemotron-3.5-lightning:30b`). The form's model field must come from `ollama ps`/`ollama show` on the Spark, not from that file. **Update (PR #70 @ `8d24e73`, R03/R05; #62):** on the active native `/api/chat` lane no alias is needed, because `num_ctx` is set per request; the `/v1` alias route of FIX-1a/FIX-3 is the fallback. If an alias was used, the form and X-02 record the **organiser base tag** behind it (`ollama show <alias> --modelfile`, `FROM` line), never the team-made alias. FIX-3's smoke assertions must match the transport that ships (see the reconciliation note in [ENGINEERING_FIX_PLANS](ENGINEERING_FIX_PLANS.md)). Issue #54 reports (Ben) a chat-only smoke of `nemotron-3.5-lightning:30b` on the Spark with no domain-tool call; that is issue-reported, not verified by us, and is not evidence that the agent ran (ledger H-07).
8. **The existing live test does not test tool selection.** `backend/tests/agents/test_live_local.py` gives the model exactly one operation and an instruction naming it. That proves the transport path, not model choice. The protocol fixes one four-tool set for all five cases.
9. **The seeded demo scene contains no buildings or existing trees, and the winter limit cannot bind.** `backend/src/tree_planner/evaluators/physical_seed.py` (`ca1662d`) sets `"triangles": []` and `"existing_trees": []` (L32–33) and `existing_trees=[]` (L121), so the baseline is unobstructed sky and no demo number shows existing shade being discounted; the B − V mechanism is exercised only in development tests. The winter case exists only when the runtime is seeded with `winter=True` (L38, L227–228). Its limit is `maximum_loss_m2_h=100` (L259), but the receiver grid is 13 × 15 = 195 samples of 0.25 m² (L25, L29–30) with one 1-h bin (L217), so the largest possible loss is 195 × 0.25 m² × 1 h = 48.75 m²·h. If the winter case is shown, say "checked and passing" (only once a recorded result shows it), never that the winter limit shaped the result. → Ledger I-02, S-01, S-06.

**Solutions:** findings 1, 7 and 8 are solved by FIX-1, FIX-3 and FIX-2 in [ENGINEERING_FIX_PLANS](ENGINEERING_FIX_PLANS.md) (for the native `/api/chat` lane, see the reconciliation note at the top of that file). Finding 2 has an optional code fix (FIX-4); the protocol is already correct without it. Findings 3–6 and 9 are wording rules in the [ledger](EVIDENCE_AND_CLAIMS_LEDGER.md).

## Tasks blocked on DGX availability

All of [Protocol](AGENT_EVALUATION_PROTOCOL.md) execution; acceptance rows marked `blocked` in [SCIENTIFIC_ACCEPTANCE](SCIENTIFIC_ACCEPTANCE.md); every ledger row with "Spark" in the verification column; the Spark-success version of the form description.

## Exact handoff needed from Ben (copy into #54)

1. Release SHA running on the Spark and the command or service that started it.
2. `ollama --version`, `ollama ps` (model name, size, processor, context) and `ollama show <tag>` (parameters, quantization) at evaluation time.
3. The base URL and transport the agent uses (native `/api/chat`, the active lane per PR #70 @ `8d24e73`, or the `/v1` fallback), plus the `think`/`num_ctx`/`num_predict` values actually sent (native), `OLLAMA_CONTEXT_LENGTH` or Modelfile `num_ctx`, as applicable. If an alias is served, the organiser base tag behind it (`ollama show <alias> --modelfile`).
4. Which driver can run a **custom prompt with a chosen tool set** through the unchanged `AgentLoop` and save raw request/response exchanges (`RecordingClient` style). If none exists, say so; the protocol stays blocked rather than being improvised.
5. Confirmation that the driver fills the protocol's host-context block from its own fresh `create_physical_runtime(winter=True)` (do **not** hand over a `scenario_id`: it is a new uuid4 per runtime), plus the FIX-3 smoke output: argument type, call id, finish/done reason and usage fields.
6. A 30–40 minute window with no other model loaded and no other job running.
7. Known defects at handoff.

## Reconciliation after ca1662d (13 Nov)

This pass reconciles the package with work published after PR #61 merged. It is documentation only: **no code, tests, builds or models were run**, nothing was run on the Spark, and nothing below is a result.

**Refs inspected (read-only):**

- `origin/main` @ `ca1662d` (merge of PR #61, this package).
- PR #66 (3D city and tree-identification specification) at `14a9a69` and re-checked at `a1fbced`; PR #67 (3D agent UI) at `b0e0ef9` and re-checked at `2ff054b`. Ledger W-03 quotes the later heads.
- PR #70 @ `8d24e73` (Nemotron agent runtime audit; merged to `main` 13 Nov 14:13 UTC at that head) and PR #71 @ `d9f1586` (agent evidence frontend handoff). Only these versions are quoted; the cited lines were compared with the earlier `c28d15b`/`0dd2f3b` and are unchanged.
- PR #44 at `origin/chore/drop-signoff-gates` (D17 sign-off withdrawal, AGENTS rule 10).
- Alex's branches: `feat/alex/design-parity` @ `a130bbd`, `feat/alex/terrain-context-view` @ `b1bb0e5`, `feat/alex/STP-005-site-audit` @ `03abb3f`. None is on `main`.
- `integration/arnav/spark-demo` @ `6ff381e` (local branch; the same tip is reachable as `origin/ref/arnav/integration-spark-demo`). Not on `main`.
- Issues #54, #62, #64, #68, #69, #73 and #74. Statements from #54 are **issue-reported by Ben**, not verified by us.
- Draft PRs #75 (#68 observation views, `2dc4c3f`: no completed CI run), #76 (#74 groundwork, `c6a8b8f`) and #77 (#69 recorded-tree importer, `6a9d45a`): #76 and #77 are green in GitHub-hosted CI on synthetic fixtures only; none is DGX, model or real-data evidence (ledger G-12). Draft PR #78 is a design reference with example figures only; nothing from it is a result.

**Method:** a read-only audit in five lanes. Every finding was independently re-checked against its cited source, then a completeness critic looked for gaps. Outcome: 97 confirmed findings plus 11 critic findings; 6 findings were refuted and dropped. Findings that target documents outside this folder were forwarded, not applied (list below).

**What changed in each file** (each edited file carries a revision line under its title):

| File | Change |
|---|---|
| README.md (this file) | Revision lines; index row for the new architecture doc; findings 1 and 7 updated for the native `/api/chat` lane (PR #70) with `/v1` as fallback; new finding 9 (no buildings or existing trees in the demo scene; winter limit cannot bind); handoff item 3 asks for transport and `num_ctx`; this section |
| [EVIDENCE_AND_CLAIMS_LEDGER.md](EVIDENCE_AND_CLAIMS_LEDGER.md) | Category notation clarified ("A + B", "X → Y (condition)"); H-05 recast; I-02, I-06, S-01, S-05, S-06, S-08, H-01–H-05, M-01, G-01, G-02, G-07, O-02, D-03 and D-04 amended; new rows I-07, I-08, O-06, H-06–H-08 and G-08–G-12; new section for real Sheffield data, 3D and geospatial (W-01–W-05); quick-reference additions; new Evidence register (the "Spark evidence" column the old rule referred to did not exist) |
| [SCIENTIFIC_ACCEPTANCE.md](SCIENTIFIC_ACCEPTANCE.md) | S-07 now points to ledger S-03, S-04, O-01 and the quick reference; N-02, N-05, A-02, A-04 and X-05 amended (recording and pointers only); X-06 records transport-specific token fields. Changes to pass/fail conditions (N-09, X-02, the X-06 threshold) are in a separate commit pending Arnav's sign-off (see "Decisions" below) |
| [JUDGING_AND_SUBMISSION_BRIEF.md](JUDGING_AND_SUBMISSION_BRIEF.md) | §5 reduced to a short corrected summary that links to the new architecture doc; wording aligned with the amended ledger rows |
| [ARCHITECTURE_AND_LIMITS_FOR_VIDEO.md](ARCHITECTURE_AND_LIMITS_FOR_VIDEO.md) | **New.** Architecture and limitations content for Alex, real components only, each tagged on-main / branch-only / issue-reported / planned |
| [ENGINEERING_FIX_PLANS.md](ENGINEERING_FIX_PLANS.md) | One reconciliation note under the title proposing native `/api/chat` equivalents for FIX-1a, FIX-2 and FIX-3, plus one-line "applies only to `/v1`" pointers above FIX-1's solution and acceptance evidence and FIX-3's solution. Ben's steps are unchanged |
| [IMPACT_AND_FEASIBILITY_RESEARCH.md](IMPACT_AND_FEASIBILITY_RESEARCH.md) | Canonical council street-tree URL; §4 runtime-risk statement covers both transports; §5 local-inference sentence made conditional on Spark evidence |

| [AGENT_EVALUATION_PROTOCOL.md](AGENT_EVALUATION_PROTOCOL.md) | New §2a transport mapping (native `/api/chat` vs `/v1`) and transport-specific recording fields in §1, §2, §5, §7 and §8; the driver records the transport. Recording, setup and failure-classification clarifications only; no expected outcome or pass condition changed. `five_case_prompts.json` is untouched and its SHA-256 hashes stay valid |

**Decisions (13 Nov):**

- **Recorded (Arnav, relayed by the team coordinator session):** S-08 option A: shade results are described as computed on synthetic test geometry at Sheffield's latitude, and the terrain view is not filmed (ledger W-01 "not filmed"; option B kept only as fallback wording). Arnav owns the agent-evidence UI (#74); Alex keeps the rest of the UI.
- **Applied in a separate commit for Arnav's sign-off:** the token validity rule (8,192 per request, prompt + output; the 7,168-token prompt guard is a margin) and the acceptance pass/fail changes to N-09 (winter wording, `--winter` blocked state) and X-02 (organiser base tag behind any alias). That commit can be dropped without affecting the claims documents.

**Forwarded to owners (not edited here):**

- PR #66 and PR #67 (3D city, tree identification, map-first agent UI): owner Arnav (their author).
- PR #70 and PR #71: their authors (transport, evidence and UI-state wording only; this pack quotes `8d24e73` and `d9f1586`).
- Alex's branches `feat/alex/design-parity`, `feat/alex/terrain-context-view` and `feat/alex/STP-005-site-audit`: the "VIEW ONLY" tag, Environment Agency attribution with OGL v3.0, "© OpenStreetMap contributors" for the OSM-derived box, and keeping the view out of every calculation (ledger W-01).
- PR #44: D17 and AGENTS rule 10 would withdraw the claims-control sign-offs; proposed scope limits and a rebase onto `ca1662d` go to its owner.
- Issue #64 checklist: FIX-3's smoke assertions and the `.env` alias line need the same transport condition as the note in ENGINEERING_FIX_PLANS.
- `docs/EVENT_DAY_CONTENT_AND_CLAUDE_HANDOFFS_2026-11-13.md` §2–§4 and `docs/EVENT_DAY_EXECUTION_2026-11-13.md` §11–§12: "superseded by" pointers, "measured" → "computed", and FIVE-03's "valid alternative" expectation.
- Root `README.md`: its "small local-model round trip has been demonstrated" refers to a laptop Qwen run and is not Spark or Nemotron evidence (ledger H-08).
