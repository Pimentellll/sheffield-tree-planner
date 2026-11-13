# STP-005 — Sheffield site and source desk audit

**Author:** Alex's coding assistant for Alex · **checked:** 12 November 2026, context/coverage update 13 November 2026 · **state:** candidate assessment, not an accepted SiteBundle or planting permission.

## Site decision for the next data check

**Primary geometry pilot: Weston Park. Fallback: Manor Fields Park.** [Sheffield City Council identifies Weston Park as a city park](https://www.sheffield.gov.uk/parks-sport-recreation/parks-gardens/weston-park) and [lists Manor Fields Park as a district park](https://www.sheffield.gov.uk/parks-sport-recreation/parks-gardens/parks-green-spaces). This identifies real places, not validated planting regions. The design's Kelham Island and Neepsend scene remains a visual placeholder.

Weston Park has a material additional constraint: [Historic England registers it as a Grade II park and garden, entry 1001340](https://historicengland.org.uk/listing/the-list/list-entry/1001340). The pilot can test geometry and viewer orientation, but any proposed planting position needs separate heritage, land manager, utility, soil and access review. Manor Fields is a fallback for the geometry pilot if Weston Park's coverage or contextual obstructions prove unsuitable; it has not been assessed for planting permission either.

### Candidate extents for the first coverage query

The boxes below are the min/max node coordinates of [OSM way 16641193](https://www.openstreetmap.org/way/16641193) and [OSM way 22958399](https://www.openstreetmap.org/way/22958399), queried from the OSM API on 12 November. They are **discovery envelopes only**: neither a surveyed boundary nor a planting polygon. [OSM data is ODbL licensed and requires attribution](https://www.openstreetmap.org/copyright); no OSM geometry has been put into the application.

| Candidate | Latitude min–max | Longitude min–max | Immediate use |
| --- | --- | --- | --- |
| Weston Park | 53.3810144–53.3838111 | −1.4927228 to −1.4879217 | Search for intersecting EA tiles and sufficient surrounding context. |
| Manor Fields Park | 53.3654730–53.3743068 | −1.4372009 to −1.4277104 | Fallback coverage search; verify the mapped way matches the intended park. |

The [EA composite catalogue FeatureServer](https://environment.data.gov.uk/KB6uNVj5ZcJr7jUP/ArcGIS/rest/services/LIDAR_Composite_Catalogues/FeatureServer) returned one intersecting record for **each** box in its 1 m first-return DSM, last-return DSM and DTM 2022 extent layers (0, 1 and 2). All six records give survey start **16 March 2021**, end **17 March 2021**, `year=2021`, `resolution=1`, `comp_year=2022`; the internal polygon filenames are `FZ_DSM_P_10706`, `D_DSM_P_10706` and `F_DTM_P_10706`. The catalogue returned `tilename=n/a`, so these are **not** downloadable tile IDs. This shows catalogue coverage and matching survey dates at the query boxes; actual tile contents, co-registration and completeness still need inspection.

## Shadow-context envelope and tile coverage (13 November 2026, response to Arnav's review on #39)

Arnav asked for an agreed low-sun cutoff and an obstruction-height envelope (horizontal reach *H* / tan *e*) before a real crop is selected, then actual tile coverage and height evidence. This section proposes the envelope and records what could be checked without downloading tiles. **The cutoff and buffers are proposals for Arnav to accept or change; nothing here is an accepted analysis setting.**

### Method and accuracy

- Sun positions: `pvlib` 0.16.1 NREL SPA (`get_solarposition`, apparent elevation with refraction), park centroids, 100 m altitude. Computed locally, 13 Nov 2026.
- WGS84 → BNG: `pyproj` 3.8.0 / PROJ 9.8.1 default EPSG:4326 → EPSG:27700 operation **without the OSTN15 grid** (none installed here). Expect metre-level horizontal error, which is adequate for choosing an envelope and tile but **not** for co-registration. The real-site import must use OSTN15, as Arnav's STP-006 work already requires.
- Discovery boxes are still the OSM way node extents above, not surveyed boundaries.

### Solar geometry at the candidates

Values for Weston Park (Manor Fields differs by under 0.05°):

| Case | Sun elevation |
| --- | --- |
| 15 July (summer design day) | 58.1° max at 12:10 UTC; 24.2° at 07:00 UTC (08:00 BST); 10.3° at 19:00 UTC (20:00 BST) |
| 21 June | 60.1° max; 11.4° at 19:00 UTC |
| 20 March | 36.6° max |
| 21 December | **13.2° max** at 12:00 UTC; ≥ 10° only 10:20–13:48 UTC (3.5 h); ≥ 5° 09:15–14:54 UTC (5.7 h); never reaches 15° |

### Proposed cutoff and reach

**Proposal:** a **10° low-sun cutoff** for the summer benefit case (the 08:00–20:00 BST window on the July design day never drops below 10.3°), and the same 10° for the winter check, stated as a limitation that it covers only 3.5 h on 21 December. A 5° winter cutoff would more than double the reach (table) and needs a decision from Arnav.

Horizontal shadow reach *H* / tan *e*, in metres:

| Obstruction height *H* | *e* = 5° | 10° | 15° | 20° | 24.2° (07:00 UTC, July) |
| --- | --- | --- | --- | --- | --- |
| 10 m | 114 | 57 | 37 | 27 | 22 |
| 20 m | 229 | 113 | 75 | 55 | 45 |
| 30 m (mature trees, most buildings) | 343 | **170** | 112 | 82 | 67 |
| 50 m | 572 | 284 | 187 | 137 | 111 |
| 78 m (Arts Tower) | 892 | **442** | 291 | 214 | 174 |

**Proposed context envelope:** the study box plus a **200 m all-round buffer** (covers obstructions up to about 35 m at 10°). For each named structure taller than 35 m, extend to that structure's own *H* / tan 10° on its sun-facing side. A directional (azimuth-limited) envelope would be smaller. That is a later optimisation, which needs Arnav's sign-off that no shading direction is dropped.

### Named tall obstruction: Arts Tower next to Weston Park

The University of Sheffield's [Arts Tower](https://sheffield.ac.uk/news/iconic-arts-tower-university-sheffield-celebrates-60-years) is 78 m tall. Its published coordinates, [53.382738° N, 1.487289° W](https://en.wikipedia.org/wiki/Arts_Tower), convert to about BNG (434201, 387444). That is **about 40 m east of the Weston Park discovery box**, within the box's northing range. On 15 July the sun's azimuth is 86° at 07:00 UTC (08:00 BST) and its 24.2° elevation gives a 174 m reach, so the tower's shadow points almost due west across the park's east side during the start of the benefit window. Before 07:00 UTC the reach is longer still (217 m at 06:30, 282 m at 06:00 UTC). **The Weston Park scene must include the tower and the surrounding university buildings in its context DSM.** Omitting them would overstate the shade added by new trees on the east side in the morning. Other nearby buildings (Western Bank Library, Firth Court, Weston Park Museum, the Children's Hospital) need heights from the DSM itself. No height for them is asserted here.

### Tile coverage at the buffered extents (catalogue check, no download)

Buffered boxes (BNG, metres, with a 450 m buffer, enough for the Arts Tower at 10°):

| Candidate | Box (E min, N min → E max, N max) | 5 km OS tile |
| --- | --- | --- |
| Weston Park | 433389, 386799 → 434611, 388013 | **SK38NW** (430000–435000 E, 385000–390000 N) |
| Manor Fields Park | 437091, 385098 → 438630, 386986 | **SK38NE** (435000–440000 E, 385000–390000 N) |

Both boxes fall inside a single 5 km tile each, even at the 450 m buffer. A 5° winter cutoff with the Arts Tower (892 m) would push Weston Park's east edge past 435000 E into SK38NE.

On 13 November the [EA composite catalogue FeatureServer](https://environment.data.gov.uk/KB6uNVj5ZcJr7jUP/ArcGIS/rest/services/LIDAR_Composite_Catalogues/FeatureServer) was queried with these buffered boxes (EPSG:27700 envelopes). The DTM layer (2), last-return DSM layer (1) and first-return DSM layer (0) each returned **one** survey polygon, `P_10706` (area 395.1 km²; filenames `F_DTM_P_10706`, `D_DSM_P_10706`, `FZ_DSM_P_10706`; flown 16–17 March 2021; `comp_year` 2022). `spatialRel=esriSpatialRelWithin` returned that polygon and `esriSpatialRelContains` returned nothing. So each buffered box lies **entirely within one survey**: no composite seam or mixed survey dates in the context. `tilename` is still `n/a`, so the downloadable tile names above are derived from the OS grid, not from the catalogue.

Mid-March flight dates mean deciduous canopy is **leaf-off** in the DSM. First-return heights of deciduous trees will under-represent summer crowns. That is a modelling gap for existing-tree shading, which Arnav should decide how to handle; it is not a reason to reject the source.

### Vertical datum evidence

EA states that composite LIDAR data is presented in metres, referenced to Ordnance Survey Newlyn using the OSTN'15 transformation, aligned to the OS National Grid, with a stated ±15 cm vertical RMSE per survey. Sources: the [data.gov.uk DSM record](https://www.data.gov.uk/dataset/cf3f1137-c12b-44a1-a835-e80fe4a60b92/lidar-composite-digital-surface-model-dsm-1m); provider text reproduced in the [Earth Engine catalogue entry for the 2022 composite](https://developers.google.com/earth-engine/datasets/catalog/UK_EA_ENGLAND_1M_TERRAIN_2022); the EA [time-stamped tile metadata](https://www.data.gov.uk/api/2/rest/harvestobject/96bc1d9e-9341-40c2-aaa0-c24d40accb2d/html) (OS Newlyn, 5 km GeoTIFF zips). The EA dataset page itself renders client-side and could not be read here. **Record as: ODN heights (OSGM15-based, via OSTN15), status "documented by publisher, not yet confirmed from the file".** Confirm against the *LIDAR Composite Technical Information Guide* linked from the [EA DSM page](https://environment.data.gov.uk/dataset/9ba4d5ac-d596-445a-9056-dae3ddec0178) and the downloaded GeoTIFF metadata. To compare with GNSS or ellipsoidal heights, use the EPSG:7405 → ellipsoidal path Arnav prepared (OSTN15 + OSGM15), not a constant offset.

### Still blocked, and exactly what unblocks it

This environment cannot reach the EA download service, so **tile hashes, nodata values and actual file CRS/datum tags are not recorded**. To unblock, someone with a normal browser does the following:

1. Go to https://environment.data.gov.uk/survey and draw an area covering the Weston Park box above.
2. Choose *LIDAR Composite DTM* and *LIDAR Composite DSM* (first and last return), 2022, 1 m. Download **SK38NW** (and **SK38NE** for the fallback).
3. Record each downloaded file name, byte size and SHA-256 (`sha256sum` / `Get-FileHash`), and from `gdalinfo` the CRS, nodata value and any vertical datum tag.
4. Add those rows to this audit as the asset manifest. Keep raw tiles out of git: they are OGL, but large, and need the EA attribution statement wherever displayed.

Next owner: Arnav accepts or changes the 10° cutoff and the 200 m / per-structure buffer, then crops SK38NW for the STP-006 import. Whoever downloads the tiles records the hashes here.

## Source and rights register

Rights below apply to the **named source product** under its published terms. No source asset has been downloaded, hashed, transformed or committed. A future SiteBundle must attach the specific acquired tile/version and rights evidence before display or export.

| Source | What was checked on 12 Nov 2026 | Local / team / public display / export decision | Data and modelling gap |
| --- | --- | --- | --- |
| [EA LiDAR composite DTM, 1 m](https://environment.data.gov.uk/dataset/13787b9a-26a4-4775-8523-806d13af58fc) | Publisher metadata says terrain raster, EPSG:27700, OGL; composite survey period 2000–2022; EA attribution. Catalogue coverage at both candidate boxes is from March 2021. | OGL appears to permit reuse with attribution for all four purposes; **asset-level decision pending tile selection and licence check**. | Need actual tile, vertical datum confirmation, nodata, crop, ground control and context. DTM alone has no trees/buildings. |
| [EA LiDAR composite DSM, 1 m](https://environment.data.gov.uk/dataset/9ba4d5ac-d596-445a-9056-dae3ddec0178) | Publisher metadata says surface raster containing buildings, vegetation and vehicles; OGL. Catalogue DSM coverage at both boxes shares the DTM's March 2021 survey dates. | Same conditional OGL decision as DTM. | Need actual tile and co-registration check. DSM minus DTM cannot reliably classify crowns, roofs or vehicles; leaf state and currentness unknown. |
| [EA survey download and catalogue](https://environment.data.gov.uk/survey) | Official portal supports area selection; [Defra says composite GeoTIFFs are supplied as 5 km tiles](https://environment.data.gov.uk/support/faqs/275808874/275809211). | Data discovery only; no tile rights inferred from portal access alone. | Select park and shadow-casting context; record tile IDs, exact capture dates, hashes and coverage. The current desk audit does not establish that either site is covered by matching tiles. |
| [OS Open Zoomstack](https://www.ordnancesurvey.co.uk/products/os-open-zoomstack) | OS describes an open, street-scale vector basemap; [OS says OpenData uses OGL terms](https://www.ordnancesurvey.co.uk/products/product-support). | Candidate contextual basemap under OGL with OS attribution; **actual product/version and asset selection pending**. | Cannot replace LiDAR, survey, planting boundaries or authoritative building heights. |
| [OS OpenMap Local](https://www.ordnancesurvey.co.uk/products/os-open-map-local) | OpenData at 1:10,000 includes generalised contextual building features; [OS lists it under OGL OpenData](https://www.ordnancesurvey.co.uk/products/open-data). | Candidate local/team/display/export source with OGL attribution, subject to exact downloaded product terms. | Generalised outlines are not a survey, detailed roof geometry or reliable ray occluders. Do not substitute OS premium Building Features or MasterMap under OpenData rights. |
| [Sheffield City Council Weston Park page](https://www.sheffield.gov.uk/parks-sport-recreation/parks-gardens/weston-park) and [park list](https://www.sheffield.gov.uk/parks-sport-recreation/parks-gardens/parks-green-spaces) | Names, public description and facility context only. The [council's Weston Park PDF map](https://www.sheffield.gov.uk/sites/default/files/2024-03/weston_park_map.pdf) includes OS copyright notice. | Reading/citation permitted for this audit; **reproduction, derivative map display and export unknown** pending the specific material's rights check. Do not copy the council/OS PDF into the app. | Park page/map does not provide a planting polygon, underground-service survey or true current tree inventory. |
| [Council tree protection map](https://www.sheffield.gov.uk/planning-development/conservation-design/tree-works-protected-trees) | Council says the online TPO/conservation map may lag new orders and advises contacting it where uncertain. A [sample council TPO PDF](https://www.sheffield.gov.uk/sites/default/files/docs/your-city-council/legal-services/Tree%20Preservation%20Order%20419A.pdf) carries an OS notice permitting viewing only and barring copy/distribution. | Read/cite protection guidance. **Do not copy or export the map/PDF data** without asset-specific permission. Local product ingestion is unresolved. | TPO layer is not a complete tree inventory or proof that an unmarked tree is unprotected. Check orders and site conditions through appropriate survey/authority process. |
| [Historic England Weston Park list entry](https://historicengland.org.uk/listing/the-list/list-entry/1001340) | Grade II registration and list entry identity. | Cite as contextual evidence; **asset/map reuse unknown**. | Heritage designation is a review flag, not an automated feasibility rule without verified boundaries and policy interpretation. |

[The National Archives' OGL attribution guidance](https://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/uk-government-licensing-framework/open-government-licence/copyright-notices-attribution-statements/) requires identification of the information provider/source and a licence link. [Sheffield Council says data may carry terms other than OGL](https://www.sheffield.gov.uk/your-city-council/about-council/access-to-information). The final asset manifest must carry the exact attribution required by each downloaded product; an OGL label on EA data does not clear unrelated council or OS map artwork.

## Required handoff before real scene use

1. With Arnav, select the bounded park extent **and surrounding low-sun shadow context**. Retrieve intersecting EA DTM/DSM tiles using the catalogue records above, then confirm full context coverage and acquisition dates. Record the exact source tile IDs, SHA-256, CRS EPSG:27700, vertical datum, resolution, nodata and rights statement.
2. Verify a surveyed known point, true north, metre scale and `analysis_to_viewer` transform. Classify or mark unknown static obstructions and existing trees; avoid representing a LiDAR crown twice. Test DTM/DSM alignment and season/context limits with Arnav.
3. Choose permitted context/boundary assets separately. Source downloadability or a public park name never certifies team sharing, app display, export, planting permission, current canopy or a feasible tree location.
4. Ben's registry and rights validator should distinguish `permitted`, `restricted` and `unknown` for local use, team sharing, public display and export. This document is not a runtime registry or accepted site status.

**Current disposition (13 Nov):** neither candidate passes V03. The context envelope is proposed and catalogue coverage of the buffered extents is confirmed (one March 2021 survey each). Tile hashes, file-level datum and nodata, and Arnav's acceptance of the envelope are outstanding. Continue with the labelled synthetic frontend scene and analytic tests. No real Sheffield geometry or dataset asset has been added to the product.
