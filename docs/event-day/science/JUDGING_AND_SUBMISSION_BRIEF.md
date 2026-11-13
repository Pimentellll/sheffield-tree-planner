# Judging and submission brief

**For:** Arnav (form, #60), Alex (video facts, #58), whole team (Q&A). **Status:** prepared copy. Bracketed `[…]` items are filled **only** from verified evidence; see the [claims ledger](EVIDENCE_AND_CLAIMS_LEDGER.md). It replaces [handoffs §2](../../EVENT_DAY_CONTENT_AND_CLAUDE_HANDOFFS_2026-11-13.md#2-safe-form-description--ready-for-userteammate-review) for final form copy; the earlier storyboard timings in handoffs §3 remain Alex's.

## 1. Submission description (paste into the NVIDIA form)

Choose **one** version after the five-case run. Word counts exclude brackets.

### Version A — Spark agent verified (A-01, X-01, X-02 verified)

> Choosing where to plant urban trees involves trade-offs that a tree count hides: where new shade actually falls relative to buildings and existing trees, winter sunlight, spacing, budget and unknown site conditions. Sheffield manages its street trees through a multi-partner strategy, so decisions also need to be explainable. CANOPY Sheffield is a tree-planning workbench that makes those trade-offs computable and traceable. A deterministic engine computes additional direct-sun shade (m²·h) using standard solar geometry, checks budget, spacing and winter-sun limits independently, and records the inputs, versions and hashes behind every result. A local agent running **[exact model tag]** through Ollama on our NVIDIA DGX Spark chooses registered planning tools to evaluate, search and compare layouts. It cannot accept plans, change the budget or invent results: figures come from stored backend results. In our five required tests it **[k/5 summary, including the ambiguous and "I don't know" cases]**. The demo uses synthetic geometry at Sheffield's latitude. Real use would need surveyed data, field validation and human approval, and shade is not yet a temperature prediction.

### Version B — Spark agent partial or not verified

> Choosing where to plant urban trees involves trade-offs that a tree count hides: where new shade actually falls relative to buildings and existing trees, winter sunlight, spacing, budget and unknown site conditions. Sheffield manages its street trees through a multi-partner strategy, so decisions also need to be explainable. CANOPY Sheffield is a tree-planning workbench that makes those trade-offs computable and traceable. A deterministic engine computes additional direct-sun shade (m²·h) using standard solar geometry, checks budget, spacing and winter-sun limits independently, and records the inputs, versions and hashes behind every result. Its agent layer lets a locally hosted model call registered planning tools while the backend keeps authority over every number and approval. **[One factual sentence on what was shown on the Spark, e.g. "On our DGX Spark we demonstrated …" or "Integration of the local model on the Spark was not completed in time; the video shows …"]**. The demo uses synthetic geometry at Sheffield's latitude. Real use would need surveyed data, field validation and human approval, and shade is not yet a temperature prediction.

### Other form fields

| Field | Fill rule |
|---|---|
| Project name | CANOPY Sheffield |
| Team name | [team to confirm] |
| Members' names and emails | Entered privately in the form only; never in the repo or video |
| Track | Urban Operations |
| AI models used | Exact tag(s) from `ollama ps` during the evaluated run, e.g. `[nemotron-3-nano:30b]`. Do not list models that were only planned or used on laptops |
| NVIDIA tools/libraries/SDKs | `NVIDIA DGX Spark`; the Nemotron model if verified. Ollama is organiser-supplied but **not** an NVIDIA SDK: list it only if the field allows non-NVIDIA tools, labelled as such. Do **not** list CUDA, NIM, TensorRT-LLM, NeMo, vLLM, Warp, cuOpt or OptiX unless the deployed release actually used them (ledger H-05) |
| Repository URL | Public URL from Ben after #59; open it in a private window first |
| Video URL | From Alex after #58; ≤ 5:00; open it in a private window first |

## 2. Impact, Technical Execution and Feasibility (team review text)

**Impact — does it solve a real problem?** Urban tree planting is constrained, public and contested. In Sheffield it runs through a formal partnership of the council, its highways contractor, conservation charities and campaign groups ([research §1](IMPACT_AND_FEASIBILITY_RESEARCH.md#1-the-real-problem-in-sheffield)). The practical difficulty is not "plant more trees" but "which positions add useful shade within this budget and these constraints, and can we show why". Shade that duplicates existing building or canopy shade adds nothing. Winter overshadowing can be a cost. Utilities and surveys decide what is deliverable. CANOPY targets that decision step: comparable, explainable options with explicit unknowns. We do **not** claim measured cooling or community outcomes; shade is the first, physically defensible link in that chain ([research §2](IMPACT_AND_FEASIBILITY_RESEARCH.md#2-shade-is-not-cooling-what-the-evidence-supports)).

**Technical Execution — agentic AI and local compute.** The agent is a bounded tool-using loop. The model sees typed tool schemas generated from the backend contracts, chooses an operation, and the host validates arguments, dispatches an asynchronous job, polls it, checks result identity and currentness, and accepts only evidence IDs it actually observed. User-facing figures are generated from stored Results. The model's own wording is kept separately and scored for faithfulness. The model runs locally on the DGX Spark through the organiser-supplied Ollama **[if verified]**; the numerical engine is a CPU reference implementation (pvlib SPA sun positions, ray–crown intersection, overlap-aware search, independent constraint checker). The five organiser-required tests are scored on eight dimensions and attribute failures to model, host or numerics ([protocol](AGENT_EVALUATION_PROTOCOL.md)). Why deterministic tools: they make numbers reproducible and auditable, and they let us show a model mistake as a model mistake rather than hiding it in fluent text.

**Feasibility — beyond the hackathon.** The contracts already carry what a real deployment needs: immutable scenario revisions, input fingerprints, source and rights records, survey requirements as explicit unknowns, and human acceptance. The next step is a desk pilot on one real street with rights-cleared geometry and an independent shadow comparison, then an optional radiation/thermal-comfort module (SOLWEIG-class) validated against field data, then integration with survey and highways processes ([research §5](IMPACT_AND_FEASIBILITY_RESEARCH.md#5-staged-adoption-pathway-feasibility)). Local inference on one device avoids sending council site data to a hosted model service.

## 3. Technical fact sheet for Alex (content only; no UI instructions)

- **Units:** shade `m²·h` (area × hours of direct sun blocked). The weighted figure is `weighted m²·h`, a priority score, never area. Money is integer pence internally; £ = pence ÷ 100. Demo scenario (if unchanged): £100.00 per tree, budget £200.00, maximum 2 trees, minimum 2 m between trees.
- **Time sample:** each case is a one-hour sample at 12:00 UTC (summer and establishment on 1 Jul; winter on 1 Dec, leaf-off). Say "a one-hour midday sample", not "summer shade".
- **Cases:** `summer` = mature tree (year 20); `establishment` = young tree (year 1); `winter` = leaf-off check against a maximum-loss limit (100 m²·h). Do not add them together.
- **Search:** "best evaluated layout among the catalogue positions; every constraint re-checked independently". Not "optimal".
- **Relocation compare:** moving the existing tree to another catalogue position is reported **infeasible** (diagnostic) by design. Do not film it as a valid better option. If a "better alternative" moment is wanted, film the search result (selected vs reference) or the UI scenario comparison.
- **Agent:** one model, a few registered tools (evaluate, search, compare, inspect). It cannot accept a scenario, change the budget or grant permission. Displayed figures come from backend results. Show the tool call, job ID/status and run ID if the UI exposes them.
- **Labels required on screen when results are shown:** "Synthetic geometry — not a surveyed Sheffield site". Also "Computed direct-sun shade — not a temperature prediction" once.
- **Only show numbers** from a Result on the release SHA with its run ID visible or logged. Laptop or old screenshots are not Spark evidence.
- **If the agent fails on camera:** keep the failure visible or cut to the deterministic workflow. Never narrate a tool call that did not happen.

## 4. Demo narrative (≤ 5:00), keyed to the existing storyboard blocks

| Block (handoffs §3) | Narration content (say in your own words) | Must be on screen | Claim rows |
|---|---|---|---|
| 0:00–0:35 Problem | Sheffield manages street trees through a partnership strategy; deciding *where* to plant means balancing new shade, winter sun, spacing, budget and unknown site conditions, and the result has to be explainable | Title; optional council strategy citation | I-01, I-02, I-06 |
| 0:35–1:05 Product | CANOPY is a workbench: a scene, a proposed tree, an accepted budget; numbers come from a deterministic engine | Synthetic-geometry label | S-01, S-08 |
| 1:05–2:25 Agent | Ask a concrete question (C1 or C2 wording); the local model picks a tool; the job runs; the answer cites the run | Model tag, tool call, job → completed, run ID | H-01, M-01, G-01 (only if verified) |
| 2:25–3:35 Results | Read the computed shade with its unit and time sample, cost in £, constraint checks, winter check; show search's best evaluated layout vs the proposal | Result panel with units and run ID | S-05, S-06, O-01, O-02 |
| 3:35–4:15 Why local + why tools | Model runs on our DGX Spark; tools keep numbers reproducible; the agent cannot approve or change the budget; show the "I don't know" (C5) or clarification (C4) clip if passed | `ollama ps` or equivalent proof; C4/C5 transcript | H-01, G-02, G-03 |
| 4:15–4:45 Feasibility + limits | Synthetic today; next a real-street pilot with surveyed data and an independent shadow check; shade is not yet temperature | Limitations card | D-02, S-09 (safer wording) |
| 4:45–5:00 Close | CANOPY Sheffield, Urban Operations, repo link | End card | D-03 |

**Partial-outcome variant:** replace 1:05–2:25 with the deterministic workflow (evaluate → search → compare in the UI) and one honest sentence on agent status. Move the agent design (bounded tools, evidence-ID checks) into 3:35–4:15 as architecture, clearly labelled "design" rather than "demonstrated".

## 5. Architecture (text for a diagram)

```text
[User in browser: React/Three.js workbench]
        │ HTTP (loopback / SSH tunnel)
        ▼
[FastAPI backend: typed contracts, scenario revisions, rights checks]
   ├── Job service (async jobs, current-selection slots, stale-result fencing, SQLite)
   │       └── Deterministic CPU engine: pvlib SPA sun → ray–crown/scene shading → m²·h metrics
   │                                    → overlap-aware search + independent constraint checker
   └── Agent loop (host-controlled)
           ├── sends typed tool schemas + trusted context → [Local model via Ollama on DGX Spark, 127.0.0.1]
           ├── receives tool call → validates arguments → dispatches job → polls → checks identity/currentness
           └── accepts only observed evidence IDs → host-generated summary from stored Results
Human: accepts scenarios and decides; the agent can only investigate.
```

Diagram labels to keep honest: "CPU numerical engine"; "local model (Ollama on DGX Spark)" only if X-01/X-02 are verified; no GPU-physics arrow.

## 6. Likely judge questions and evidence-based answers

| Question | Answer (keep within ledger) |
|---|---|
| How much does this cool the street? | We don't predict temperature. We compute direct-sun shade, which UK field studies link to lower radiant heat exposure. A temperature or comfort estimate needs a radiation model with weather data and field validation; that is our stage-2 extension. |
| Is this real Sheffield data? | No. The demo uses synthetic geometry at Sheffield's latitude, so the solar geometry is right for the city but the buildings and trees are test objects. Real data needs rights, coordinate checks and surveys first. |
| What does the AI actually do that a form couldn't? | It turns a plain-language question into the right registered analysis, runs it and explains the stored result, and it should ask or decline when the question is ambiguous or out of scope (our C4/C5 tests: [result]). We have not shown it is better than a manual workflow; that comparison is future work. |
| How do you stop hallucinated numbers? | Figures shown to users are generated from stored backend results. The host rejects evidence IDs it did not observe and checks result currentness. We separately score the model's own wording, and report any mismatch as a model error. |
| Why local / why the Spark? | The model runs on the device next to the tools, with no hosted model API, which matters for council data governance. [Latency: measured value with n, or "not measured".] The numerical engine is CPU; we don't claim GPU physics. |
| Is the search optimal? | It reports the best evaluated layout in a finite catalogue, with constraints re-checked independently. We make no global-optimality claim; the demo catalogue is tiny, so this shows correctness, not scale. |
| How did Nemotron do? | [Exact k/5, failures and their class, model tag, SHA.] Five tests don't establish reliability; we report every attempt. |
| What about utilities, soil, permissions? | They are modelled as explicit "survey required" unknowns and never marked as passed. Real delivery follows survey, highways and partnership processes. |
| Who would use it? | Tree and highways officers and designers preparing options for review, and partnership members who need to see why one option was preferred. That is a hypothesis to test in a pilot, not a validated user finding. |
| What would it take to deploy? | Rights-cleared geometry, a one-street desk pilot with an independent shadow check, then survey integration and governance ([research §5](IMPACT_AND_FEASIBILITY_RESEARCH.md#5-staged-adoption-pathway-feasibility)). |

## 7. Limitations and future pathway (closing card text)

**Today:** synthetic geometry; one-hour midday samples; assumed crown sizes, transmission and costs; three-candidate catalogue; CPU engine; five agent tests on one scenario; no field validation; no temperature, energy, carbon, air-quality, flood or financial predictions; utilities, soil and permissions remain survey-required.
**Next:** a real-street desk pilot with rights-cleared data → independent shadow validation → an optional SOLWEIG-class thermal-comfort module with field checks → integration with survey and highways decisions under human approval.

## 8. Final pre-submit checks (#60)

- [ ] Version A or B chosen from evidence, with every bracket filled from the [acceptance](SCIENTIFIC_ACCEPTANCE.md) sign-off record
- [ ] Model tag in the form = `ollama ps` tag in the run log
- [ ] No ledger UP wording in form, README or video
- [ ] Repo and video URLs open in a private window; video ≤ 5:00
- [ ] Submitted by the 17:30 target; confirmation saved. The 18:00 close is team-reported, not organiser-confirmed
