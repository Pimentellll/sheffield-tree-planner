# CANOPY 3D City + Agent UI — implementation tracker and PR integration plan

**Proposed implementation work, not feature-completion evidence.** 13 November 2026. The source of truth for current code/status is [BUILD](../BUILD.md), not this plan. Scientific meaning, rights and tool authority belong to [SPEC](../SPEC.md), [CONTRACTS](../CONTRACTS.md) and [VALIDATION](../VALIDATION.md).

## Documentation PRs

1. **Geospatial foundation:** `3D_CITY_AND_TREE_PIPELINE.md` — source custody, verified coordinates/datum, tree inventory/CHM classification, visual/physics split and real-site gates (`GEO3D-01..08`). Separate geospatial documentation PR, to be reviewed by Arnav (scientific interpretation), Alex (3D consumer), Ben (API/registry).
2. **Product experience:** [3D_AGENT_PRODUCT_UX.md](3D_AGENT_PRODUCT_UX.md) — map-first IA, tree inspector, agent tool trace, metrics/evidence states, design artifact brief and accessibility (`UX3D-01..09`). To be reviewed by Alex (frontend owner), Arnav (scientific claims), Ben (agent/API).

Both PRs are documentation only. They neither enable real Sheffield computation nor mark hardware or source rights accepted. Reviewers should first verify the current implementation SHA, existing PRs, and any contracts changed since 13 November.

## Implementation dependency graph

`SOURCE DATA + RIGHTS → CRS/HEIGHT/CONTEXT → VISUAL TILES + TREE FEATURES → CITY EXPLORER / FEATURE INSPECTOR`

`SOURCE DATA + RIGHTS + GEODESY + SEMANTICS + BASELINE OWNERSHIP → VALIDATED REAL SiteBundle → PHYSICS ↔ VIEWER PARITY → REAL-SITE METRICS`

`CURRENT SCENARIO/RESULT APIs → JOB STATES + HUMAN REVIEW → AGENT TOOL TRACE + EVIDENCE/COMPARE/REPORT UI`

City visualization may arrive **before** real-site numerical acceptance, as long as it is explicitly visual-only. It must not bypass the scientific adapters. The existing synthetic P0 demo remains functional during development.

## Proposed implementation PR sequencing

| PR slice | Contents | Owner | Reviewers / evidence |
| --- | --- | --- | --- |
| **I1: dataset custody** | Council tree GeoJSON schema receipt, EA tile acquisition/hashes/rights, metadata manifest | Arnav + Alex | Ben asset/rights review; file receipts; no real-site claim |
| **I2: coordinate + raster importer** | Geodesy accuracy/true north/datum, GeoTIFF read, no-data, alignment, context | Arnav | Alex viewer parity; Ben contracts; known-point tests |
| **I3: city viewer + trees** | MapLibre or justified alternative, terrain/building LOD, source tree point layer, stable selecting inspector, visual-only banner | Alex | Arnav source/position review; performance/accessibility receipts |
| **I4: canopy detection/identity** | Candidate crown segmentation, building exclusion, council/crown matching, feature confidence/evidence | Arnav + Alex | Curated annotation, precision/recall and ambiguity tests |
| **I5: numerical real-site adapter** | Reviewed nonflat terrain and existing occluders, shadow context, candidate/site bundle and source fingerprint | Arnav + Ben | V03/B08 independent evidence, solver/viewer parity; fail-closed retained |
| **I6: Studio result-state UX** | Actual job states, revision/currentness, unsupported/empty modes, agent trace and human approval | Alex + Ben | Same-tools manual+agent traces; stale/late/failure browser tests |
| **I7: compare/report polish** | Physical units, controlled changes, run provenance/rights/survey warnings, responsive captures | Alex | Ben/Arnav semantic check; full keyboard and evidence tests |
| **I8: launch/demo QA** | Current main SHA, UI screenshots, dataset/claims ledger, device/browser QA, release/rollback | Ben integration with all | Full acceptance only after independent reviews |

Check existing issue tracker to avoid duplicate coding tasks. Each implementation PR should refer to the relevant `GEO3D-xx` or `UX3D-xx` acceptance row and actual issue (if assigned), attach reproducible tests and specify what is still unknown.

## Event-day priority and non-interference

The 13 November [event board](../EVENT_DAY_EXECUTION_2026-11-13.md) puts a working integrated deterministic demo, genuine model tool trace, Spark proof and submission evidence ahead of full city ingestion. Treat citywide work as forward-looking P2 and one-site visual pilot as conditional P1; do not disrupt Ben's release/device work or Alex's submission UI.

**Release claim table:**
- **Permitted currently when backed by receipts:** synthetic CPU geometric shade evaluation and constrained search, immutable result provenance, a labelled engineering 3D viewer.
- **Only after actual external data/rights evidence:** real Sheffield 3D **visual context** and source-record tree locations.
- **Only after V03/B08 and numerical parity:** real Sheffield modelled shade benefit.
- **Only after separate validated new models:** °C cooling, AQI, runoff/flood prevention, carbon/biodiversity/monetised return.
- **Only after real model + tool run on device:** adaptive NVIDIA/Nemotron/Spark claims. Browser WebGL GPU work is not CUDA physics.

## Minimum cross-owner review questions

- **Arnav:** Do actual grid+datum and sun/north conventions agree? Are DSM/building/tree semantics and leaf-off limitations honest? Is baseline canopy occlusion unambiguous? Are physical metric and target/time/area basis exact?
- **Alex:** Is City Explorer useful without an accepted site? Can users select recorded/inferred/proposed trees reliably? Does map dominate? Are agent/evidence panels legible at desktop/tablet and accessible by keyboard? Does visual state ever imply a backend calculation not performed?
- **Ben:** Are all displayed source assets rights checked? Are new visual contracts additive/versioned and generated as needed? Do scenario, job, model tool and result revisions remain immutable, bounded, auditable and race-safe? Can the user continue manually when agent/model fails?

## Evidence required in implementation PR descriptions

Repository commit, tool/runtime/device versions, source URLs/capture dates/file SHA-256/licence permissions, dataset sample schema, exact coordinates/transform operation, test command/output, GUI screenshot or browser trace, source/result/run/scenario IDs, supported claims, limitations, affected issues, owners' acceptance and rollback plan. Never call 'docs merged' equivalent to 'feature implemented'.

## Review and merge discipline

Follow the repository's documented feature-branch/PR review process; do not push directly to main or silently change another owner's work. Docs-only PRs can target main for visibility, but **do not merge without appropriate owner review**, especially on this event day. Confirm CI and branch head are current before merging. Ben remains the coordinator for shared BUILD status and application integration; these new files deliberately do not overwrite it.
