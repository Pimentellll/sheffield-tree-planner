# CANOPY 3D City + Agent UI — implementation sequencing and PR integration plan

**Proposed implementation work, not feature-completion evidence.** 13 November 2026. The source of truth for current code/status is [BUILD](../BUILD.md), not this plan. Scientific meaning, rights and tool authority belong to [SPEC](../SPEC.md), [CONTRACTS](../CONTRACTS.md) and [VALIDATION](../VALIDATION.md).

## Documentation PRs

1. **Geospatial foundation:** `3D_CITY_AND_TREE_PIPELINE.md` — source custody, verified coordinates/datum, tree inventory/CHM classification, visual/physics split and real-site gates (`GEO3D-01..08`). Companion documentation PR [#66](https://github.com/Pimentellll/sheffield-tree-planner/pull/66), to be reviewed by Arnav (scientific interpretation), Alex (3D consumer), Ben (API/registry).
2. **Product experience:** [3D_AGENT_PRODUCT_UX.md](3D_AGENT_PRODUCT_UX.md) — map-first IA, tree inspector, agent tool trace, metrics/evidence states, design artifact brief and accessibility (`UX3D-01..09`). This PR, [#67](https://github.com/Pimentellll/sheffield-tree-planner/pull/67), to be reviewed by Alex (frontend), Arnav (scientific claims), Ben (agent/API).

**Merge order:** #66 before #67 (or together), because UX3D rows cite GEO3D IDs and the PR #66 §3.2 tree tokens; after #66 merges, switch the PR #66 URLs here to relative links. **Related live work:** [#69](https://github.com/Pimentellll/sheffield-tree-planner/issues/69) (recorded-tree inventory, GEO3D-01), [#73](https://github.com/Pimentellll/sheffield-tree-planner/issues/73) (agent-run API), [#74](https://github.com/Pimentellll/sheffield-tree-planner/issues/74) (agent-run UI consumer), draft PRs [#70](https://github.com/Pimentellll/sheffield-tree-planner/pull/70) and [#71](https://github.com/Pimentellll/sheffield-tree-planner/pull/71).

Both PRs are documentation only. They neither enable real Sheffield computation nor mark hardware or source rights accepted. Reviewers should first verify the current implementation SHA, existing PRs, and any contracts changed since 13 November.

## Implementation dependency graph

`SOURCE DATA + RIGHTS → CRS/HEIGHT/CONTEXT → VISUAL TILES + TREE FEATURES → CITY EXPLORER / FEATURE INSPECTOR`

`SOURCE DATA + RIGHTS + GEODESY + SEMANTICS + BASELINE OWNERSHIP → VALIDATED REAL SiteBundle → PHYSICS ↔ VIEWER PARITY → REAL-SITE METRICS`

`CURRENT SCENARIO/RESULT APIs → JOB STATES + HUMAN REVIEW → AGENT TOOL TRACE + EVIDENCE/COMPARE/REPORT UI`

City visualization may arrive **before** real-site numerical acceptance, as long as it is explicitly visual-only. It must not bypass the scientific adapters. The existing synthetic P0 demo remains functional during development.

## Suggested implementation sequencing

I1–I8 (like GEO3D-xx and UX3D-xx) are suggested sequencing and supplementary acceptance checklists, **not** task IDs, assignments or a status board (AGENTS.md rule 10). [BUILD](../BUILD.md) is the only status home. Live issue assignment governs; this table assigns no writer. Status: see BUILD / the mapped issue.

| Slice | Contents | Acceptance rows → live issues (assignment governs) | Reviewers / evidence |
| --- | --- | --- | --- |
| **I1: dataset custody** | Council tree ArcGIS FeatureServer schema receipt in native EPSG:27700 (not reprojected GeoJSON); EA tile acquisition/hashes/rights; metadata manifest | GEO3D-01 → [#69](https://github.com/Pimentellll/sheffield-tree-planner/issues/69) (Street Trees recorded inventory; Community Forestry optional, unassigned); GEO3D-02 → [#10](https://github.com/Pimentellll/sheffield-tree-planner/issues/10), Arnav scientific review via [#30](https://github.com/Pimentellll/sheffield-tree-planner/issues/30) | Ben asset/rights review; file receipts; no real-site claim |
| **I2: coordinate + raster importer** | Geodesy accuracy/true north/datum, GeoTIFF read, no-data, alignment, context | GEO3D-02/03 → #10 (Ben, single writer for import/terrain/transform/mesh paths), Arnav scientific review via #30; reconcile with the display-only crop script on Alex's branch `feat/alex/terrain-context-view` (`b1bb0e5`) | Arnav scientific review (#30); Alex viewer parity; known-point tests |
| **I3: single-site viewer + trees** | Weston Park visual pilot: terrain/building context, source tree point layer, stable selecting inspector, visual-only banner; MapLibre is an alternative for the viewer owner to decide | GEO3D-04 (after GEO3D-03 alignment), UX3D-02/03 → Alex's existing unmerged branch `feat/alex/terrain-context-view` (`b1bb0e5`) / [#16](https://github.com/Pimentellll/sheffield-tree-planner/issues/16). Citywide browsing/LOD is F024 (P2), F025/F033 (P3): explicit assignment and a method/data/rights/validation plan first | Arnav source/position review; performance/accessibility receipts |
| **I4: canopy detection/identity** | Candidate crown segmentation, building exclusion, council/crown matching, `evidence_class`/`match_status` evidence | GEO3D-05 → no issue; needs explicit assignment before work | Curated annotation, precision/recall and ambiguity tests |
| **I5: numerical real-site adapter** | Reviewed nonflat terrain and existing occluders, shadow context, candidate/site bundle and source fingerprint | GEO3D-07 → #10 + #30 (B08) | V03/B08 independent evidence, solver/viewer parity; fail-closed retained |
| **I6: Studio result-state UX** | Actual job states, revision/currentness, unsupported/empty modes, agent trace and human approval | UX3D-05 → [#17](https://github.com/Pimentellll/sheffield-tree-planner/issues/17)/[#25](https://github.com/Pimentellll/sheffield-tree-planner/issues/25); UX3D-06 → [#73](https://github.com/Pimentellll/sheffield-tree-planner/issues/73) (agent-run API, Ben) + [#74](https://github.com/Pimentellll/sheffield-tree-planner/issues/74) (consumer, Arnav) + [#29](https://github.com/Pimentellll/sheffield-tree-planner/issues/29)/[#56](https://github.com/Pimentellll/sheffield-tree-planner/issues/56) (panels, Alex). Agent-evidence UI: Arnav (#74); surrounding UI shell: Alex (#56), as assigned on those issues | Same-tools manual+agent traces; stale/late/failure browser tests |
| **I7: compare/report polish** | Physical units, controlled changes, run provenance/rights/survey warnings, responsive captures | UX3D-07 → #17/#29/#74; UX3D-08 → #29/[#32](https://github.com/Pimentellll/sheffield-tree-planner/issues/32) | Ben/Arnav semantic check; full keyboard and evidence tests |
| **I8: launch/demo QA** | Current main SHA, UI screenshots, claims checked against the event-day ledger, device/browser QA, release/rollback | Event-day release process; see BUILD | Full acceptance only after independent reviews |

Much of I6/I7 already exists on main: `frontend/src/planning/evaluation.ts` (`classifyResult`, `CURRENTNESS_LABEL`, `EXECUTION_MODE_LABEL`, `describeJob`), the compare panels in `frontend/src/panels/CompareScreen.tsx` and `Requirements.tsx`, and the client-built review pack in `ReportScreen.tsx`. These rows add only acceptance deltas beyond the mapped issues and extend those components rather than rebuilding them.

Before starting, check [#26](https://github.com/Pimentellll/sheffield-tree-planner/issues/26), #29, #32, #56, #73, #74 and draft PRs #70/#71 for overlap. Each implementation PR cites its STP/M/B/F/V IDs and issue (required); GEO3D/UX3D rows are optional supplementary acceptance references. Attach reproducible tests and specify what is still unknown.

## Event-day priority and non-interference

The 13 November [event board](../EVENT_DAY_EXECUTION_2026-11-13.md) puts a working integrated deterministic demo, genuine model tool trace, Spark proof and submission evidence ahead of full city ingestion. The [issue index](../EVENT_DAY_ISSUE_INDEX_2026-11-13.md), the source of operational task ownership, marks the one-site Sheffield mesh (X-E06) **P2 deferred until rights and CRS/solver parity pass**, superseding the board's earlier P1. Citywide browsing/LOD maps to [FEATURE_PRIORITIES](../FEATURE_PRIORITIES.md) F024 (P2) and F025/F033 (P3) and needs explicit assignment plus a method/data/rights/validation plan before implementation (AGENTS.md). Do not disrupt Ben's release/device work or Alex's submission UI.

**Proposed future claim conditions (not permissions):** statements in the video, form, README or Q&A must match an approved row in `docs/event-day/science/EVIDENCE_AND_CLAIMS_LEDGER.md` on main ([GitHub](https://github.com/Pimentellll/sheffield-tree-planner/blob/main/docs/event-day/science/EVIDENCE_AND_CLAIMS_LEDGER.md)). Until a row is approved, ledger row S-08 governs: any real-geography view is labelled **visual context only**, with results from synthetic geometry (`SCIENTIFIC_ACCEPTANCE.md` S-02). The conditions below are prerequisites for proposing a ledger row, not permission to make the claim.
- **Candidate now, when backed by receipts and a ledger row:** synthetic CPU geometric shade evaluation and constrained search, immutable result provenance, a labelled engineering 3D viewer.
- **Only after data/rights evidence and a GEO3D-03 alignment check:** real Sheffield 3D **visual context** and source-record tree locations.
- **Only after V03/B08 and numerical parity:** real Sheffield modelled shade benefit.
- **Only after separate validated new models:** °C cooling, AQI, runoff/flood prevention, carbon/biodiversity/monetised return.
- **Only after real model + tool run on device:** adaptive NVIDIA/Nemotron/Spark claims. Browser WebGL GPU work is not CUDA physics.

## Minimum cross-owner review questions

- **Arnav:** Do actual grid+datum and sun/north conventions agree? Are DSM/building/tree semantics and leaf-off limitations honest? Is baseline canopy occlusion unambiguous? Are physical metric and target/time/area basis exact?
- **Alex:** Is City Explorer useful without an accepted site? Can users select recorded/inferred/proposed trees reliably? Does map dominate? Are agent/evidence panels legible at desktop/tablet and accessible by keyboard? Does visual state ever imply a backend calculation not performed?
- **Ben:** Are all displayed source assets rights checked? Are new visual contracts additive/versioned and generated as needed? Do scenario, job, model tool and result revisions remain immutable, bounded, auditable and race-safe? Can the user continue manually when agent/model fails?

## Evidence required in implementation PR descriptions

STP/M/B/F/V IDs and issue, repository commit, tool/runtime/device versions, source URLs/capture dates/file SHA-256/licence permissions, dataset sample schema, exact coordinates/transform operation, test command/output, GUI screenshot or browser trace, source/result/run/scenario IDs, supported claims, limitations, affected issues, owners' acceptance and rollback plan. Never call 'docs merged' equivalent to 'feature implemented'.

## Review and merge discipline

Follow the repository's documented feature-branch/PR review process; do not push directly to main or silently change another owner's work. PRs for teammate review, including these docs PRs, start as drafts with no reviewers requested until the publication/review gate is approved (AGENTS.md); Ben coordinates merge after owner review. Docs-only PRs can target main for visibility, but **do not merge without appropriate owner review**, especially on this event day. Confirm CI and branch head are current before merging. Ben remains the coordinator for shared BUILD status and application integration; these new files deliberately do not overwrite it.
