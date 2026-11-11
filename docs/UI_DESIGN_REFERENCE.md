# CANOPY Sheffield — UI design reference, screen inventory and implementation contract

**Status (11 November 2026):** **Source-inspected design prototype, not implemented product UI**. Arnav supplied two screenshots of the contact sheet and six downloadable HTML export archives. Their HTML, declared component logic, style attributes, static data and bundled SVG asset manifests were inspected. The original [Claude artifact, supplied page](https://claude.ai/artifact/2ZbqmnjEJ1vn2mDvjeK2bQ#page-dcb81aee8d83) remains the original design link; the actual original Claude page was not directly accessible. The **exported files now provide sufficient concrete evidence for design and implementation planning**.

**Authority:** [SPEC](SPEC.md) owns product requirements and agent policy; [FEATURE_PRIORITIES](FEATURE_PRIORITIES.md) owns F001–F035/P0–P3 and M0–M7; [CONTRACTS](CONTRACTS.md) owns SiteBundle, ScenarioInput, jobs, metrics and tool meanings; [NUMERICS](NUMERICS.md) owns physics and optimisation; [VALIDATION](VALIDATION.md) owns proof; [BUILD](BUILD.md) owns decisions, ownership and task status. This reference is **the visual/product-interaction handoff**, not a second wire specification or an approval to claim illustrative data as measured results.

## 1. Inspected sources and custody

| User-supplied export | Page / contents | Archive SHA-256 |
| --- | --- | --- |
| 01 · Sheffield City Overview-html.zip | \`Overview.dc.html\`, one illustrated SVG, custom support and React runtime | \`c1ff47d56608edc69e2fc849191275e7ed506236e3c722a95dda131aab9a99c0\` |
| 02 · Planting Optimisation Studio (flagship)-html.zip | \`Main.dc.html\`, one illustrated SVG, custom runtime | \`75ae049d1e3560b46209d012b050d4754d5406d1737e052c656f8602d3ae5503\` |
| 03 · Scenario Comparison-html.zip | \`Compare.dc.html\`, two illustrated SVGs, custom runtime | \`d7f320301bd8977d7a94ad99dde15db041a49e86e48b8e741226b1c57d5c5821\` |
| 04 · Impact & Investment Report-html.zip | \`Report.dc.html\`, one illustrated SVG, custom runtime | \`0d6c9e885faa908441510b7789955c8ce8d654ad2a7167990a624ae150c44347\` |
| Design system-html.zip | \`DesignSystem.dc.html\`, token/component showcase | \`d41fee65c5d81b0acdc32662e0a563c97695223da071185ada1161c31897a3fc\` |
| Contact sheet-html.zip | \`ContactSheet.dc.html\` and copies of all four page files and illustrative map SVGs | \`6db93fac40072f60d0d9c866470d593ff8e7f09c13ec248b348c127f121abb8c\` |

Source artboards specify a **1600 × 1000 px preview**, styled as absolute-positioned custom \`x-dc\` HTML with inline CSS, a local \`support.js\` helper, bundled React scripts, and generated SVG illustration basemaps. **This is not a reusable production React/Three.js application**; the exported SVGs are drawings, not GIS geometry, measured environmental data or proof of a running solver. Some visual event handlers exist, but the planning dataset, numerical summaries, timing and agent transcript are sample content.

**Asset custody:** The user supplied the original ZIPs in the design handoff. Their binary archives and large generated SVGs are **not included in this documentation-only PR**. Alex needs the original six ZIPs (or an agreed legally usable export) for full visual parity; the archive hashes above identify the reviewed revision. Inspect/review third-party asset terms before adding graphics, data, bundled runtime or fonts to the application. Do not blindly vendor React/support scripts from this export. Use the existing application's pinned dependency stack.

## 2. Global design system — exact tokens from the supplied export

**Design language:** dark forest navigation and map canvas; contrasting ivory analytical surfaces; spacious map-first composition with slim framing panels. Colour has semantic meaning, *not just decoration*. The artboards use the map as the focal area; a production layout must adapt to smaller screens instead of scaling the entire 1600px page down.

| Token | HEX | Semantic role |
| --- | --- | --- |
| Forest | \`#101E1B\` | App ground and navigation |
| Pine | \`#243D35\` | Panels and controls |
| Lime | \`#B7E879\` | Proposed action / one primary CTA per view |
| Ivory | \`#F4F3ED\` | Analytic surfaces and text |
| Water | \`#62AFC2\` | Rivers, stormwater and Plan A comparison |
| Heat | \`#E8A476\` | Heat opportunity and Plan B comparison |
| Constraint | \`#D67C64\` | Exclusions, required survey and stale-state warnings |
| Canopy | \`#527A55\` | Existing canopy/tree context |
| Heat on ivory | \`#D98A55\` | Darker chart/data stroke |
| Equity on ivory | \`#7FB33F\` | Darker chart/data stroke |
| Water on ivory | \`#3F8EA3\` | Darker chart/data stroke |
| Air on ivory | \`#8E88B8\` | Darker chart/data stroke |

**Typography:** Manrope 700–800 for display headings and primary titles, Inter 400–600 for interfaces and body, JetBrains Mono for every currency value, numerical result, site ID, unit and revision. Exported sizes: 30px display, 24px KPI, 17px panel title, 13px body, 11.5px meta, 10.5px caption. Desktop-artboard sizes are design references, **not acceptance of inaccessible 10.5px labels on small screens**. Aim for legible type, WCAG contrast, visible focus/keyboard controls and text alternatives to colour-only cues. Original SVG/inline icons target a 1.6px stroke; use an internally consistent icon set.

**Reusable visual components:** app/navigation rail; page title and source-status watermark; site selector; layer toggles; target and candidate map markers; ranked proposal row; selected-site detail card; budget slider plus numeric field; objective/constraint controls; stale-result banner; model job status/trace; KPI tile with evidence level; paired-plan comparison bar; canopy-growth control; cost estimate/range; source and licensing table; proposal/export surface. Labels **MODELLED / INDICATIVE / NOT QUANTIFIED / EST.** convey evidence classes; they do not themselves prove any run.

**Symbology:** existing tree green, proposed action lime, Plan A blue, Plan B amber, excluded/constraint coral; distinguish *opportunity* (heuristic map field) from *feasibility* (candidate/clearance/survey status), and distinguish *known model-feasible* from professional permission to plant. Use shapes, outlines and text as well as colour.

## 3. Screen 01 — Sheffield City Overview (\`Overview.dc.html\`)

**Intent:** establish Sheffield context, show citywide opportunity/need, then launch bounded site planning. Screenshot artboard is dark, with illustrated tilted terrain, roads, existing canopy dots and five named waterways: Don, Sheaf, Loxley, Rivelin and Porter Brook.

**Observed elements and illustrative content:**
- Headline: **“Plan greener streets. Prove the impact.”**
- City-level demo indicators: **18.4%** canopy cover; **11 / 28** low-canopy districts; **14.2 km²** heuristic heat-priority area; **24,600** screened positions. **None is verified citywide Sheffield data from this export.**
- Six layer toggles: Existing canopy; Heat priority; Rivers & flood zones; Built fabric; Air-quality indicators; Canopy equity. The custom component changes its local on/off state, while the illustrated basemap is not a verified GIS layer switch.
- Priority district ranking with tab selections for **Heat**, **Canopy gap** and **Flood**; a small hardcoded district table is sorted locally in the export. The “heat” field is a heuristic, not temperature; “flood” is a context/exposure indicator, not damage.
- Hero/clickthrough card: **Kelham Island & Neepsend**, **0.86 km²**, draft Plan B **46 trees / £74.5k estimated**; “Open Optimisation Studio.”
- \`2D\`, \`3D\`, “Reset view” and location search appear but do not establish a functioning GIS camera or search integration.

**Implementation contract:** citywide layers are a **P2 F024 overview** and must not block B02/B04/B05. A static, honestly labelled city context is acceptable as a visual entry screen while the audited site is built. Data-backed rankings require verified source joins, CRS/rights checks, provenance and precise time/area definitions. Use a site-selection action to enter the active SiteBundle, not a hardcoded route into a purported accepted Sheffield study area.

**Critical site discrepancy:** the design's Kelham Island & Neepsend corridor is a **UI scenario placeholder**, whereas Ben's dossier identifies **Weston Park** and **Manor Fields Park** as candidate geometry pilots and Peace Gardens as conditional. Neither the design's Kelham area nor the dossier's sites have been accepted as a modelled, rights-cleared planting area. B03 owners must explicitly choose a first site/fallback; Alex should use whichever is accepted and preserve the UI layout.

## 4. Screen 02 — Planting Optimisation Studio (\`Main.dc.html\`) — FLAGSHIP

**Observed composition:** dark header/left “Plan parameters” controls; central large illustrated Kelham map with layers/markers and selected-site overlay; right-side current-plan KPI and ranked-site evidence pane. The design makes the interactive map the centre of the workflow.

### 4.1 Initial example state — illustrative, NOT a completed numerical run

| Item | Exported value / label |
| --- | --- |
| Scenario | Plan B · v3, “Urban cooling priority” |
| Study area | 0.86 km² Kelham Island & Neepsend |
| Candidate count | 1,260 screened (sample) |
| Capital budget | £75,000, adjustable **£10,000–£150,000** in **£2,500** steps |
| Plan B layout | 46 trees; £74,530 capital estimated; £470 remaining |
| Objective sliders | Heat & shade 45%; canopy equity 25%; flood & stormwater 15%; air quality 15% |
| Default constraints | Façade clearance 3m ON; exclusions ON; 11m new-tree spacing ON; winter sun ON; survey-site exclusion OFF; £7,000/year maintenance cap ON |
| Reported result | Additional target shade **9,320 m²·h**, summer design day, year-10 crown assumption — **hardcoded illustrative result**, not executed physics |
| Establishment | £19,980 estimated over 3 years — scenario number |
| Example selected candidate | \`KN-0377\`, Corporation St west footway; suitability 72.6/100; +228 m²·h; £1,950 estimated + £160/year establishment; “utility survey required” |
| Sample run text | Rev \`7f3a\`; “2.4 s”; greedy/local swaps; deterministic — **placeholder run/latency**, not measured |
| Site priorities | Demo “surface heat” 0.72, canopy deficit 0.97, traffic 0.93, stormwater 0.13 — heuristic proxies |

### 4.2 Actual HTML behaviour audited

- Moving the budget slider, a weight slider or a constraint toggle sets local \`stale=true\`; previously shown plan values dim, and a warning text is displayed. **Good interaction pattern to retain.**
- The objective sliders each vary independently from 0–100 by 5. The sum is displayed, but **there is no enforcement that the sum equals 100** before “regeneration.”
- The \`Generate planting plan\` action simply calls local state to set \`stale=false\`. **It does not run a search, call an API, modify the plan, create a new revision, or replace a numerical result**. This is the highest-priority fidelity gap.
- Clicking ranked rows or markers changes the locally selected rank; the detailed card's data is visibly authored for \`KN-0377\` and is not a general-purpose per-candidate API view.
- “Cooling”, “Flood”, “Balanced” and “Custom” presets; “Exclude”; “Why here?”; 2D/3D/map camera controls; overlay buttons and chatbot input are visually present, but no actual domain-simulation/agent action is established by their exported handlers.
- The sample copy says 41 sites replaced and 16 retained relative to Plan A; those are prewritten comparisons, not computed replanning evidence.

### 4.3 Required production behaviour

1. User edits **draft inputs**, then the backend validates and the human accepts consequential scenario changes under CONTRACTS. Editing must immediately invalidate *current* UI metric selection; asynchronous old jobs may finish only into history.
2. For a supported P0 objective, invoke actual \`evaluate_layout\` or \`search_layouts\`, backed by numerical methods in NUMERICS. The accepted run's IDs, inputs, units, source/provenance, status and timing come from the backend. A “Generate” click cannot merely remove the stale banner.
3. Hard budget/exclusion/spacing/clearance/winter rules must be enforced **server-side**. Prototype switches must not silently waive required accepted constraints; make unsupported switches locked/disabled or require an explicit permitted human scenario revision.
4. The four illustrated weighted outcome controls are **not already four validated environmental simulators**. P0 supports direct useful shade and declared costs; full multidomain weighted/Pareto optimisation is conditional P2 F021 and needs method/data/metric contracts. If the build only supports shade, remove, disable or clearly label unsupported composite/flood/AQI “optimise” controls rather than claim to compute them. “Balanced” cannot be declared functional just because it is drawn.
5. Site details must be generated from selected candidate/result references, not a single hardcoded card. Opportunity proxy scores are *indicative*, independent from numerical shade and independently validated model-feasibility.
6. “Why here?” should use a registered local model investigation, such as \`compare_locations\`/controlled \`compare_scenarios\` after those operations exist. Display model-selected operation, actual arguments, observation/result references and decision status; no canned answer/latency.
7. The map must share geometry scale, ENU/CRS, north, candidate IDs and selected layout with the numerical service; SVG illustration may remain only as **labelled visual reference**, not as authoritative survey geometry.

## 5. Screen 03 — Scenario Comparison (\`Compare.dc.html\`)

**Intent:** compare an equal-budget **Plan A flood-led** and **Plan B cooling-led** layout over the *same site, candidate set and constraints*. Two illustrated basemaps occupy symmetric comparison panels. Plan A is blue, B amber; the UI distinguishes A-only, B-only and shared sites.

**Illustrative example:** both have a £75,000 ceiling and 1,260 candidates. A: flood 50 / heat 15 / air 15 / equity 20; **57 trees, £74,710**. B: heat 45 / equity 25 / flood 15 / air 15; **46 trees, £74,530**. The artwork labels **41 A-only**, **30 B-only**, and **16 shared** sites; counts are internally consistent. These are not measured/planner-executed results.

**Visual structure:** Side by side / Swipe / Difference only buttons; symmetric maps and legends; butterfly metric bars from a common centreline; growth years **Planting (0), 5, 10, 20, 30**; prose trade-off explanation; “Planning agent” investigation card; “Adopt Plan B” and “Build hybrid from shared sites.”

**Actual HTML behaviour:** the year-selector radio controls change local state and recalculate some displayed rows using **hardcoded illustrative crown-area multipliers and shade factors** (\`year 0/5/10/20/30\`, arbitrary lookup tables), not species-specific growth or a physics rerun. The alternate view mode buttons, “Build hybrid” and export do not demonstrate working actions. “Adopt Plan B” is currently only a link to the report, not an approved scenario change.

**Agent card as supplied:** says Nemotron re-ran both layouts under ±20% crown size, B remained ahead in **18/20 runs** and A tree count in all, with a \`sensitivity_sweep\` tool and **6.1 s**. This is **static sample copy**, not a recorded agent execution. \`sensitivity_sweep\` is **not a registered domain operation in CONTRACTS**; implement comparable checks using validated \`compare_scenarios\`/existing tools, or request coordinated approval for a new operation before claiming it.

**Production requirements:** compare only compatible evaluated scenario/run IDs; show explicit differences in objective/constraints/cases; preserve actual spend, shared/unique placements and independent feasibility status. Growth-stage choices require real separate profile states/cases (B07/F011) and appropriate model limitations. Swipe/difference mode must actually alter map presentation or be disabled. Adoption/hybrid creation must create a *draft* and require human acceptance; it cannot silently mutate the active scenario.

**Metric caveat:** “stormwater opportunity” is a heuristic, not modelled avoided runoff, and any relative plan ranking on flood/air must be described as a *proxy-based illustrative decision*, not scientific flood or pollutant benefit.

## 6. Screen 04 — Impact & Investment Report (\`Report.dc.html\`)

**Intent:** light, print-ready council/sponsor decision-support report. Ivory background, contrasting forest titles, embedded illustrated site map, neighbourhood distribution bars, financial summary, evidence-classified benefits, cost-over-time chart, assumptions and data-provenance table.

**Example report title:** “Kelham Island & Neepsend planting strategy — Plan B, urban cooling priority.” Banner: **“Not yet for decision · survey pending”**. Prepared 11 Nov 2026, sample revision \`7f3a\`.

**Illustrative economics/planting:** 46 trees: **32 street pits + 10 verges + 3 riverside + 1 yard**; estimated £74,530 installation, £19,980 establishment years 1–3, 25-year cost **£140k–£176k** excluding replacement/inflation. Unit price estimates are not contractor quotes. The category arithmetic is internally consistent (32 × £1,950 + 10 × £720 + 3 × £860 + 1 × £2,350 = £74,530), but those prices and maintenance schedules are not verified local procurement data.

**Evidence table as exported:**
- **MODELLED:** “Direct shade — 9,320 m²·h/day”, year-10 crowns, demo summer design day. **Design placeholder until a real physics result exists.**
- **INDICATIVE:** heat-exposure index, canopy equity, stormwater opportunity. Equity currently means below-median canopy in illustrative cells, not measured distributional impact; deprivation data are not joined.
- **NOT QUANTIFIED:** air quality and carbon. The UI explicitly declines to assign £ value to heat, flood, air or carbon, which is a good boundary.
- Cost chart/benefit-per-£ summaries are scenario arithmetic and should be populated only from versioned costs and validated model outcomes.

**Source table in export:** EA LiDAR DTM/DSM and EA Flood Map for Planning marked “Licence check”; existing council trees and cost schedule marked “Demo stand-in.” Do not interpret these example labels as actual ingestion, acceptance, permission or proof of accuracy.

**Actual HTML behaviour:** “Share link” and “Export report (PDF)” are visible buttons without verified share/export logic. “All sources” currently links to \`DesignSystem.dc.html\`, which is a design-token specimen, **not a real provenance page**.

**Production requirements:** render from a validated \`prepare_proposal\` or suitable selected immutable results, with rights/asset checks, source versions, revision/run IDs, explicit cost scope/ranges, and unquantified/unsupported fields retained as such. Implement share/export only with working code and permission; otherwise disable/hide. A proposal is not council approval to plant.

## 7. Contact sheet and cross-screen information architecture

The inspected Contact Sheet defines **exactly four core application screens** in this order:
1. **City Overview:** canopy versus heat; find a study location.
2. **Planting Optimisation Studio:** flagship weights, constraints, ranked candidates and evidence.
3. **Scenario Comparison:** Plan A versus Plan B under comparable inputs.
4. **Impact & Investment Report:** costs, evidence levels and provenance.

A fifth exported **Design System** artboard is a reference, not a fifth decision workflow. The common UI navigation includes icons linking Overview, Studio, Comparison, Report and “data sources”; in the prototype the last points to the Design System. In the product it must lead to an actual sources/provenance surface.

**Proposed route/interface states**, not existing production routes:
- \`/overview\`: site selection and contextual indicators.
- \`/studio/:siteId\`: accepted scenario, drafts, layers, selected candidate, evaluation/search, agent investigation.
- \`/compare/:comparisonId\`: compatible A/B evaluated alternatives and case controls.
- \`/report/:proposalId\`: validated and rights-cleared decision summary.
- Sources/provenance drawer/page: data versions, rights, unresolved site checks.

Link screens through **immutable scenario/layout/result references**, not by copying demo metrics or stage labels across components.

## 8. Contract-to-UI implementation mapping for Alex (no new schema)

| Surface / interaction | Existing operation or authoritative data | Feature / tasks / validation |
| --- | --- | --- |
| Site selector, map and source watermark | \`SiteBundle\`, scene revision, source rights, ENU transform; \`inspect_site\` | F001/F002; B03/B05/B08; V01/V03/V10 |
| Editable controls and acceptance | \`ScenarioInput\`; accepted vs hypothetical revisions; immutable job identity | F005/F009; B01/B05; V01/V05/V10 |
| Real shade and candidate markers | \`evaluate_layout\`, metric instances, selected layout, exact receiving surfaces/cases | F003/F004/F010; B02/B04/B05; V02/V04/V05 |
| Greedy/reference proposal | \`search_layouts\` + independently validated model constraints | F006/F007; B06/B05; V04/V06 |
| Budget, costs, uncertainty | Profile-estimate/version, supported scenario, per-metric provenance, separate optional cases | F007/F011/F012/F014/F016; B06/B07; V04/V07 |
| Controlled comparison | \`compare_locations\`, \`compare_scenarios(mode=fixed_layout|redesign)\` when implemented | F013/F015; B07/B10/B05; V07/V09/V10 |
| Local agent investigator | Registered dispatcher + model-selected action, observation, run/result identity, bounded stopping | F008/F013; B09/B10; V08/V09/V11 |
| Proposal and report | \`prepare_proposal\`, evidence, rights-clear allowlisted export | F010/F018; B08/B12; V03/V10/V12 |
| Stale result and failure UX | Backend job/selection/revision semantics, not a frontend-only flag | F009/F010; B01/B05; V05/V10 |

**Canonical reactive state flow:**

\`view current accepted revision → edit an unsaved draft → invalidate current selection/dim old result → validate/human accept consequential changes → queue a new job → show queued/running/cancelled/failed correctly → accept ONLY the selected current-revision completed result → update map/metrics/provenance → optionally compare/investigate.\`

Do not allow a late callback from an old revision (or an earlier job in the same revision/slot) to replace the newer selection. Do not relabel a development fixture or exact-input recorded run as live computation. A cached result has its original run plus current delivery identity.

## 9. Reconcile the source artboards against accepted product scope

| Export design element | Evidence status / action |
| --- | --- |
| Four weighted goals / Cooling, Flood, Balanced, Custom | **Illustrated UI target**, NOT proof that P0 supports weighted multi-environment search. Keep current supported shade objective; optional proxy scores must be honestly labelled, and multidomain Pareto/weighted optimisation requires F021 approval and source-backed methods. |
| 0.86 km² Kelham site and citywide stats | **Unverified illustrative site and overview**. Accept a real primary/fallback through B03/B08, otherwise show synthetic/demo labels. |
| 46 trees, £74,530, 9,320 m²·h, 2.4s | **Hardcoded display values**. Replace with actual results / timing from B04/B06/B12; preserve the visual formatting pattern. |
| “MODELLED” badge on demo values | Illustrative copy only. In production, show modelled badge only for a recorded deterministic run plus provenance; watermark any design fixture separately. |
| Exported SVG basemaps and 2D/3D modes | **Illustrations**; no validated geometries, solar/ray run, camera transforms or surveying evidence. Integrate a lawful versioned site scene separately. |
| Prototype “Generate” and stale animation | Local flag toggling only; wire to accepted revision and real numerical job before calling it operational. |
| Prototype “Why here?” and agent sensitivity trace | Static UI; connect to local registered tools and observed result IDs; \`sensitivity_sweep\` not currently registered. |
| Winter sunlight “unaffected”, façade 3.4m and utility check | Static selected-card statements. Require actual geometry/constraint evaluation or label unknown. |
| Growth year 0/5/10/20/30 | Hardcoded multipliers; real case states depend on supported profiles and B07 validation. Do not present generic growth as a species or survival forecast. |
| Share / PDF export / report source link | Buttons shown; operational behaviours not established. Implement or disable, and link to actual provenance rather than Design System. |
| Fixed 1600×1000 artboard | Visual reference; do not inherit fixed desktop-only layouts as the production responsive design. |
| Cost / environmental benefit claims | Explicitly distinguish scenario estimates, heuristic opportunity, model output and unquantified services. Flooding/air-quality/carbon/household savings require separate model evidence. |

**Key competitor-aware product interaction:** Ben's accepted [research-to-design direction](SPEC.md) is **proposal → concern → fixed-layout test → observed evidence → optional constraint-preserving repair → recheck or explain/no-change**. Add an agent evidence panel to the existing Studio/Comparison visual language when implementing B10. The original artboard's prewritten “20 runs / 6.1s” claim is **not** such evidence.

## 10. Visual fidelity and implementation acceptance — Alex's work package

**Before B05 code:** inspect the six original exports and contact-sheet screenshots; confirm design source revision, actual assets/licensing, intended desktop/map layout and selected primary site. Coordinate with Ben/Arnav on contracts, geometry frame, tool statuses and owner-approved available objectives. Record the design handoff under B05 without creating a competing task tracker.

**M2 first slice (P0 development gate):**
- Preserve forest/pine/ivory/lime structure, typography and visible map, target and tree markers, but start with a working 2D scene/form if 3D is not integration-ready.
- The “Generate” control sends a real typed request; display actual result IDs, costs/units, zero-gain/errors and provenance; make draft edits immediately stale.
- Verify case/coordinate alignment between map and evaluator, including north direction and target geometry. Use accepted scene or clearly marked synthetic fixture.

**M3–M5:**
- Wire actual candidate list, constraints and optimiser output to ranked rows and selected-site details; no fixed KN-0377 card or 46-tree count.
- Prove early Nemotron local model tool round-trip when permitted, then bounded interaction and evidence trace.
- Integrate at least one genuinely computed A/B or fixed-layout comparison before enabling “Adopt” or “Why here?” as functional controls.

**M6–M7:**
- Implement only supported growth/sensitivity, repair-or-explain and report surfaces; preserve optional/pending states for anything unvalidated.
- Test map display modes, keyboard and small-screen access, altered budget/constraints, old-job races, unsupported metrics, incomplete site, survey unknown and actual agent/error evidence.
- Produce screenshot comparisons to the original artboards while proving that production metrics are current-run results rather than design placeholders.

**Acceptance reviewer split:** Alex owns interaction and visual implementation, Ben owns API/jobs/dispatcher semantics, Arnav owns geometry/numerical meaning/claim checks. Shared contract changes require coordinated approval. Refer to B05/B08/B10/B12 and V05/V07/V09/V10/V12 in BUILD/VALIDATION for final completion; documentation and source inspection alone do not pass them.

## 11. Next handoff and unresolved questions

The six supplied exports now give **enough screen-specific detail for Alex to begin UI implementation decomposition**. They do **not** answer these product/engineering decisions:
- Which georeferenced Sheffield site will be accepted for the initial numerical demonstration, versus the design's Kelham placeholder?
- What exactly will the P0 optimisation objective expose when four illustrated benefit sliders are not physically implemented?
- Which one counterfactual/stress-test question should the team commit to demonstrating with actual result traces?
- Which source/code assets from the exports can be lawfully reused; will the team share the reviewed ZIPs directly with Alex?
- Which UI control labels need to be disabled, renamed or moved to an indicative/roadmap state until their underlying operation is implemented?
- Have Ben and Alex accepted the same shared contract revision and roles?

These are approval/integration gates, not reasons to commission another broad research phase. **Do not treat this UI design as implementation evidence, and do not overwrite a functioning app with the exported illustration code.**

## 12. Integrated system design references

The [integrated system architecture](ARCHITECTURE_DESIGN.md) explains authoritative scene/scenario/result/agent relationships underlying these screens, and the [adversarial architecture audit](ARCHITECTURE_AUDIT.md) identifies the highest-risk design mismatches: unsupported four-axis optimisation, Kelham scene provenance, static evidence and fabricated apparent agent outcomes. The actual supplied exports remain the visual reference; this document remains the screen-accurate interaction and component handoff. Alex's implementation must not redefine CONTRACTS or NUMERICS to make the illustrated values appear real.
