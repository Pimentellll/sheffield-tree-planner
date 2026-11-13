# CANOPY SHEFFIELD — FRONTEND IMPLEMENTATION MASTER HANDOFF

> **Provenance:** written by Arnav on 13 November 2026 as the brief for implementing [Product Vision v2](README.md) in the existing frontend. Reproduced as given. "The attachment" below is `CANOPY_Sheffield_Product_Vision_v2.html`, kept on the reference branch `ref/arnav/product-vision-v2-design` (see the [README](README.md) for the link and why it is not on `main`). This is an assignment brief, not a record of completed work.

## ROLE

Act as a principal frontend engineer, React/TypeScript architect, Three.js interaction engineer, UX implementation specialist, and independent QA reviewer.

Your task is to **implement the CANOPY Sheffield Product Vision v2 design into the existing working application**.

This is a software engineering execution task, NOT a design ideation task.

I am attaching:

**CANOPY Sheffield — Product Vision v2.html**

The file contains eight high-fidelity product design artboards.

You must inspect the actual visual and structural contents of the file, extract its design patterns, map the artboards to the current application architecture, and implement them as functioning React components.

Do not simply produce another HTML mockup, a static screenshot, an implementation plan, or a collection of disconnected pages.

**The intended deliverable is a running, tested, integrated CANOPY frontend, committed on an isolated branch with a reviewable pull request.**

Work autonomously through investigation, implementation, testing and review, making sensible engineering decisions without repeatedly requesting approval.

---

# 1. CANONICAL REPOSITORY

https://github.com/Pimentellll/sheffield-tree-planner

The existing project uses:

- React 19
- TypeScript
- Vite
- Three.js
- A Python numerical/backend application
- Typed scenario, layout, result and job contracts
- An existing physical-scene viewer
- An implemented synthetic numerical evaluation/search path
- Developing local agent integration

Do not start a new frontend repository or discard the existing application.

## Repository inspection — mandatory

First fetch the latest repository state.

Inspect:

- `docs/BUILD.md`
- `docs/SPEC.md`
- `docs/CONTRACTS.md`
- `docs/NUMERICS.md`
- `docs/VALIDATION.md`
- `docs/ARCHITECTURE_DESIGN.md`
- `docs/UI_DESIGN_REFERENCE.md`
- `docs/FEATURE_PRIORITIES.md`
- `docs/EVENT_DAY_EXECUTION_2026-11-13.md`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `frontend/src/scene/SiteScene.tsx`
- `frontend/src/scene/transform.ts`
- `frontend/src/planning/`
- `frontend/src/panels/`
- `frontend/src/api/`
- `frontend/package.json`
- Frontend tests and browser-test scripts

Also inspect these implementation specifications, including their PR versions if not merged:

- PR #66 — Geospatial 3D city and tree-identification architecture
- PR #67 — 3D UI, agent UX and implementation tracker
- PR #70 — Nemotron harness and agent-run architecture audit
- PR #71 — Agent evidence UI and frontend resilience handoff
- PR #75 — Agent async observation interface changes, if still open/relevant

Do not assume PRs are merged. Fetch the actual head, PR diffs and active integration branches.

Use `BUILD.md` and the running code as the authority for what is implemented; historical design documents are not implementation proof.

## Team coordination

The project is under active parallel development.

- Arnav: product/frontend direction and scientific acceptance
- Ben: backend, integration, model connectors and deployment
- Alex: presentation, visuals and frontend review

Inspect the current branch and open PRs before modifying code.

Do not overwrite active work by another developer or agent.

Do not force-push, blindly merge divergent branches, reset shared worktrees, modify Spark deployments, or change backend contracts without coordination.

Prefer changes isolated to the frontend.

Develop on a fresh feature branch based on the appropriate latest integration baseline. Open a PR for review rather than pushing directly to `main`.

---

# 2. UNDERSTAND THE ATTACHED PRODUCT VISION ARTIFACT

The attachment is a bundled HTML gallery containing eight 1600 × 1000 artboards.

Extract and inspect the individual pages. Do not mistake the outer HTML bundler for the actual reusable component source.

The artboards are:

| ID | Design |
|---|---|
| B07 | Flagship Planting Studio |
| B08 | Selected proposed tree and shadow footprint |
| C01 | Budget and constraints editor |
| C02 | Stale result after draft modification |
| C03 | Running numerical evaluation/search |
| C04 | Completed result and provenance |
| C05 | Search alternatives and candidate ranking |
| C06 | Scenario comparison |

Study each screen's layout, typography, spacing, colours, components, legends, visual hierarchy, card composition and intended interaction.

The artifact should be your **primary visual reference**.

The repository's design and scientific specifications determine correct functionality.

### Important interpretation

The eight screens depict states and sub-workspaces of one connected application.

Do not implement eight unrelated routes with duplicated layouts and hardcoded information.

For example:

- B07 is the default Studio.
- B08 is a selected-tree state of the Studio.
- C01 is a scenario-editing state.
- C02 is the state after modifying a draft.
- C03 is the active evaluation/search state.
- C04 is a completed-result/evidence state.
- C05 is an alternative-layout analysis state.
- C06 is the Compare experience.

Implement these as a coherent application with shared state, reusable components and genuine event handling.

---

# 3. CRITICAL SOURCE AUDIT

Before implementation, inspect the artifact for inconsistencies and gaps.

Several are already known.

### A. Budget inconsistency

The C01 artboard displays £64,000 in the budget editor but shows a draft conversion of 7,500,000 pence and a change summary from 6,400,000 to 7,500,000 pence.

The intended example appears to be a budget change from £64,000 to £75,000.

Correct this through the actual controlled input and scenario model. Never hardcode contradictory budget values.

### B. Invented runtime metrics

The artifact contains example data such as:

- 39 proposed trees
- £74,300 upfront cost
- 5,520 m²·h additional shade
- 157 candidate positions
- Run IDs and job timings

These are DESIGN EXAMPLE values, not evidence that the current backend has produced those specific results.

In the application, numerical values must come from actual backend observations or clearly identified synthetic/test fixtures.

Never portray an example value as a live computation.

### C. Unsupported progress phases

The C03 artboard depicts detailed phases and numerical progress.

Determine whether the current job API actually reports those phases.

If not, implement truthful queued/running status and an indeterminate progress indicator instead of fabricating phase counts or percentages.

### D. Tree-specific marginal contribution

The B08 artboard shows marginal shade for one selected tree.

Confirm whether the current API can provide an exact remove-one or controlled comparison measurement.

Do not derive this metric from an unrelated layout total or candidate ranking.

If unsupported, show the source-backed information that is available and mark marginal contribution as not computed.

### E. Shadow footprint

The B08 artboard depicts swept shadow footprints and time-specific shadow ellipses.

These may be useful visual overlays, but the existing Three.js viewer does not necessarily expose those exact quantities.

Distinguish illustrative visual overlays from numerical receiver-sampled shade evidence.

### F. Agent capability

The B07 artboard says the agent has seven registered tools.

Display the actual supported operations and current model status from the running application.

Do not fake a Nemotron model connection or a completed tool investigation.

### G. Scientific feature boundaries

Heat, flood, AQI, carbon and other environmental benefits are not equivalent to geometric shade.

Unsupported measurements must not appear as real computed benefits.

### H. Candidate ranking semantics

C05 describes marginal shade from candidate positions and includes selected placements.

Audit whether those values represent adding, removing, swapping or relocating a tree. Each operation has different mathematical meaning.

Correct labels and calculations to match actual supported evaluation methods.

Create a brief artifact-to-implementation discrepancy register before proceeding, then resolve problems through code or an explicitly labelled unsupported state.

---

# 4. IMPLEMENTATION OBJECTIVES

The final UI should preserve the attachment's sophisticated visual style while making its core workflows operational.

## Priority P0 — Functional flagship experience

Implement:

1. New application shell and visual design system
2. Flagship Planting Studio composition
3. Functional existing Three.js scene integration
4. Existing/proposed tree and candidate selection
5. Budget and supported constraint editing
6. Explicit draft/accepted scenario separation
7. Stale-result and superseded-result behaviour
8. Actual evaluate/search job requests
9. Loading, completed, cancelled and failed job states
10. Current numerical result and provenance presentation
11. Functional navigation and responsive layout

## Priority P1 — Enhanced investigation experience

Implement where supported:

1. Selected tree inspector
2. Tree-profile and crown-state information
3. Search alternatives panel
4. Candidate ranking
5. Scenario comparison
6. Run history and evidence drawer
7. Agent investigation UI linked to real registered tools
8. Human approval for consequential scenario revisions
9. Review-pack navigation
10. Camera, layer and geometry controls

## Priority P2 — Separate geospatial extension

Prepare the UI architecture for:

- Actual georeferenced city terrain
- Sheffield building geometry
- Recorded existing-tree points
- Inferred canopy objects
- Multi-resolution 3D city exploration
- Source-backed tree selection

Do not block the functioning Studio redesign on unacquired LiDAR or unvalidated real-site geometry.

Do not attempt an unrequested complete citywide ingestion pipeline as part of this frontend PR.

If a city viewer can be introduced independently using verified existing assets without risking the core application, use a clean modular boundary. Otherwise document its implementation seam.

---

# 5. DESIGN SYSTEM IMPLEMENTATION

Retain the attachment's visual language and reconcile it with the current CSS.

Primary CANOPY tokens:

- Forest: `#101E1B`
- Pine: `#243D35`
- Lime: `#B7E879`
- Ivory: `#F4F3ED`
- Water: `#62AFC2`
- Heat: `#E8A476`
- Constraint: `#D67C64`
- Canopy: `#527A55`

Typography:

- Manrope for headings
- Inter for interface elements
- JetBrains Mono for numerical values, units, IDs and revisions

Use CSS variables/design tokens.

Create reusable styles and components for:

- Navigation
- Context breadcrumbs
- Scenario state indicators
- Information cards
- Metric cards
- Tree inspectors
- Legends
- Map overlays
- Constraint controls
- Agent panels
- Job status
- Run history
- Comparison layouts
- Empty/error states
- Review actions

Use existing locally available or legally usable assets. Preserve relevant attribution and font licences.

Do not turn the product into a generic component-library dashboard.

The 3D viewport should remain visually dominant.

Avoid excessive permanent sidebars, unreadably small labels, overwhelming shadows, gratuitous animation and excessive glassmorphism.

---

# 6. APPLICATION COMPONENT ARCHITECTURE

Refactor only as much as necessary.

The exact component structure should be derived from existing code, but a reasonable target decomposition is:

**Application shell**
- AppShell
- NavigationRail
- WorkspaceHeader
- SiteContext
- StatusIndicator

**Spatial workspace**
- StudioWorkspace
- SceneViewport
- SceneToolbar
- CameraControls
- LayerManager
- SceneLegend
- TreeSelectionOverlay

**Scenario workflow**
- ScenarioControls
- BudgetEditor
- ConstraintEditor
- ScenarioChangeSummary
- ScenarioApproval
- ScenarioStatus

**Numerical evidence**
- MetricSummary
- ResultInspector
- ResultStatus
- RunHistory
- AlternativesPanel
- CandidateRanking
- ProvenanceDrawer

**Tree inspection**
- TreeInspector
- TreeProfileDetails
- ShadowFootprintOverlay
- ConstraintDiagnostics

**Agent**
- AgentLauncher
- AgentInvestigationDrawer
- ToolActionTimeline
- ToolObservationCard
- AgentEvidenceSummary
- HumanReviewCard

**Comparison**
- ScenarioCompareWorkspace
- ComparisonScene
- DifferenceSummary
- TradeoffInspector

Do not create redundant components if existing ones already satisfy the contract.

Reuse current typed APIs, scenario state hooks and numerical utilities.

Avoid copying the same mutable state into multiple disconnected local components.

---

# 7. FUNCTIONAL DATA INTEGRATION

The application must be driven by genuine state.

The critical state identities include:

- Site ID and revisions
- Scenario ID and revision
- Accepted scenario reference
- Draft edits
- Layout ID and revision
- Candidate catalogue revision/fingerprint
- Selected feature ID
- Selected evaluation case
- Current job ID
- Selected run/result ID
- Result currentness
- Source/evidence status

Do not store unrelated copies of authoritative backend data that can silently diverge.

## Budget editing

The budget must be represented correctly in integer GBP pence in the domain layer.

Editing £64,000 to £75,000 creates a draft.

An existing result cannot automatically become the result for the new draft.

The user must see the change, accept the revision through the appropriate backend authority, and initiate or select a valid new evaluation.

## Evaluation and search

Use real registered operations such as:

- `evaluate_layout`
- `search_layouts`

Submit jobs through the existing backend interface.

Observe terminal job states.

Read validated results.

Display only those result fields supported by the actual contract.

Do not invent an optimiser response or simply reset a loading indicator when the user clicks Generate.

## Stale results

Immediately differentiate:

- Current accepted result
- Draft differs from accepted scenario
- Superseded historical result
- Pending new computation
- Current completed result
- Cancelled/failed result

A late response for an old revision must not overwrite the selected current result.

Preserve previous results for inspection, with correct revision identity.

## Alternatives

If the backend returns multiple evaluated layouts, show them as selectable alternatives.

Display:

- Layout ID
- Tree count
- Upfront cost
- Physical shade metric
- Feasibility
- Selected objective
- Constraints
- Run and scenario reference

Do not label a heuristic result globally optimal unless that property has actually been established.

## Comparison

Build comparison displays from compatible backend results.

Ensure both sides use compatible:

- Site geometry
- Evaluation cases
- Targets
- Units
- Budget basis
- Profile assumptions
- Scenario identity

Show exactly which inputs changed.

Reject misleading controlled comparisons when assumptions differ without disclosure.

---

# 8. THREE.JS SCENE IMPLEMENTATION

Preserve the working Three.js rendering infrastructure wherever possible.

The implementation should improve the existing viewport rather than replacing it with a static image.

Required interactions:

- Orbit
- Pan
- Zoom
- Camera reset
- North indicator
- Scale reference
- Candidate selection
- Tree selection
- Proposed-tree highlighting
- Contextual feature inspection

When supported, implement:

- Selectable tree crown and trunk
- Proposed tree ghost during editing
- Target-region visibility
- Exclusion-region visibility
- Candidate markers
- Layout comparison overlays
- Selected tree footprint
- Evaluated solar position/visualisation

## Coordinate correctness

Preserve the existing ENU coordinate conventions and explicit viewer transform.

Do not silently reinterpret real-world geographic coordinates or treat a provisional visual transform as validated geodesy.

## Scene semantics

Visually distinguish:

- Existing recorded trees
- Inferred canopy
- Proposed trees
- Selected proposal
- Available candidates
- Excluded candidates
- Survey-required locations
- Target surfaces
- Static obstructions

Only show real-data classifications when backing feature records actually exist.

If a source lacks an attribute, show Unknown or Not recorded.

## Performance

Avoid unnecessary reinitialisation of the WebGL renderer.

Use appropriate geometry reuse, memoisation, disposal, batching and instancing.

Keep rendering state separate from backend scenario authority.

Measure performance under representative scenes.

Do not replace functioning local graphics with a larger third-party GIS stack unless justified and independently tested.

---

# 9. AGENTIC AI INTEGRATION

The assistant must be an evidence-investigation tool, not a decorative chat widget.

First inspect the current agent service, active PRs and actual supported tool contracts.

Coordinate with Ben's ongoing backend/model work.

Do not rewrite the model runtime.

## Supported interaction

A user selects a planting position and asks:

"Why this tree position rather than one closer to the path?"

The frontend should:

1. Capture the currently selected feature and accepted scenario.
2. Send the question through the supported agent interface.
3. Display the model/tool availability.
4. Present actual selected tool actions where available.
5. Show queued/running/completed observations.
6. Link results to real IDs and numerical evidence.
7. Present the grounded explanation.
8. Show a human review action if a scenario change is proposed.

The agent must not manufacture physical quantities.

## Agent states

Implement appropriate UI for:

- Available
- Model unavailable
- Investigating
- Tool selected
- Job queued
- Job running
- Result received
- Failed tool call
- Unsupported request
- Proposed hypothetical scenario
- Awaiting human decision

If the actual agent backend is not yet integrated, build the component against the documented typed interface and show a truthful unavailable state.

Do not simulate a successful model investigation in production.

Test manual planning independently of the model.

---

# 10. SCIENTIFIC AND EVIDENCE SAFEGUARDS

Preserve the repository's scientific boundaries.

A synthetic scene is not a verified Sheffield site.

A 3D rendered crown is not necessarily surveyed vegetation.

Geometric direct shade does not establish degrees Celsius of cooling.

A heuristic candidate ranking does not establish planting permission.

A model-generated recommendation does not equal a human-approved scenario.

Use correct units:

- GBP pence internally
- GBP in UI
- `m²·h` for physical shade integrals
- Separate `weighted_m²·h` utility when supported

Show accurate run/provenance labels.

Display numerical zero distinctly from not computed.

Show unknown constraints distinctly from passed constraints.

Never suppress important source or scientific warnings to improve appearance.

---

# 11. TESTING REQUIREMENTS

This project already has frontend unit tests and browser-check scripts.

Inspect their current behaviour, preserve successful cases and extend coverage.

Relevant commands include:

```bash
cd frontend
npm ci
npm run build
npm test
npm run test:browser
npm run test:physical
```

Adapt commands only where the actual repository environment requires it.

## Minimum functional tests

Test:

1. App loads with backend connected.
2. App loads without backend.
3. Navigation between Studio, Compare and Review works.
4. Selected tree state updates the inspector.
5. Scene/candidate selection retains correct identity.
6. Budget edits mark previous results stale.
7. Draft discard restores accepted values.
8. Accepted scenario revision is correctly bound.
9. Search submits the proper job.
10. Running job does not show fictional progress.
11. Completed job displays the actual result.
12. Cancelled job does not create a fictional completed plan.
13. Failed job preserves appropriate last-known evidence.
14. Late results cannot overwrite a newer selection.
15. Alternatives display exact layout data.
16. Scenario comparison preserves compatible cases.
17. Unsupported environmental metrics are not fabricated.
18. Agent unavailable mode is truthful and does not block manual operation.
19. Synthetic status remains visible.
20. Keyboard navigation and responsive layouts remain usable.

## Visual review

Capture actual running application screenshots at:

- 1920 × 1080
- 1600 × 1000
- 1024 × 768
- Approximately 390 × 844

Compare the resulting application against the attached B07–C06 artboards.

Check hierarchy, spacing, typography, rendering, selection, controls, content density and responsive behaviour.

Do not declare visual parity purely from a successful build.

---

# 12. IMPLEMENTATION EXECUTION STRATEGY

Use an iterative engineering pipeline, but perform implementation rather than stopping at the plan.

### Phase 1 — Inspect

Read the repository and attached design.

Identify the actual main/integration baseline and conflicting open PRs.

Create a concise implementation matrix describing:

- Existing components that can be reused
- New components required
- Missing backend capabilities
- Design discrepancies
- Potential source conflicts
- Tests required

### Phase 2 — Design-system integration

Introduce or refine CSS variables and reusable UI components.

Build the application shell and flagship B07 layout first.

Retain backend connectivity throughout.

### Phase 3 — Functional Studio

Implement B08, C01, C02, C03 and C04 through shared application state.

Ensure correct scenario editing, tree selection, actual jobs and evidence.

### Phase 4 — Alternatives and comparison

Implement C05 and C06 using genuine result data and existing domain operations.

### Phase 5 — Agent experience

Integrate the agent investigation UI against the current real interface.

If backend capability is incomplete, preserve the frontend seam and truthful unavailable states.

Do not invent a fake operational model.

### Phase 6 — Audit and improve

Run tests.

Inspect screenshots.

Compare against the design.

Find and fix layout, state-management, interaction and scientific-presentation defects.

Repeat affected tests.

### Phase 7 — Integration handoff

Commit the completed implementation to your isolated branch.

Open a reviewable PR targeting the appropriate current integration branch, with the final destination of `main` after team review.

Include a clear summary, screenshots, test results, remaining limitations and any backend integration dependencies.

Do not merge without the appropriate team review.

---

# 13. TIME AND PRIORITY MANAGEMENT

This is being executed during the 13 November 2026 NVIDIA hackathon.

Protect the working numerical demonstration and current DGX integration.

The priority order is:

**First:** functional and visually improved Studio.

**Second:** correct results, scenario states, alternatives and comparison.

**Third:** agent evidence UI integration.

**Fourth:** optional 3D city expansion and additional polish.

Do not spend the critical implementation window rebuilding the geospatial data pipeline, changing numerical contracts or introducing a new frontend framework.

Do not disrupt Ben's existing model infrastructure or Alex's presentation/video work.

If the entire design cannot be implemented safely in the available working session, land a genuinely functioning, tested vertical slice and record the remaining work precisely.

A smaller working implementation is better than a beautiful but disconnected prototype.

---

# 14. COMPLETION CRITERIA

The implementation is successful when:

- The application looks substantially like the attached Product Vision v2.
- The main Studio layout is polished, cohesive and responsive.
- The 3D scene remains interactive.
- Core planning controls use real application state.
- Budget changes create the correct draft/stale experience.
- Evaluation/search operations call the existing backend.
- Completed numerical results come from actual result contracts.
- The alternatives and comparison interfaces use compatible result data.
- The agent interface reports actual capability and tool observations.
- Scientific uncertainty and provenance remain visible.
- The working application passes relevant tests.
- Screenshots demonstrate the implementation.
- A reviewable PR exists, with implementation and limitations documented.

Do not claim a feature is complete merely because a control is visible.

Do not claim a test passed unless it ran and passed.

Do not claim a DGX or Nemotron run unless actual hardware/model execution evidence exists.

---

# 15. FINAL RESPONSE FORMAT

When implementation concludes, provide:

**A. Implementation summary**

What was implemented and how closely it matches B07–C06.

**B. Architecture changes**

Important files, components, state flows and API integrations.

**C. Verification evidence**

Tests executed, pass/fail counts, screenshots and any browser observations.

**D. PR handoff**

Branch, commit SHA, PR URL, reviewers and merge status.

**E. Remaining issues**

Specific incomplete capabilities, backend dependencies, blockers and appropriate owners.

**F. Demo instructions**

Exact commands and user interactions needed to launch and demonstrate the improved interface.

Do not stop after providing the initial plan.

Begin by inspecting the attached HTML and current repository, then proceed directly into implementing the highest-priority functioning UI.
