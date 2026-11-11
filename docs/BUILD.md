# Build plan, task state and decisions

**This is the only task-status/decision home until a shared tracker is explicitly adopted.**  
Documentation baseline 0.1. Application implementation remains **Planned**; B09 separately records completed readiness preparation without claiming device/domain acceptance. Named owners are proposed and must acknowledge their lane; they can use scoped coding assistants without giving away scientific or integration accountability.

Related: [Spec](SPEC.md) · [Contracts](CONTRACTS.md) · [Numerics](NUMERICS.md) · [Validation](VALIDATION.md).

## 1. Delivery policy

Develop the portable core **before the event**, after the relevant working contracts are understood. Do not wait until Spark access to write CPU physics, tests, jobs or the interface. Separately check current competition eligibility and preserve an honest advance-work record. A rule/rights gate blocks the affected submission or asset use, not unrelated engineering.

Build in dependency order, not three isolated prototypes. The research handoff and this documentation are not software completion. Do not reduce the ambition to a mock: each slice must produce a real behaviour and then improve that same system.

## 2. Proposed ownership and integration

- **Ben:** scenario/backend contracts, job identity, domain dispatcher, agent adapter and integrated working baseline. Owns contract-change coordination, not sole authorship/review of everything.
- **Arnav:** physical semantics, analytic reference, site/evaluator validity, search correctness and uncertainty. Split site → evaluator → masks → search, rather than one late monolith.
- **Alex:** scene import/view transform, map controls, target/exclusion editing, comparison/evidence panels, accessibility and demo interaction.
- **Ben + Arnav:** real evaluator request/result and final constraint validation. Ben can implement search plumbing after Arnav defines/tests semantics.
- **Arnav + Alex:** one known point, north direction, metre scale, tree size and target area agree between viewer and solver.
- **Ben + Alex:** revision identity, queued/error/cancelled/cached/stale states and late-job rejection.

At each integration checkpoint provide: exact revision, what ran, output/evidence, interface changes, current blocker and next action. Do not substitute a meeting or a model's assurance for a working path.

## 3. Work items

### B01 — Contract and portable application foundation

- **Owner:** Ben; reviews: Arnav + Alex. **State:** Planned. **Dependencies:** this working spec; explicit acknowledgement before parallel consumers build against it.
- Create typed backend models, generated API/frontend types and the minimal local API/UI shell. Select versions through imports and an actual smoke; record tested install/start commands. Establish immutable revisions, structured errors and a central asset registry.
- The dedicated private repository is established under D08; B01 covers application/schema work, not another repository. Use this checkout or an isolated worktree and preserve unrelated work.
- **Acceptance:** V01 and the validation portion of V05; one valid synthetic site/scenario is accepted, malformed units/refs are rejected, generated types match backend. Setup can be repeated. No invented successful numerical response.
- **Evidence to attach:** commands/output, schema/OpenAPI version, generated-type check and source revision. **Next consumer:** B02/B04/B05/B09.

### B02 — Analytic solar and geometry reference

- **Owner:** Arnav. **State:** Planned. **Dependencies:** B01 shared models.
- Implement solar direction, UTC/time bins, analytic ellipsoid/trunk intersections and a minimal static occluder reference. Tests use authored, explicitly synthetic inputs; maintain correct normals/areas and no double-counting.
- **Acceptance:** V02's B02 analytic/opaque-geometry subset, finite/units tests and same-input repeatability. Solar-reference comparisons are separate from hand-computed shadow tests. Multi-tree evaluation and transmission wait for their named later gates.
- **Evidence:** test command/output and input/expected/actual values. **Next consumer:** B04 and accelerator comparison.

### B03 — Real-site and rights audit (parallel lane)

- **Owner:** Arnav + Alex, one named writer per asset/manifest. **State:** Planned. **Dependencies:** SiteBundle contract, not the full solver.
- Audit one park/playground candidate plus a fallback; verify lawful team sharing/display/export, geometry scale/north/context, semantic masks and existing-tree assumptions. Keep unknown utilities/soil/permission visible. Do not substitute historical planting areas or School Localities for site permission/geometry.
- **Data-source candidate, not selected:** assess Environment Agency 1 m composite DTM/DSM via [Defra Survey](https://environment.data.gov.uk/survey) against a Sheffield park site and fallback. Pilot a small rights-checked crop and verify local survey year, DSM/DTM alignment, elevations/datum, real building-versus-canopy semantics, missing shadow-casting context, metre/north transform and the resulting viewer/solver geometry. This is *raster elevation*, not a ready-made semantic 3D map or evidence of plantability. See [SOURCES: LiDAR candidate](SOURCES.md#candidate-site-geometry-source-environment-agency-lidar-11-november-2026-desk-audit); V03 is still required.
- **Acceptance:** V03; a reviewed manifest and usable source assets, or an explicit failed-site decision and replacement. Unknown rights do not pass.
- **Evidence:** provenance/licence records, transform checks and gap list. **Next consumer:** B08. **Does not block:** synthetic B02/B04/B05.

### B04 — Baseline versus one tree, real computation

- **Owner:** Arnav evaluator; Ben job wrapper. **State:** Planned. **Dependencies:** B01 + B02. B03 only for real-site claims.
- Evaluate unchanged scene and one proposed tree on identical samples/bins. Return actual metrics, constraints, identity and provenance through the API. Capture real runtime fixtures from this implementation for UI development; label synthetic scene provenance.
- **Acceptance:** V02's B04 single-tree subset + V04 baseline/single-tree metric cases; valid zero gain and already-shaded target. Multi-proposed-tree overlap/constraint tests belong to B06. No optimiser/model prerequisite.
- **Evidence:** reproducible run IDs, input snapshot and baseline/proposal result. **Next consumer:** B05/B06/B07/B08.

### B05 — Interactive vertical slice

- **Owner:** Alex with Ben. **State:** Planned. **Dependencies:** B01 for shell; B04 for actual data.
- Show site, target, existing/proposed tree and computed difference. Add manual evaluation, progress, cancellation, error/provisional/cached labels and revision-safe edits. Validate viewer/solver transform with Arnav.
- **Acceptance:** V05 + V10's B05 single-tree UI subset; edit a scenario while an old run finishes and prove the old result cannot overwrite the draft/current revision. A rendered sun slider does not silently change analytical metrics. Search/comparison and multi-zone/case panels are integrated with B06/B07/B10 and covered fully at B12, not prerequisites for G1.
- **Evidence:** end-to-end trace and actual UI capture, including failure/stale state. **Next gate:** G1.

### B06 — Candidate search and independent feasibility

- **Owner:** Arnav semantics; Ben may implement search/job plumbing under agreed ownership. **State:** Planned. **Dependencies:** B04 and candidate/profile contract.
- Build candidate masks, deterministic competent reference, marginal-gain greedy plus local improvement. Implement maximise-shade first, then target-seeking least-cost search. Keep a separate final-layout validator.
- **Acceptance:** V04 and V06 plus V02's B06 multi-tree overlap subset; compare tiny exact cases, enforce pins/spacing/budget/winter rules, show actual spend/count, preserve empty/target-miss outcomes. Supported winter-case evaluation is supplied by B07 before that portion is verified; B06's portable search work can proceed first. Never claim proven infeasibility from a heuristic miss.
- **Evidence:** reference/selected layouts, constraint report and method/seed. **Next consumer:** B10.

### B07 — Cases, uncertainty and controlled comparison

- **Owner:** Arnav with Ben; Alex consumes results. **State:** Planned. **Dependencies:** B04.
- Add establishment/target/leaf-state cases, fixed-crossing crown transmission, supported winter checks, controlled one-tree relocation and fixed-layout sensitivity. Test spatial/time/context refinement and correct cache invalidation. Full redesign reuses B06; path-length attenuation is not required in this core.
- **Acceptance:** V07 plus V02's B07 fixed-transmission subset; separate horizon from uncertainty, record all changed inputs, keep other trees fixed in relocation, and flag infeasible alternatives instead of silently modifying them. Validate matching comparison/case UI panels with Alex before G2/G3.
- **Evidence:** comparisons/ranking and convergence records, including stable rankings when that is what occurs. **Next consumer:** B10.

### B08 — Real Sheffield integration proof

- **Owner:** all three, Arnav accountable for physical validity. **State:** Planned. **Dependencies:** B03 + B04 + B05.
- Replace synthetic input with the accepted real site without changing API meaning. Re-run transform, baseline, one-tree and context checks on the actual assets. Inspect independent reference/observation evidence where available.
- **Acceptance:** V03 + applicable V02/V07; real-site claim is supported and provisional assumptions are prominent. A visually convincing mesh alone does not pass.
- **Evidence:** rights-cleared manifest, reproducible real runs and matching UI. **Next gate:** real-site portion of G2.

### B09 — Local model/runtime proof (start early when available)

- **Owner:** Ben. **State:** Active — preparation implemented; device acceptance blocked until event access. **Dependencies:** tool schema from B01 for domain integration; actual Spark access for Spark evidence.
- **Prepared:** [DGX_SPARK.md](DGX_SPARK.md), SSH/tunnel template, ARM64-pinned inference recipe/model manifest, and installable `sheffield-tree-planner-readiness` diagnostic. This diagnostic is not the product agent, domain dispatcher or application package.
- **Local evidence:** initial worker suite passed eight protocol/CLI test methods on Python 3.11; integrated parent suite passed ten methods on Python 3.13, including deployment/document invariants. These use a labelled synthetic HTTP protocol fixture, not a model. `uv build` produced wheel/sdist. Compose 5.7.1 parsed the service configuration; OpenSSH 10.2 parsed the placeholder SSH config without connecting. Registry metadata was digest-checked for the exact Linux ARM64 image; no weights/image layers were downloaded. Final independent-review, clean-artifact and hosted-CI receipts belong to the exact PR revision, not inferred from these preliminary checks.
- **Merge verification (11 November):** reconciled [PR #1](https://github.com/bbeennyy860-cyber/sheffield-tree-planner/pull/1) with main `9833748430c9197bc7184e89391e9fd07094bd11`, preserving the source audit, feature priorities and research dossier. Parent and independent reviewer each passed all twelve tests using a fresh Python 3.11.9 wheel installation outside the checkout; installed version/help/environment and non-loopback rejection checks passed. `uv build` reproduced the previously checked wheel/sdist SHA-256 values. Source, tests, deployment templates and CI are unchanged from the original PR head. Independent integration review passed on tree `d8b64a85fb86bce696a600f4167ee1c220b4ab6c`; subsequent edits only clarify this BUILD status/evidence. Ruff 0.17.4 explicit core checks (`E4,E7,E9,F`) and formatting passed; its broader defaults report six existing style findings, not merge regressions. Integration release impact is **none**; the diagnostic retains its initial minor version **0.1.0**. See the PR for final hosted-CI and merge receipts; this does not establish a model, GPU, device or domain run.
- **Next action / owner:** Ben obtains organiser-approved host/account/fingerprint/network access; the integration owner then runs the real device/model/domain checks below. No remote configuration, SSH key creation or deployment has occurred.
- Test an exact supported open-model/checkpoint/quantisation/parser/runtime and one registered tool call. On a laptop, test adapter/schema behaviour separately and label the environment. Model unavailability must not block CPU/manual work.
- **Acceptance:** V08: actual model → tool arguments → dispatcher → observation, with recorded device and cold/warm behaviour. An assumed SDK or scripted response does not pass.
- **Evidence:** exact versions, logs with secrets removed, timings and coexistence memory. **Next consumer:** B10.

### B10 — Adaptive planning investigator

- **Owner:** Ben; Arnav validates tools, Alex validates interaction. **State:** Planned. **Dependencies:** B06 + B07 + B09, B05 for visible product.
- Implement interpret/inspect/choose/analyse/explain loop over immutable scenarios. Include relocation, redesign after an accepted change, and justified sensitivity. Guard claims, permissions, prompt injection and no-progress termination.
- **Acceptance:** V09; unfamiliar requests choose appropriate real operations, preserve constraints and cite actual current result IDs. No hardcoded “AI demonstration” replacing the model path.
- **Evidence:** traces for success, ambiguity, unsupported savings, tool failure, no-progress and stale scenarios. **Next gate:** G3.

### B11 — Same-tools value comparison

- **Owner:** all three; someone other than the agent-loop author checks scoring. **State:** Planned. **Dependencies:** B10 + working manual/fixed workflow.
- Run held-out ordinary, compound, counterfactual, infeasible and failure tasks through manual controls, fixed workflow and agent, with identical backend/constraints. Include manual effort and all failures.
- **Acceptance:** V11; report completion, claim accuracy, corrections, useful analyses and latency without assuming the agent wins. Narrow the claim if evidence does not support superiority.
- **Evidence:** task definitions, immutable inputs, runs and scoring. **Next consumer:** B12/pitch.

### B12 — Reproducible build and demo candidate

- **Owner:** Ben integration, Alex demonstration, Arnav scientific claims. **State:** Planned. **Dependencies:** B05–B11; event eligibility is additionally required before submission claims/actions.
- Test clean setup, complete smoke, permissions-safe export and known-good recovery. Record exact dependency/model/data manifest. Set feature freeze against the actual submission deadline once confirmed; use later work for repairs/rehearsal, not unrelated feature expansion.
- **Acceptance:** V12; another teammate runs the instructions, genuine local-agent evidence exists, no hard-constraint/stale/claim failures remain, fallback labels and limitations are visible.
- **Evidence:** verified runbook, clean setup output, final demo trace and claim ledger. Remote CI, publication and submission are separate authorised actions, not inferred from local tests.

## 4. Integration gates

- **G1 — truthful portable slice:** B01/B02/B04/B05; baseline → one tree → actual metric → UI → edit makes prior result stale. Synthetic provenance is allowed here.
- **G2 — defensible real decision:** B03/B06/B07/B08; real-site evidence, reference/search comparison, hard-constraint validation and horizon/winter checks.
- **G3 — real investigation:** B09/B10; actual local model takes the right tool branch from observed results, then explains verified evidence.
- **G4 — release candidate:** B11/B12; repeatable end-to-end operation, honest comparative results, recovery and admissible demo material. G4 is not authority to publish or submit.

Owners report the first failed gate rather than declaring the whole product finished. Reuse one working path throughout.

## 5. Decisions and unresolved gates

- **D01 — accepted direction (Ben, 11 November):** documentation then advance development, rather than waiting for the event. Previous team's week of advance work is user-reported precedent. Exact current eligibility remains unknown; maintain prior-work provenance and confirm before representing eligibility.
- **D02 — working defaults:** opaque axis-aligned ellipsoid/trunk; unweighted additional target shade; upfront GBP-pence budget; explicit winter limits; one primary benefit case; one adaptive agent and deterministic tools. Rationale: testable semantics before richer biology/economics. Arnav/Ben/Alex acknowledge before parallel dependent implementation; local exploratory tests may use this named draft.
- **D03 — proposed ownership:** responsibilities above. Owners acknowledge or swap lanes explicitly; do not infer agreement from silence.
- **D04 — contract clarification:** supersession is an orthogonal marker, not a terminal execution state. Rationale: old work may finish into history without becoming current. Review with backend/UI consumers in B01; this supersedes the research draft's combined status list.
- **D05 — site unresolved:** no real site/geometry/planting permission is certified. B03 owns evidence; synthetic development proceeds honestly while that work runs. Environment Agency LiDAR is a newly documented candidate for B03 assessment, not an approved site, accepted source or implementation decision.
- **D06 — stack candidate:** Python/FastAPI/Pydantic, React/Three.js, local SQLite/files and one model service. Exact versions/model/native backend require B01/B09 smoke. Warp is a candidate, not a proven dependency; RT-core acceleration is not claimed.
- **D07 — organiser rules unresolved:** advance-code/assets/AI use, prior-work declarations, exact deadline, demo format, repository/IP requirements and supplied runtime. Ben coordinates an approved sender; no message sent by these docs. Keep the confirmation source and date here.
- **D08 — repository established (Ben's approval, 11 November):** [bbeennyy860-cyber/sheffield-tree-planner](https://github.com/bbeennyy860-cyber/sheffield-tree-planner) is the private canonical repository; Ben is the owner/admin. Write access is authorised for Alex Kurkar (`akurkar07`) and Arnav Chitriv (`reverez`), verified from the Originator project and their GitHub profiles. Invitation acceptance/live access is determined by GitHub, not inferred from this record. `docs/` is the living specification; earlier local/ZIP copies are historical. This approval covers initial docs publication and those invitations, not arbitrary later pushes, public visibility, licensing, spending, deployments or submission.

- **D09 — Spark preparation (Ben's approval, 11 November):** access is only at the event. Prepare and publish a private draft PR with SSH/deployment documentation and tested inference-connection tools; request no reviewers. Actual device configuration, credentials, deployment, tag/release publication and submission retain their separate gates. Prefer an authorised preloaded local model that passes the real tool check; the pinned Nemotron BF16/vLLM profile is a candidate for a confirmed 128 GB unit. The final target places the application, jobs and numerics on Linux ARM64 Spark as well as inference; a laptop backend over SSH is an intermediate mode, not final deployment proof. [DGX_SPARK.md](DGX_SPARK.md) describes the route and failure boundaries.

- **D10 — architecture/feature research publication (Ben's approval, 11 November):** publish the [agentic feature review and team inputs](references/AGENTIC_FEATURE_REVIEW.md) in this private repository's docs. It compares inspected projects, recommends evidence-directed stress-test → controlled repair-or-explain, and records a partial project-link capture. Ben explicitly directed that remaining WhatsApp messages be skipped; no full transcript, private contacts, screenshots or unrelated messages are published. Documentation-only publication does not approve a merge, runtime deployment or new model/data claims. **Decision owners:** Ben, Alex and Arnav. **Next action:** acknowledge the expanded target's supported concern cases and reconcile any changed shared meanings before implementation. Evidence is primary documentation/source inspection, not competitor execution or a demonstrated agent advantage.
- **D11 — capacity and source ownership update (Ben, 11 November):** Ben reports substantial Claude Max/GPT Pro development capacity across the team and invited a more ambitious build target. The review maps a complete planning workbench onto the existing B01–B12/G1–G4 sequence, with parallel isolated writers and independent verification. It does not create another backlog or mark tasks complete. **Alex is collecting the sources; SOURCES and B03 remain the canonical source/site lane.** Preserve Alex's current additions and coordinate source/manifest writes with him. Shared implementation roles still require acknowledgement; subscription access does not establish API entitlement, Spark readiness, data rights or permission to spend.

- **D12 — comprehensive research dossier (Ben's publication approval, 11 November):** combine the earlier research and the extensive research mandate into one [fourteen-part dossier](references/DEEP_RESEARCH_DOSSIER.md) under `docs/`, published on the existing draft research PR. **Recommendation:** modify and continue, emphasising local, auditable, survey-aware decisions rather than generic agentic tree optimisation. The dossier includes 170 annotated source records, primary data-schema checks, mathematical/scientific limits, same-tools agent benchmarks, B01–B12 handoffs, P0/P1/P2 recommendations and document-specific amendments. **Owners:** Ben/Arnav/Alex for accepting changes; source/site ownership remains B03 and SOURCES. **Next action:** agree the decision target and contract/frame clarifications, then advance B01/B03 and the existing G1 spine. **Evidence:** independent final narrative/source-registry review found no blockers; minor annotation/alias issues were corrected; citation identity/evidence and document-link checks passed; a standalone synthetic formulation audit passed. These do not establish an implemented evaluator, accepted real site, agent advantage or Spark runtime. **Gate:** shared specification changes need affected-owner acceptance; draft publication does not authorise readiness, reviewer requests, merge, deployment or submission.

Risk triggers and fallback: missing real geometry/rights → another audited site, while synthetic engineering continues; untrusted numerics → analytic CPU reference and reduced supported claims; Spark/model failure → manual product still usable but local-agent gate incomplete; overloaded numerical lane → stable evaluator/mask handoffs; shared-file conflict → stop/reconcile one writer; late UI edit → stale identity guard; undocumented benefit → remove that claim, not invent a model.

- **D13 — Arnav's research-to-design adoption (11 November; team interface gate open):** Arnav explicitly requested formal inclusion of Ben's useful research recommendations into the living product design. Adopt as product-direction guidance: local and auditable decision workbench; concern-driven fixed-layout stress test before optional constraint-preserving repair; honest stable/no-change result; agent-selected evidence gathering; decision-sensitive survey question when real tested alternatives differ; same-tools manual/fixed/agent comparison; only validated shade/upfront cost claims initially; CPU numerical truth before optional GPU claims. Details and scope are in [SPEC section 10](SPEC.md) and [VALIDATION section 8](VALIDATION.md). Preserve F013 as P1 with a preferred judge-facing demo; promotion to hard P0 is **not** agreed. This records **Arnav's acceptance only**; Ben/Alex still must acknowledge any affected ownership, product-gate or shared interface decisions. No CONTRACTS or NUMERICS wire/math semantics changed, no implementation verified, no source licence/site/eligibility cleared. **Next:** Ben/Arnav/Alex accept the minimum concern test and interface revision; Alex packages bounded work. Research bibliography remains a reference, not competing code instructions.
- **D14 — UI artifact reference registered (11 November; content inspection pending):** Arnav supplied [a Claude-generated UI artifact](UI_DESIGN_REFERENCE.md) as an existing design. The external artifact's actual screens/source could not be inspected via available tools. The linked reference and requirements-to-interface handoff are recorded, **not** an invented screen transcription or proof of implemented UI. Alex obtains/export-checks the artifact, records exact actual components/layout/interactions and reconciles them against SPEC/CONTRACTS/F001–F018 before B05 delivery. No UI code, screenshot or artifact bytes were committed here.

## 6. Task changes, evidence and advance-work record

Task states: `Planned → Ready → Active → Review → Integrated → Verified`, with `Blocked`/`Deferred` when appropriate. Before a shared repository exists, record the exact local baseline/files; do not invent a merged commit. Once a tracker is adopted, it becomes the single status home and this file becomes the roadmap with links, not a second live board.

For each active item record inline: human owner; actual writer; agreed spec/schema revision; starting code revision or explicit local-only state; owned paths; shared/forbidden paths; dependency IDs; permitted side effects; acceptance IDs; test commands/results; checks not run; reviewer; final revision; blocker/next action. A model's self-review is not independent acceptance.

Shared contracts, lockfiles and integration files have one writer. Use short branches and isolated worktrees/clones after a repository exists. Coordinated schema changes land with consumers/adapters and compatibility tests. Review the final diff and verify the integrated baseline. No automatic force-push, PR publication/reviewer requests, merge, permission change or deployment authority is conferred here.

**Advance-work entries belong here**, not in a new diary. Record date, author(s), task/change, assets/dependencies, AI assistance, source revision and any event declaration needed. Do not backdate work or conceal reuse.

- **11 November 2026 — documentation only:** existing researched design converted into this living specification by Ben's requested AI-assisted preparation. No project application implementation or Spark run established by this entry. Prior source/audit/arithmetic evidence is in the background handoff; it is not a new site simulation.

- **11 November 2026 — repository bootstrap:** private repository and initial development-doc publication approved by Ben, with write-access invitations authorised for the two verified teammates. Application tasks remain Planned; no remote CI, product tests or Spark run is implied.

- **11 November 2026 — B09 readiness implementation:** approved AI-assisted preparation added the portable diagnostic, synthetic protocol tests, pinned deployment candidate and operational guide on `feat/dgx-spark-readiness`, based on `625a6ee8fe97bef5d7d428e2034afa09f4156d6d`. Implementation used a scoped Codex worker and parent integration; review/build/test receipts accompany the PR. This entry is advance work and must be disclosed if required. No scientific output, real-model inference or Spark execution is established.

- **11 November 2026 — Defra LiDAR candidate desk review:** added a potential 1 m DTM/DSM source to SOURCES and the B03 investigation lane. Official metadata/FAQ reviewed; no Sheffield tiles downloaded, preprocessing demonstrated, site selected, permissions independently approved or real-site solver output obtained. Site audit and acceptance stay Planned.

**Documentation review:** independent supplied-text contract review found six material gaps; they were corrected and the follow-up returned PASS. The corrections define same-revision result selection/cache delivery, hypothetical-scenario authority, catalogue version identity, deadline outcomes, phase-specific acceptance and the first dependency order. Cross-scenario metric identity and infeasible-comparison handling were also clarified. This is documentation consistency evidence, not implemented software or scientific validation. The earlier distributed documentation archive contains its snapshot integrity manifest; checks must be rerun against each new repository revision.

After the contract/owner acknowledgement, begin B01 and B03 in parallel. B02 integration starts when the relevant B01 models are available; Arnav may independently explore analytic formulas against this named draft before then, but that is not integrated B02 acceptance. Do not hold all engineering hostage to real-site selection or future hardware access.

## 7. Priority-aware delivery plan

The canonical catalogue, feature acceptance, P0–P3 boundaries and M0–M7 gates are in [FEATURE_PRIORITIES.md](FEATURE_PRIORITIES.md). B01–B12 remain the only implementation/task IDs and the only task-status home. These phases organise delivery; they do not mark planned work complete or replace any B/V acceptance.

| Milestone | Existing tasks | Exit condition |
|---|---|---|
| M0 Development readiness | B01, B03; start B09 readiness investigation when available | Acknowledged contract/owners, tested portable setup/interfaces, and event/data-rights gates recorded with unknowns explicit. |
| M1 Scientific foundation | B02, B04; B03 only gates real-site claims | Analytic solar/geometry references and reproducible baseline-versus-one-tree calculation, including valid zero. |
| M2 First vertical slice | B01, B04, B05 | Real request→calculation→UI result; edits immediately stale old values; failure/zero/provisional states shown. No optimiser, polished 3D or model prerequisite. |
| M3 Basic optimisation | B06 | Feasible finite-candidate layout, independent constraint validation, reference comparison and truthful objective/status. |
| M4 Early local tool proof | B01, B09; B10 consumes it later | Genuine local model chooses a registered implemented tool, dispatches it, observes actual output and gives grounded response with device/version evidence. Can run beside M1/M2; advanced B07 sensitivity is not a prerequisite. |
| M5 Agentic replanning | B05/B06/B09/B10 | Accepted budget/constraint change drives the correct real operation; B10's full adaptive investigation acceptance remains intact. |
| M6 Selected P1 enhancements | B07/B10/B12 | Chosen growth/season/sensitivity/counterfactual/report features pass their mapped V criteria; no mandatory constraint omitted. |
| M7 Submission candidate | P0-relevant B08/B09/B12 evidence, plus actual entry gate | Peer-reproducible demo and claim ledger for the scope actually shown; site, runtime, fallback and event eligibility claims evidenced. This scoped candidate does not mark B12 or B11 fully Verified. Full B12 still retains its stated B05–B11 dependencies and V12 acceptance. |

**P0 versus first slice:** P0 is the complete competitive MVP, not M2. P0 needs F001–F010, including a constrained proposal, actual metrics/cost, user-driven recomputation and real local Nemotron tool round-trip. Basic replanning can be manual UI/API work in B05/B06 while B09 proves one early model tool call. This limited B09 evidence is not B10 completion. F013's richer counterfactual agent and B10's full adaptive loop remain P1 work with the original V09 acceptance; B07's full comparisons/sensitivity and B11 agent-value comparison are not prerequisites for the M2 slice. A demonstrated feature still passes its applicable checks.

**Critical path:** B01→B02/B04→B05→B06→B10→B11/B12 for the full planned system. B03 runs in parallel against a candidate/fallback and gates real-site claims at B08, not synthetic engineering. Start B09 when schema and permitted runtime are available, not after B07. Leave time before the verified deadline for integration, affected validation, claim/evidence capture, recovery and pitch.

**Proposed lanes (unacknowledged until owners agree):** Ben—backend foundation, typed API, scenarios/jobs, dispatcher, Nemotron, DGX and integration; Arnav—geospatial processing, solar/canopy physics, optimisation, numerical validation and uncertainty; Alex—map/3D view, controls, comparisons, evidence panels and demo interaction. Shared: Ben/Arnav numerical result contract; Arnav/Alex coordinate/render agreement; Ben/Alex revision, async and stale-state behaviour. One human owner and one writer per task/shared file. Change contracts only with affected producers/consumers coordinated; use isolated worktrees for parallel work.

**Feature admission and freeze:** confirm the actual event deadline/rules before setting a freeze. After freeze, take defect fixes, affected validation, evidence, recovery and demo-critical work only. Before freeze, admit P1/P2 only when dependencies are ready, method/data/rights are adequate, its mapped V acceptance fits, and it cannot consume the P0 integration/evidence reserve. P3 does not enter the hackathon critical path.

**Existing-plan interpretation:** B07 contains the full growth, season, sensitivity and comparison work; B10 contains the full adaptive investigator; B11 compares that agent with manual/fixed workflows; B12 remains the full reproducible candidate. Staging early B09 and a P0 manual replanning path does not reduce those tasks' final acceptance or claim their completion.

### Documentation update record

- **Scope/revision:** user-assigned feature-priority documentation update on branch docs/feature-priorities-mvp, based on fetched origin/main revision 14d0ce8. No pre-existing B01–B12 item was assigned to this documentation task; this record is in the existing BUILD plan and does not create an implementation task or change task states.
- **Implementation commit:** d2ae0aa79eb86eabfc5ed15dad9f59ab3f4ca157; the feature-plan change passed the recorded checks at this revision.
- **Files:** AGENTS.md, README.md, docs/README.md, docs/SPEC.md, docs/CONTRACTS.md, docs/BUILD.md, docs/VALIDATION.md, and new docs/FEATURE_PRIORITIES.md.
- **Checks actually run:** local Markdown path/anchor audit (54 local links/anchors; PASS); feature/reference audit (F001–F035 and referenced R/B/V IDs; PASS); git diff --cached --check (PASS on the final staged documentation diff before commit).
- **Tests not run:** no application tests or runtime/model/site checks; this branch changes documentation only and does not claim numerical, Sheffield-site, DGX, or Nemotron evidence.
- **Interface impact:** no wire fields, units, states, error codes, revision rules or numerical definitions changed. CONTRACTS only identifies when existing operations enter milestones; NUMERICS and SOURCES were reviewed and left unchanged.
- **Limits/next dependency:** priorities, owners and event timing remain proposed/unacknowledged; no site, runtime or eligibility gate is resolved. Next: review this scoped PR and any repository checks; teammates acknowledge lanes/contracts before parallel dependent implementation.
