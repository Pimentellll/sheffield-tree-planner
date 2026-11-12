# STP-005 — Sheffield site and source desk audit

**Author:** Alex's coding assistant for Alex · **checked:** 12 November 2026 · **state:** candidate assessment, not an accepted SiteBundle or planting permission.

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

## Source and rights register

Rights below apply to the **named source product** under its published terms. No source asset has been downloaded, hashed, transformed or committed. A future SiteBundle must attach the specific acquired tile/version and rights evidence before display or export.

| Source | What was checked on 12 Nov 2026 | Local / team / public display / export decision | Data and modelling gap |
| --- | --- | --- | --- |
| [EA LiDAR composite DTM, 1 m](https://environment.data.gov.uk/dataset/13787b9a-26a4-4775-8523-806d13af58fc) | Publisher metadata says terrain raster, EPSG:27700, OGL; composite survey period 2000–2022; EA attribution. Catalogue coverage at both candidate boxes is from March 2021. | OGL appears to permit reuse with attribution for all four purposes; **asset-level decision pending tile selection and licence check**. | Need actual tile, vertical datum confirmation, nodata, crop, ground control and context. DTM alone has no trees/buildings. |
| [EA LiDAR composite DSM, 1 m](https://environment.data.gov.uk/dataset/9ba4d5ac-d596-445a-9056-dae3ddec0178) | Publisher metadata says surface raster containing buildings, vegetation and vehicles; OGL. Catalogue DSM coverage at both boxes shares the DTM's March 2021 survey dates. | Same conditional OGL decision as DTM. | Need actual tile and co-registration check. DSM minus DTM cannot reliably classify crowns, roofs or vehicles; leaf state and currentness unknown. |
| [EA survey download and catalogue](https://environment.data.gov.uk/survey) | Official portal supports area selection; [Defra says composite GeoTIFFs are supplied as 5 km tiles](https://environment.data.gov.uk/support/faqs/275808874/275809211). | Data discovery only; no tile rights inferred from portal access alone. | Select park and shadow-casting context; record tile IDs, exact capture dates, hashes and coverage. The current desk audit does not establish that either site is covered by matching tiles. |
| [OS Open Zoomstack](https://www.ordnancesurvey.co.uk/products/os-open-zoomstack) | OS describes an open, street-scale vector basemap; [OS says OpenData uses OGL terms](https://www.ordnancesurvey.co.uk/products/product-support). | Candidate contextual basemap under OGL with OS attribution; **actual product/version and asset selection pending**. | Cannot replace LiDAR, survey, planting boundaries or authoritative building heights. |
| [Sheffield City Council Weston Park page](https://www.sheffield.gov.uk/parks-sport-recreation/parks-gardens/weston-park) and [park list](https://www.sheffield.gov.uk/parks-sport-recreation/parks-gardens/parks-green-spaces) | Names, public description and facility context only. The [council's Weston Park PDF map](https://www.sheffield.gov.uk/sites/default/files/2024-03/weston_park_map.pdf) includes OS copyright notice. | Reading/citation permitted for this audit; **reproduction, derivative map display and export unknown** pending the specific material's rights check. Do not copy the council/OS PDF into the app. | Park page/map does not provide a planting polygon, underground-service survey or true current tree inventory. |
| [Historic England Weston Park list entry](https://historicengland.org.uk/listing/the-list/list-entry/1001340) | Grade II registration and list entry identity. | Cite as contextual evidence; **asset/map reuse unknown**. | Heritage designation is a review flag, not an automated feasibility rule without verified boundaries and policy interpretation. |

[The National Archives' OGL attribution guidance](https://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/uk-government-licensing-framework/open-government-licence/copyright-notices-attribution-statements/) requires identification of the information provider/source and a licence link. The final asset manifest must carry the exact attribution required by each downloaded product; an OGL label on EA data does not clear unrelated council or OS map artwork.

## Required handoff before real scene use

1. With Arnav, select the bounded park extent **and surrounding low-sun shadow context**. Retrieve intersecting EA DTM/DSM tiles using the catalogue records above, then confirm full context coverage and acquisition dates. Record the exact source tile IDs, SHA-256, CRS EPSG:27700, vertical datum, resolution, nodata and rights statement.
2. Verify a surveyed known point, true north, metre scale and `analysis_to_viewer` transform. Classify or mark unknown static obstructions and existing trees; avoid representing a LiDAR crown twice. Test DTM/DSM alignment and season/context limits with Arnav.
3. Choose permitted context/boundary assets separately. Source downloadability or a public park name never certifies team sharing, app display, export, planting permission, current canopy or a feasible tree location.
4. Ben's registry and rights validator should distinguish `permitted`, `restricted` and `unknown` for local use, team sharing, public display and export. This document is not a runtime registry or accepted site status.

**Current disposition:** neither candidate passes V03. Continue with the labelled synthetic frontend scene and analytic tests. No real Sheffield geometry or dataset asset has been added to the product.
