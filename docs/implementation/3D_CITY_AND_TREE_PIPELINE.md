# CANOPY Sheffield — 3D city, tree inventory and scientific scene implementation specification

**Status:** implementation proposal for review, **not** a claim of real-site readiness.  
**Date:** 13 November 2026. **Scope:** new geospatial visualisation and tree-identification capabilities with a strict adapter to the existing numerical backend.  
**Owners proposed:** Alex (city frontend/3D interaction); Arnav (geodesy, data semantics, scientific approval); Ben (asset registry, API/job contracts and deploy).  
**Authority:** [BUILD](../BUILD.md) for actual status; [SPEC](../SPEC.md), [CONTRACTS](../CONTRACTS.md) and [NUMERICS](../NUMERICS.md) for supported meaning; [site desk audit](../site-audit/STP-005-desk-audit.md) for acquisition status; [VALIDATION](../VALIDATION.md) for acceptance gates. This is an implementation design, not a replacement for those sources.

## 1. Problem, desired result and hard boundaries

### Current state (repository inspection, 13 Nov)

- `frontend/src/scene/SiteScene.tsx` is a local Three.js engineering viewer: fixed ground/grid and geometric tree proxies; it supports synthetic reference/physical scenes, candidate markers and evaluated layouts. It is **not** a geospatial, tiled 3D model of Sheffield.
- `frontend/src/scene/transform.ts` uses a provisional ENU → Three.js transform (east, up, −north), and reports incompatible bundle matrices; do not assume all real coordinate frames are supported.
- `backend/src/tree_planner/site/import_pipeline.py` rejects every `site_kind != synthetic_test`. `ImportResult.physical_scene` rejects non-flat terrain, unresolved elevated semantics, missing cells and uncertain existing-tree/DSM duplication. `terrain.py` works on prepared in-memory rasters, **not GeoTIFF ingestion**.
- The synthetic numerical evaluation/search and typed immutable result/jobbing pathway exist. Real Weston Park/Manor Fields source files, their hashes, accurate datum/semantic mapping, rights and solver parity have not been accepted. BUILD/B08 govern readiness.
- The [13 Nov site audit](../site-audit/STP-005-desk-audit.md) selects **Weston Park** as geometry pilot and **Manor Fields Park** as fallback. An OSM box is a discovery envelope, **not** surveyed planting land.

### Target user journey

A user opens a georeferenced 3D Sheffield viewer, navigates to Weston Park, displays recorded tree locations and inferred canopy separately, selects a feature to read its source and uncertainty, and requests entry into a site-scale planting workspace. A validated scientific SiteBundle is required for real numerical claims; otherwise the UI remains in **real geographic visualisation only** mode with computation disabled/clearly isolated.

**Non-goals for event-day MVP:** a verified whole-city inventory; citywide numerical optimisation; species/health inferred from height alone; raw DSM-labelled pixels as surveyed trees; arbitrary agent access to source files; planting permission; claims about °C cooling, carbon, AQI, runoff or monetary savings based only on geometric shade. The event-day board identifies citywide ingestion as P2: do not disrupt the working synthetic demo/Spark delivery to pursue this visual milestone.

## 2. Data-source and rights matrix (discovery ≠ ingestion)

| Source | Intended role | Observed/required evidence | Acceptance rule |
| --- | --- | --- | --- |
| [Sheffield Council Street Trees](https://www.data.gov.uk/dataset/957a85f3-d56b-4aed-9f29-5f8fe1363e57/street-trees) | Source-backed street-tree points | Download/API sample, real feature schema, IDs, timestamps, geometry CRS and rights | Never assume citywide completeness or species/size fields until inspected |
| [Community Forestry Trees/Planting Areas](https://ckan.publishing.service.gov.uk/dataset/community-forestry-trees-and-planting-areas) | Planted-tree history and groups | Inspect exact geometry/status/date/rights | Historical planting is not proof of survival or planting permission |
| [EA DTM 1 m](https://environment.data.gov.uk/dataset/13787b9a-26a4-4775-8523-806d13af58fc) | Ground surface | Download tile, hash, CRS, datum, nodata, capture dates, coverage | Ground only; no trees/buildings |
| [EA DSM 1 m](https://environment.data.gov.uk/dataset/9ba4d5ac-d596-445a-9056-dae3ddec0178) (and first-return variant) | Elevated surface and candidate canopy heights | Co-registered DTM/DSM, height semantics, capture season | DSM−DTM ≠ individual tree inventory; includes buildings/objects |
| [OS OpenMap Local](https://www.ordnancesurvey.co.uk/products/os-open-map-local) | Open contextual building/road footprints | Exact downloadable product, date, attribution, accuracy | Generalised footprints ≠ complete roof/wall mesh |
| [OpenStreetMap](https://www.openstreetmap.org/copyright) | Supplementary paths/roads/buildings | Per-feature provenance, ODbL attribution and any sharing/derivation requirements | Discovery footprint and missing map tags ≠ surveyed absence |

The site desk audit reports catalogue coverage of Weston Park in EA tile **SK38NW** and Manor Fields in **SK38NE**; tiles were **not** in the accepted runtime at last review. Its March **16–17 2021** LiDAR flight is plausibly leaf-off for deciduous trees. This creates known summer-canopy incompleteness; do not silently turn that surface into a full leaf-on shade model.

The Weston Park context must include nearby tall obstructions, notably the Arts Tower, subject to validated height/position and directional solar-context rules. The audit's proposed 10° cutoff and 200 m-plus-tall-obstruction envelope require scientific signoff, and a 5° winter sensitivity may imply much larger geometry extents.

## 3. Proposed architecture: one source register, two geometry products

### 3.1 Pipeline stages

1. **Acquisition and custody:** licensed raw asset downloads via human-approved source-list workflows; store raw files outside git, digest SHA-256; record URI, source release, capture date, licence, all four use permissions, required attribution, resolution/coverage, owner and acquisition time. No generic external URL passed by the planning agent.
2. **Verified geodesy:** inspect source coordinate reference system, axis order, precision, units, vertical datum and no-data. EA data are typically BNG/EPSG:27700 with ODN heights. Use an appropriate grid-enabled PROJ transformation (OSTN15/OSGM15 where required), report the selected operation/accuracy and known-point residuals. Do **not** assume a single constant datum offset or equate BNG grid north to true north.
3. **Spatial preparation:** resample/co-register DTM and DSM where necessary with explicit interpolation rules; form coverage masks, capture dates and height residual statistics; handle missing data fail-closed for analysis. Clip a site and independently justified distant shadow context. Never allow a visual tile boundary to truncate an analytical occluder unnoticed.
4. **Semantic separation:** class terrain, building, vegetation and unknown; use rights-cleared footprints/observations and explicit confidence. Height alone is not semantic proof. Keep unknown elevated cells explicit rather than promoting to canopy.
5. **Tree inventory fusion:** ingest authoritative recorded points and supplementary detections as **different evidence classes**; match using geometry, local uncertainty and source dates; preserve stable IDs and unmatched sources. Never merge overlapping crowns on proximity alone without a recorded association.
6. **Visual asset build:** produce terrain LODs, simplified building extrusions/mesh, 3D-tree instances, feature index, tiles/layers, attributes and source overlay metadata; provide citywide/coarse and site/high-detail representations.
7. **Scientific asset build (independent gate):** only from reviewed source geometry, produce receiver samples, static occluders, existing-tree baseline representation, planting regions/exclusions and finite candidate catalogue; register immutable physical scene and exact source fingerprints. A decorative 3D model must never be used as implicit numerics input.
8. **Evaluation/inspection:** inspect-site readiness gates and explicit results connect an accepted SiteBundle to the existing backend; unsupported or non-accepted sites remain visual-only.

### 3.2 Proposed contracts (additive; not existing API)

A versioned `CitySceneManifest` should reference:
- geographic extent, source CRS/datum/operation, local visual origin, units and north convention;
- source hashes and per-asset rights for local use, team sharing, public display and export;
- terrain/buildings/trees/layer tiles and scale/LOD policies;
- feature-index manifest (stable source-backed IDs, geometry type and selection metadata);
- temporal/season coverage and quality, with 'unknown' values preserved;
- inspected/verified status and a labelled relationship to zero or more SiteBundle revisions.

A `TreeFeature` should include stable canonical ID; original source IDs; tree presence class (`recorded_location`, `detected_crown`, `potential_match`, `field_verified`); source and capture date; position and transform identity; optional crown geometry, estimated height and species **only if evidenced**; confidence/evidence class; match links and ambiguity; baseline occlusion ownership; and complete restrictions/uncertainty.

This is a design seam. Before code, Ben owns typed API generation/versioning and Arnav approves spatial/physical meanings. Do not mutate the existing 0.1.0 SiteBundle serialization ad hoc from the browser.

### 3.3 One crown, one baseline occlusion owner

A council point, inferred LiDAR crown and rendered tree icon may describe the same physical tree. They do not automatically represent three independent shading blockers. Introduce `baseline_occluder_ref` / `representation_role` and explicitly map each accepted existing canopy component to **exactly one** computational baseline obstruction. If evidence cannot resolve matching, mark it unknown and block affected real-site shade claims rather than double-counting.

For a given receiver/time/case and fixed baseline, `additional_shade = shade(baseline + proposals) − shade(baseline)` in declared physical units; weighted utility is a separate quantity. Leaf-off DSM crown geometry cannot be used for leaf-on dates without a documented, tested substitution/assumption.

## 4. Individual-tree identification methodology

**Phase 0 — direct point features:** parse downloaded council GeoJSON/ArcGIS features with actual verified schema, retain source record ID and location, show a point icon with `recorded location; not independently field-verified`. Do not invent missing crown/species/health attributes.

**Phase 1 — canopy candidates:** compute CHM = aligned DSM − DTM (after no-data handling) as elevated-object evidence. Exclude confidently classified buildings and unsuitable surfaces, run height filtering/segmentation (e.g. local peaks/watershed), and make crown **candidates**, not certified trees. Record raster scale, thresholds, algorithm version, scene date and confidence proxies. The 1 m source, overlapping crowns and deciduous leaf-off limitations must be visible.

**Phase 2 — matching:** spatially join candidate crowns with inventory points using documented distance/overlap, positional error and source epoch; preserve `recorded-only`, `detected-only`, `matched`, `ambiguous` and `conflicting` cases. Never silently fabricate a tree or species by nearest-object association. Flag problematic occlusion near buildings and park edges.

**Phase 3 — independent validation:** manually annotate a representative local validation set, including buildings, tree clusters, solitary trees and leaf-off cases. Report inventory coverage (unknown if not established), crown-object precision/recall, match precision and positional residuals with confidence stratification. Compare to a simple inventory-only baseline. ML detection (imagery/DeepForest) is optional and gated on image rights, locally relevant annotation and evidence of added value; it is not the required first implementation.

## 5. 3D viewer architecture decision

**Preferred first slice:** georeferenced MapLibre GL JS (terrain if properly prepared, 3D building extrusions and tree feature layers) for City Explorer; retain the current Three.js numerical scene for bounded local planting/evaluation. A future CesiumJS/3D Tiles alternative is valid if profiling or true city-scale mesh requirements justify it. This is a proposal, not a mandated dependency change.

LOD:
- city: downsampled terrain, generalised buildings, area/cluster canopy (no claims of individual tree identity);
- neighbourhood: more detailed buildings, inventory markers, candidate canopy outlines;
- site: instantiated trees, crown geometry and selectable stable IDs;
- analytical: separately validated geometry, receivers, exclusions and proposed placements.

Feature picking returns stable ID/manifest source refs, **not** a visually guessed instance index. Large tile/asset sets require indexed retrieval, camera frustum/LOD controls, bounded memory and a graceful failed/absent tile state.

Camera: georeferenced north, scale and tilt; visible north reset and 2D/3D camera modes where implemented. City-to-site transition preserves selection and geography; demonstrate with known points and metre-scale objects. Browser GPU rendering is **not** DGX Spark GPU numerics.

## 6. Scientific adapter and current code blockers

| Existing component | Required change | Gate/owner |
| --- | --- | --- |
| `site/terrain.py` and `site/import_pipeline.py` | Add GeoTIFF read/metadata, validated grid transform, aligned clipping and real-site pathway; **do not** remove fail-closed real-site restriction until V03 proves prerequisites | Arnav + Ben |
| `site/transform.py` / `frontend/src/scene/transform.ts` | Explicit verified CRS↔ENU/visual transform, true north, datum, site origin; no silently provisional fallback for real numerical scenes | Arnav + Alex |
| `site/assets.py` / site service | Store source use permissions, capture/semantic metadata, fingerprints and asset IDs; rights check per display and export | Ben |
| `frontend/src/scene/SiteScene.tsx` | Preserve synthetic scientific layer; add site geometry selection and measured scene-vs-solver parity after approval | Alex + Arnav |
| New city source/visual pipeline | CityScene and TreeFeature schema, indexed 3D tile/render assets, inventory and detected canopy layers | Alex + Arnav; Ben reviews schema |
| Physical evaluator | Non-flat ground placement/candidate/receiver support and static obstruction correctness, with physical regression evidence | Arnav + Ben |

**Do not** remove source-rights, hash/identity, unknown-semantic, unsupported-mode, or no-real-site safety checks just to make a mesh render.

## 7. Implementation slices and acceptance evidence

| ID | Slice | Concrete acceptance | Status |
| --- | --- | --- | --- |
| GEO3D-01 | Acquire source inventory | Street Trees/Community Forestry sample downloaded, fields/licences/geometry/rights recorded, hash manifest | NOT VERIFIED |
| GEO3D-02 | Acquire Weston Park EA tiles | SK38NW DTM/DSM/first-return exact files, SHA-256, nodata/CRS/datum/capture metadata and coverage/context checked | NOT VERIFIED |
| GEO3D-03 | Geodesy proof | Grid-enabled transform, known-point + round-trip and true-north metre-scale checks, accepted accuracy threshold | NOT VERIFIED |
| GEO3D-04 | Basic real visual pilot | Right-cleared terrain/building/recorded tree layers render in a tiltable 3D Weston Park scene | NOT VERIFIED |
| GEO3D-05 | Tree identification | Unknown/recorded/matched/detected data model, curated validation sample and classification error report | NOT VERIFIED |
| GEO3D-06 | Visual/physics split | Same selected location/source identities, no double-counting, clear visual-only mode | NOT VERIFIED |
| GEO3D-07 | Real numerical adapter | Non-flat site targets/candidates, reviewed obstructions/context, failed/valid cases, immutable result provenance | BLOCKED: V03/B08 |
| GEO3D-08 | Performance and accessibility | Measured viewport loads, frame times, memory, feature selection and keyboard/alternative table interactions | NOT VERIFIED |

This document makes no claim of having downloaded a tile, derived trees, solved real-site physics, or validated an actual Sheffield planting polygon. Scene quality must never substitute for scientific validity.

## 8. Required tests

**Data:** invalid CRS, wrong axis, missing OSTN/OSGM resource, unknown vertical datum, mismatched pixel grids, no-data strip, stale/duplicate source ID, rights restricted/unknown, capture-epoch mismatch, semantic unknown. All produce explicit typed failures or visually limited data.

**Tree matching:** recorded-only, detected-only, overlap, ambiguous multi-crown, building false positive, positional offset, leaf-off absent crown, tree removed after source epoch, protected/plantability unknown. Preserve original records for audit; never convert an inventory gap to absence.

**Rendering:** terrain height and north control vs known reference; camera and identity persistence across LOD; tile error; stable feature picking; icon/outline for each evidence class; 2D/3D mode correctness; responsive and reduced-motion alternatives.

**Numerics:** non-flat placement z; terrain intersection; static building/vegetation shading with identical baseline; directional context; measured receiver triangle area; one-crown-one-occluder; incomplete data blocked; comparison same inputs; no phantom cooling/thermal/flood result; visual-to-physics geometry parity.

**Ownership:** reviewers Arnav (science), Alex (visual), Ben (API/source); exact branch SHA, data receipts, measured validation and non-deceptive UI screenshot attached to the eventual implementation PR. Production merge follows [AGENT_EXECUTION_PRD](../AGENT_EXECUTION_PRD.md) and BUILD gates. This document alone does not authorize a code merge or a real-site claim.
