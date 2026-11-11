# UI design reference and implementation handoff

**Source supplied by Arnav (11 November 2026):** [Claude UI artifact — supplied page](https://claude.ai/artifact/2ZbqmnjEJ1vn2mDvjeK2bQ#page-dcb81aee8d83).

**Evidence/access status:** Arnav reports that the UI design is complete. The linked Claude artifact could **not be opened or inspected** with the connected tools used for this documentation change. Therefore **no actual layout, typography, component, screenshot, source code, interaction, completeness or implementation status has been verified from that artifact**. The link is a *design reference*, not a checked-in UI implementation. Do not infer that its contents match the requirements below. Alex should export/share the actual artifact source or screenshots and perform the comparison before claiming visual fidelity.

**Authority:** [SPEC](SPEC.md) defines product behaviour; [FEATURE_PRIORITIES](FEATURE_PRIORITIES.md) defines P0/P1 feature priority; [CONTRACTS](CONTRACTS.md) defines data and tool semantics; [VALIDATION](VALIDATION.md) defines truth/evidence; [BUILD](BUILD.md) owns implementation status. This document is the bridge between those accepted requirements and the separately supplied visual reference. It does not replace or silently amend any of them.

## Intended experience — requirements derived from the approved product design, NOT from inspection of the Claude artifact

The application is a site-first, interactive decision workbench. A user should be able to:
1. Select the accepted Sheffield study site, see whether the data are real/verified or synthetic, and inspect source/rights/survey gaps.
2. Set a planning budget, target surfaces, relevant evaluation periods, known exclusions and supported objective. Show initial GBP upfront-cost scope and explicit units.
3. Explore existing conditions and proposed tree positions on a georeferenced 2D/3D map. Geometry, north, positions, shading and metric labels must agree with the deterministic evaluator.
4. Start a genuine evaluation or constrained placement search. Show the current job/revision, activity status and exact results; allow a usable form/keyboard path, not only drag controls.
5. Compare the accepted layout and evaluated alternatives with actual cost, additional shade in m²·h, separate winter effects and known model-feasibility checks; identify changed inputs and limitations.
6. Edit budget, placements or supported constraints; immediately mark displayed prior results as stale and require computation on the newly accepted scenario before calling the values current.
7. Ask the local Nemotron agent to investigate a challenge. Show the question, selected registered tool, input/scenario identity, observation/result references, tested concern, and repair-or-explain disposition.
8. Review evidence and, when implemented and rights-permitted, prepare a proposal for professional survey. Never imply physical planting authorisation.

## Proposed map / controls / evidence integration matrix

This matrix is a **required implementation handoff**, not an assertion about the linked artifact's visual structure.

| UI concern | Required behaviour/data | Implementation task and acceptance |
| --- | --- | --- |
| Site selector/readiness | Exact SiteBundle revision, context, CRS/north/scale, source/readiness and restricted/unknown status | B03/B05/B08; V03/V10 |
| Spatial viewer | Existing/proposed/candidate/excluded/unknown legend, scene units and target geometry; no fabricated canopy/simulation numbers | B05; V02/V10 |
| Objective & budget panel | Validated accepted ScenarioInput, upfront cost in GBP pence, declared objective, cases and explicit hard constraints | B01/B05/B06; V01/V04/V10 |
| Sun/time controls | Clearly distinguish view-only time controls from changing an analysis case and therefore requiring a new numerical run | B02/B05/B07; V02/V05/V10 |
| Search/evaluate status | Queued, running, complete, zero benefit, no candidate/target miss, cancelled, failed; latest job selection and provenance | B01/B04/B05/B06; V05/V06/V10 |
| Layout comparison | Actual baseline, proposed and other evaluated layouts with identical case definitions, cost, shade, feasibility and changed assumptions | B04/B06/B07/B05; V04/V07/V10 |
| Agent investigation | Supported concern → fixed-layout test first → observed evidence → optional constrained redesign → recheck or explain/no change | B07/B09/B10; V07/V09/V11 |
| Evidence/report | Data provenance, site/source licence, explicit assumptions, run IDs, live/cached/recorded/fixture modes, survey requirements | B08/B12; V03/V08/V10/V12 |
| Accessibility and failures | Form/keyboard alternatives, colour-independent labels, visible stale/failed/incomplete states | B05/B12; V05/V10 |

## Agentic demonstration to support visually

The intended distinguishing interaction is **proposal → tested concern → evidence → repair or explain / missing information**, not a chat response that simply justifies an optimiser result.

- Begin with an accepted brief and a validated candidate.
- A user questions a specific location, planting strip or crown assumption.
- The agent chooses a registered comparison or analysis operation; do not pre-script the answer or bypass backend permissions.
- Where a fixed-layout concern has meaning, test the original before redesign. Report no-change honestly if the original remains suitable.
- If required and permitted, search for a revised *model-feasible* alternative and recheck applicable hard constraints/cases.
- Show before/after positions, changed inputs, actual result IDs and next human/survey decision; no fabricated temperature, AQI, flood-damage or monetary savings.

**Scope:** One meaningful working investigation is the preferred judge-facing P1 demonstration target, but promotion to an unconditional P0 acceptance gate remains a separate Ben/Arnav/Alex decision. The M2 first slice must not wait for this full flow.

## UI artifact adoption checklist — Alex + Ben + Arnav

1. **Obtain actual source:** access the supplied Claude artifact, export code/screens or a shareable specification; record the artifact revision/date and which page the link targets. If it is private/unreachable, request export from its owner rather than reconstructing unseen screens.
2. **Compare:** capture the actual page structure, components, layout, colors, typography, map/view state, chart labels, controls, interactions and responsiveness in an appendix to this document *after direct inspection*. Distinguish artifact content from new implementation requirements.
3. **Map:** trace each actual component/control to F001–F018, the authoritative API/result fields, and a named B/V item. Mark visual-only mock metrics/fixtures clearly and replace them with actual computed results.
4. **Resolve mismatches:** bring unsupported outputs, fake cooling/energy/AQI/flood claims, impossible APIs, stale/agent states or unimplemented features back to the affected owners; do not change scientific meanings to match a picture.
5. **Implement:** establish the minimum frontend shell, site/map transform, forms, actual job result rendering and stale/error states. Add visual polish only after the real M2 path works.
6. **Verify:** screenshot-to-actual-render comparisons, north/coordinate checks, keyboard/forms, failure/zero/stale states, budget/constraint changes, provenance and live agent observation.

**Current state at publication:** design link registered; artifact contents and fidelity **unverified**; no UI code committed or executed by this documentation change.
