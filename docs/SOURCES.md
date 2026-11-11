# Sources and evidence boundaries

These sources were inspected during the preceding research preparation, not freshly re-audited by writing these development docs. Links support source facts, not compatibility, performance, originality or completed-product claims. Verify relevant current versions/licences again during implementation.

**User-reported precedent:** on 11 November 2026, Ben reported that the previous team developed a week before its hackathon and stated the intention to document then develop before this event. That timing was not independently verified here. UCL confirms a prior winning project [23], not current advance-code permission. The official event page [6] and organiser clarification, not precedent, govern eligibility.

**Known source limitations:** planting-area records are historical, School Localities are not grounds/buildings, tree points lack full crown dimensions, and some park/street-tree sources link restrictive INSPIRE terms. Downloadability is not a blanket reuse licence. No restricted raw assets are included in this documentation pack.

The working stack is a proposal. NVIDIA hardware capabilities and Warp/platform documentation do not prove this application's runtime, RT-core use or acceleration. TreePlanter is relevant prior art; our intended agent value still needs the same-tools comparison in VALIDATION.

## Candidate site geometry source: Environment Agency LiDAR (11 November 2026 desk audit)

**Status: candidate for B03, not an accepted Sheffield site asset.** The [Defra Survey Data Download](https://environment.data.gov.uk/survey) [24] offers Environment Agency 1 m composite [DSM](https://environment.data.gov.uk/dataset/9ba4d5ac-d596-445a-9056-dae3ddec0178) [25] and [DTM](https://environment.data.gov.uk/dataset/13787b9a-26a4-4775-8523-806d13af58fc) [26]. Publisher metadata describes approximately 99% coverage of England, GeoTIFF elevation rasters provided in 5 km National Grid tiles, horizontal CRS EPSG:27700, heights in metres relative to Ordnance Datum Newlyn, and Open Government Licence terms with Environment Agency attribution. The 2022 composite may use surveys acquired between 2000 and April 2022; check the survey index for the selected Sheffield location rather than assuming a 2022 capture or current canopy. The publisher's ±15 cm RMSE statement concerns underlying survey vertical accuracy, not validated tree or roof reconstruction.

**Proposed use, conditional on B03/V03:** select one bounded Sheffield park/playground plus sufficient off-site shadow-casting context; download overlapping DTM and DSM tiles; check their survey dates, coverage, coordinate reference, vertical datum, no-data values and alignment; crop and preprocess to terrain and static-obstruction geometry. An indicative DSM-minus-DTM height layer may help find obstacles but does not identify which are buildings, trees or temporary objects. Classify/validate geometry using independent permitted evidence or explicitly declare unknown semantics. Transform to the site's local east/north/up metre frame, retain surveyed source positions and produce consistent ray-query and Three.js display assets with hashes and provenance. Run checks for a known reference point, orientation, lengths/heights, canopy double-counting, and low-sun context before claiming real-site shade results.

**Limitations and rights gate:** these are elevation *rasters*, not a ready-to-use semantic 3D city mesh, full LiDAR point cloud, detailed crown model, planting permission or utility/soil survey. A 1 m DSM can smooth building edges, mix foliage/roofs/vehicles, and cannot reliably infer winter leaf-off transmission or species-specific canopies. The composite can be old or stitched from different surveys; reject or flag materially inconsistent DTM/DSM pairing and changed vegetation/buildings. The product's proposed ellipsoid/trunk tree model is separate from this static reconstruction. Confirm current OGL terms, attribution and permitted sharing/display/export for each actual source and derivative; this does **not** clear the separate Sheffield Council INSPIRE-licensed layers. Do not commit unreviewed raw assets to this repository.

**Feasibility decision:** suitable for an *offline, site-sized preprocessing pilot* supporting the local deterministic simulator, with a good chance of meeting R01 if audited. It is not necessary to reconstruct all Sheffield, provide a live nationwide data feed, or couple the model to Defra at runtime. Before selection under B03, demonstrate a reproducible cropped import; acceptable survey recency; independently checked ground/building heights and scene semantics; a tractable mesh and visual/solver transform; lawful use and export flags; and a fallback site/source if any blocking gap remains. No tiles, meshes or Sheffield numerical results were downloaded/validated as part of this desk audit. The [Defra download FAQ](https://environment.data.gov.uk/support/faqs/275808874/275809211) [27] documents selecting an area of interest and available product/year/resolution tiles.

## User-supplied reference shortlist (11 November 2026)

These user-provided links are **research/design comparators or possible spatial data sources, not automatically downloadable environmental measurements**. They were added before the follow-on traffic/CO2/water dataset search. Treat relevance, API/data availability, access terms and model validity as separate questions; audit before importing or making numerical claims. The TreePlanter link was supplied twice (including a tracking-parameter variant) but was **already recorded as [1]**, so it is not duplicated.

- **[1] TreePlanter (already cited)**: numerical/optimisation precedent for siting trees and analysing shading; not Sheffield monitoring data.
- **[28] PlanIT Geo TreePlotter Projects**: product/example gallery; investigate workflow/data-display ideas, not assume access to project records.
- **[29] UK Tree Equity Score**: possible equity/context and canopy-prioritisation comparator; verify downloadable geography, resolution, update date and reuse rights before any scored feature.
- **[30] ShadeMap**: visual sun/shadow comparison reference; not verified to supply reusable geometry or quantitative simulation input.
- **[31] Schrodi et al., Climate-Sensitive Urban Planning Through Optimization of Tree Placements**: research on tree placement using neural surrogate estimates of mean radiant temperature and iterated local search. A research comparator, not Sheffield observations; adding a thermal-comfort surrogate is outside the validated first-version evaluator.
- **[32] Autodesk Forma site-design overview (August 2026)**: planning/visualisation/workflow comparator; no assumed access to proprietary analysis layers or algorithms.
- **[33] Ordnance Survey OS Open Zoomstack**: potential open base-map vector layers to give geographic context; assess feature types and licensing. Not a substitute for metre-resolved LiDAR geometry or planting/flood/traffic measurements.

## Sheffield traffic, flood and water dataset discovery (11 November 2026)

**Status: researched candidates only.** Following the user-supplied reference additions, the following publisher/data records were checked for relevance to the Sheffield Tree Planner. They have **not** been imported, clipped to a nominated Sheffield site, independently field-validated, measured in runtime, or accepted by the team. The current R01–R10 product remains a direct-sun/shade tool; these data can inform context or future explicitly validated modules. Every imported layer must still pass CONTRACTS/SiteBundle provenance, scale, dates, licence, attribution and V03 checks. Prefer rights-cleared small local extracts over citywide downloads.

**Traffic emissions, CO2 and road exposure**

| Ref | Source and content | Project use / boundary |
| --- | --- | --- |
| [34] | DESNZ local-authority greenhouse gases, 2005–2024, XLSX/CSV (released June 2026) | **Medium**: Sheffield road-transport CO2/CO2e baseline and official historical comparisons; local-authority totals are not park-level road emissions, pollution concentrations or tree-sequestration estimates. |
| [35] | DfT Sheffield road traffic statistics, AADF/count points, vehicle classes, raw counts, CSV/JSON | **High contextual**: locate higher traffic corridors and prioritise shade/exposure zones; count estimates and road coverage have quality limits; volume is *not* CO2 without a validated vehicle/fuel/emissions model. |
| [36] | NAEI gridded emissions, UK-wide ~1 km sector/pollutant/year datasets | **Medium**: spatial *emissions inventory* context if a CO2/road-transport layer is obtainable; not measured ambient CO2, and 1 km grid is coarse for a park. Check sector definitions, licence, pollutant availability and year. |
| [37] | NAEI major-road emissions 2024 workbook | **Medium**: potential road-link inventory; inspect whether selected workbook contains required CO2 fields and compatible geometries before selecting. **Access note:** NAEI website currently redirected to a maintenance notice during this desk audit; download not confirmed. |

**Floodplains, pluvial flooding and existing flood infrastructure**

| Ref | Source and content | Project use / boundary |
| --- | --- | --- |
| [38] | EA Flood Map for Planning, river/sea Flood Zones 2 and 3 (GeoPackage/GeoJSON, updated Oct 2026) | **High contextual**: floodplain screening and provisional exclusion/warning layers; ignores the benefit of flood defences and is not site-specific planting consent or a hydrologic planting-benefit estimate. |
| [39] | EA Risk of Flooding from Surface Water (RoFSW), 2 m model-derived risk/depths | **High contextual**: identify local ponding/runoff-risk locations, distinct from river floodplains; modelled probabilistic risk, not observed rainfall nor tree-specific effect. |
| [40] | EA Surface Water Spatial Planning Extents and depths, present-day | **High contextual**: available flood likelihood / depth bands (3.3%, 1%, 0.1% AEP), but check source scenario definitions and rights; not a direct hydraulic simulation. |
| [41] | EA Recorded Flood Outlines, OGL, historic event polygons | **Medium**: historical checks/interpretation; incompleteness means no outline does *not* mean no flood. |
| [42] | Sheffield City Council Strategic Flood Risk Assessment (2023 study/maps) | **Medium**: city-specific interpretation/constraints; some zones predate revised EA models, so prefer updated official flood products for current extents. |
| [43] | EA Flood Zones plus Climate Change | **Medium**: long-horizon context; not a forecast of effect of planting trees. |
| [44] | Sheffield SuDS Regions, OGL GeoJSON/geoservice | **High contextual**: distinguish mapped sustainable-drainage regions, where present. Indicative and not surveyed. |
| [45] | Sheffield SuDS Links, OGL GeoJSON/geoservice | **High contextual**: network/link geometry for mapped drainage infrastructure; verify actual site alignments. |
| [46] | Sheffield Highway Drain Links, OGL GeoJSON/geoservice | **High contextual**: road drainage proximity and possible planting conflicts; not an underground-utilities clearance certificate. |
| [47] | Sheffield Open Watercourse Links, OGL GeoJSON | **High contextual**: city-scale mapped streams, including potential streamside siting exclusions. Indicative only. |
| [48] | Sheffield Watercourse Culvert Links, OGL GeoJSON | **High contextual**: buried/channelled watercourse context and root-space issues; verify on site. |
| [49] | Sheffield Section 21 flood-management asset register, OGL GeoJSON nodes/links | **High contextual**: screening for recorded infrastructure; not proof every underground asset is present. |
| [50] | OS Open Rivers, freely available vector watercourse data | **Medium**: national consistent river/waterway backdrop, less specific than mapped local assets. |

**Rain, irrigation-related water demand, soils and catchments**

| Ref | Source and content | Project use / boundary |
| --- | --- | --- |
| [51] | Met Office HadUK-Grid daily/monthly precipitation, 1 km NetCDF, OGL | **High optional**: historic rainfall and summer dry-period context; not a site irrigation record or local precipitation-gauge measurement. |
| [52] | EA Potential Evapotranspiration/PETI, daily 1 km, 1961 onward, ZIP | **High optional**: atmospheric evaporative demand and moisture-balance exploration; based on well-watered grass, **not** species-specific urban-tree irrigation demand. |
| [53] | EA Rainfall API, near-real-time 15-minute rain-gauge totals, OGL | **Medium optional**: nearby observations and recent storms; geography, availability and short recent API history vary. |
| [54] | ISRIC SoilGrids, 250 m predicted texture/organic carbon/soil properties, CC BY 4.0 | **Medium optional**: broad soil suitability proxy; coarse estimates cannot certify soil volume, permeability or water storage at a planting pit. REST API noted as temporarily paused; alternative access exists. |
| [55] | UKCEH modelled daily soil moisture and soil temperature, 1 km, 1965–2018 | **Medium optional**: historical soil wetness/seasonality; modelled and not current field moisture. Confirm dataset-specific reuse terms. |
| [56] | EA Flood Monitoring API, river stages/flows/flood alerts, OGL | **Medium optional**: nearby observed river context; not river-water availability for irrigation or a prediction of a specific flood. |
| [57] | UK Water Resources Portal, UKCEH rainfall/drought/river-flow/soil-moisture explorer | **Medium/low**: drought/context research; verify underlying data source permissions and export before product embedding. |
| [58] | EA WFD River Water Body Catchments Cycle 3 Classification 2022 | **Medium/low**: drainage-catchment context and water status; too broad to estimate park-scale watering or flood reduction. |
| [59] | University of Sheffield SuDS Research Group open research datasets (green roofs, bioretention, ET) | **Research only**: potential validation/parameter-study evidence for *future* green infrastructure/hydrology modules; roof/bioretention experiments are not validated tree hydrology. |
| [60] | EA Help for Water Rights Trading / Abstraction licences | **Low / restricted**: licensed water-source administration, not real park irrigation. **Special restrictions** limit use of location data; do not import/share by assuming all map layers are OGL. |
| [61] | EA Catchment Abstraction Management Strategy Assessment Points, OGL | **Low**: regional water resource availability context, not a park watering supply. |
| [62] | EA WFD Surface Water Management Catchments Cycle 4, 2026–2029 | **Low/medium**: most recent catchment geography for basin-level context, not microdrainage. |

**Research interpretation of supplied links:** TreePlanter [1] and Schrodi et al. [31] are relevant *optimisation/thermal* prior art; TreePlotter [28] and Autodesk Forma [32] are product/workflow comparators; ShadeMap [30] is a shadow-visualisation comparator (no dataset/API rights established); Tree Equity Score [29] can inform prioritisation and has a public data-download option, but exact exported layers/rights must be audited; OS Open Zoomstack [33] is a free contextual basemap, not an emissions, watering or flood model.

**Recommended scoped progression:** keep B01/B02/B04/B05 and the LiDAR B03 site audit as planned. For the first real Sheffield SiteBundle, optionally overlay a small OGL city drainage/EA flood layer and DfT traffic points **as attributed contextual evidence**, not as new objective terms. Design any CO2, irrigation, runoff, interception, stormwater or tree carbon-benefit calculation as a separately reviewed and benchmarked requirement with units, calibrated inputs and V03/V07-style acceptance tests. No verified street-scale CO2 monitoring or a public Sheffield park-specific tree irrigation-volume dataset was established in this search. No record proves construction-ready planting, flooding averted, air pollution removed, or CO2 offset by planting.

Sources:

[1] [TreePlanter paper, SOLWEIG-based tree-location optimisation and algorithm comparison](https://gmd.copernicus.org/articles/15/1107/2022)

[2] [Official DGX Spark hardware, including Arm CPU and Blackwell RT cores](https://docs.nvidia.com/dgx/dgx-spark/hardware.html)

[3] [Inspected NeMo-Ray model/tool/observation loop, pinned source revision](https://github.com/Harrishayy/NeMo-Ray/blob/6b3dfdc06ffe9b846eca864fb87257151ed0f337/agent/nemoray_modelling/agent.py)

[4] [Official Nemotron on Spark overview](https://build.nvidia.com/spark/nemotron/overview)

[5] [NVIDIA Spark Nemotron playbook source](https://github.com/NVIDIA/dgx-spark-playbooks/tree/main/nvidia/nemotron)

[6] [Official Sheffield event](https://events.nvidia.com/Hack-for-Impact-Sheffield)

[7] [pvlib solar-position inputs and timezone requirement](https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.solarposition.get_solarposition.html)

[8] [Warp mesh-ray query API](https://nvidia.github.io/warp/stable/language_reference/_generated/warp.mesh_query_ray.html)

[9] [Warp project and supported execution overview](https://github.com/NVIDIA/warp)

[10] [Warp installation, architecture/platform and Spark guidance](https://nvidia.github.io/warp/stable/user_guide/installation.html)

[11] [Warp FAQ and limitations](https://nvidia.github.io/warp/stable/user_guide/faq.html)

[12] [Community Forestry Trees official item metadata](https://www.arcgis.com/sharing/rest/content/items/47dbf190bd254de8aea2008e6aedbbd2?f=json)

[13] [Street Trees official item metadata](https://www.arcgis.com/sharing/rest/content/items/162d40a383fa48cbadc101ef18829bec?f=json)

[14] [Historical tree-planting areas official metadata](https://www.arcgis.com/sharing/rest/content/items/34dcbf28a00c4fb498caaffbfb26793e?f=json)

[15] [Parks & Countryside Sites official metadata](https://www.arcgis.com/sharing/rest/content/items/9a75a5cfb5ce4386b09651bd61d9255b?f=json)

[16] [School Localities official metadata](https://www.arcgis.com/sharing/rest/content/items/7b2df397e9994ca5984bad0b679ce6d9?f=json)

[17] [Parks & Countryside Sites layer](https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/INSPIRE/FeatureServer/12)

[18] [INSPIRE End User Licence, including use/redistribution restriction](https://www.ordnancesurvey.co.uk/documents/licensing/inspire-end-user-licence.pdf)

[19] [Official GitHub MCP server and configured tool access](https://github.com/github/github-mcp-server)

[20] [GitHub pull-request workflow documentation](https://docs.github.com/en/pull-requests)

[21] [GitHub Projects practices: small issues and one source of truth](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/best-practices-for-projects)

[22] [GitHub branch-protection behaviour and settings](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)

[23] [UCL report identifying NeMo-Ray as a previous NVIDIA Hack for Impact winner](https://www.ucl.ac.uk/engineering/news/2026/sep/ucl-computer-science-students-recognised-national-and-international-competitions)

[24] [Defra Survey Data Download application](https://environment.data.gov.uk/survey)

[25] [Environment Agency LiDAR Composite DSM 1 m metadata](https://environment.data.gov.uk/dataset/9ba4d5ac-d596-445a-9056-dae3ddec0178)

[26] [Environment Agency LiDAR Composite DTM 1 m metadata](https://environment.data.gov.uk/dataset/13787b9a-26a4-4775-8523-806d13af58fc)

[27] [Official Defra FAQ: downloading survey data, tile sizes and formats](https://environment.data.gov.uk/support/faqs/275808874/275809211)

[28] [PlanIT Geo TreePlotter Projects](https://planitgeo.com/library/treeplotter-projects/)

[29] [UK Tree Equity Score](https://uk.treeequityscore.org/)

[30] [ShadeMap interactive shadow map](https://shademap.app/@47.608,-122.339,6z,1794418525924t,0b,0p,0m)

[31] [arXiv preprint 2310.05691 (PDF)](https://arxiv.org/pdf/2310.05691)

[32] [Autodesk Forma: site-design tools overview (28 August 2026)](https://blogs.autodesk.com/forma/2026/08/28/forma-site-design-tools-overview/)

[33] [Ordnance Survey OS Open Zoomstack](https://www.ordnancesurvey.co.uk/products/os-open-zoomstack)

[34] [DESNZ local authority GHG emissions, 2005–2024](https://www.gov.uk/government/statistics/uk-local-authority-and-regional-greenhouse-gas-emissions-statistics-2005-to-2024)

[35] [DfT road traffic statistics: Sheffield](https://roadtraffic.dft.gov.uk/local-authorities/E08000019)

[36] [NAEI 1 km gridded emissions data](https://naei.energysecurity.gov.uk/data/maps/download-gridded-emissions)

[37] [NAEI major road emissions, 2024](https://naei.energysecurity.gov.uk/data/maps/major-road-emissions)

[38] [EA Flood Map for Planning, Flood Zones 2/3](https://environment.data.gov.uk/dataset/04532375-a198-476e-985e-0579a0a11b47)

[39] [EA Risk of Flooding from Surface Water](https://environment.data.gov.uk/dataset/b5aaa28d-6eb9-460e-8d6f-43caa71fbe0e)

[40] [EA surface-water planning extents, present-day](https://www.data.gov.uk/dataset/dfd734fb-cc68-4229-b60d-8c0280398052/flood-map-for-planning-surface-water-spatial-planning-extents-present-day)

[41] [EA Recorded Flood Outlines](https://environment.data.gov.uk/dataset/8c75e700-d465-11e4-8b5b-f0def148f590)

[42] [Sheffield 2023 Strategic Flood Risk Assessment](https://www.sheffield.gov.uk/public-health/flooding/strategic-flood-risk-assessment)

[43] [EA Flood Zones plus Climate Change](https://www.data.gov.uk/dataset/77931470-ee6b-4f8e-8868-82842aed2e5d/flood-map-for-planning-flood-zones-plus-climate-change)

[44] [Sheffield SuDS Regions](https://www.data.gov.uk/dataset/7ebd8e69-ceae-41c0-ab79-163adef6b423/sustainable-drainage-system-regions)

[45] [Sheffield SuDS Links](https://www.data.gov.uk/dataset/4919b577-d07b-409d-81e0-ce8b61c99f4b/sustainable-drainage-system-links)

[46] [Sheffield Highway Drain Links](https://www.data.gov.uk/dataset/15cfbc81-cd13-4e9f-899d-fc137781290d/highway-drain-links)

[47] [Sheffield Open Watercourse Links](https://www.data.gov.uk/dataset/32a6f3aa-9ca5-4042-8201-8d2f9425e673/open-watercourse-links)

[48] [Sheffield Watercourse Culvert Links](https://www.data.gov.uk/dataset/8a001e4c-50eb-4730-a258-04c58d8de28a/watercourse-culvert-links)

[49] [Sheffield Section 21 Asset Register Links/Nodes](https://www.data.gov.uk/dataset/ad0c1c23-0ea6-4bc5-a7b6-788c78346b04/section-21-asset-register-links-and-nodes)

[50] [OS Open Rivers](https://www.ordnancesurvey.co.uk/products/os-open-rivers)

[51] [Met Office HadUK-Grid datasets, rainfall](https://www.metoffice.gov.uk/research/climate/maps-and-data/data/haduk-grid/datasets)

[52] [EA Potential Evapotranspiration dataset](https://www.data.gov.uk/dataset/7b58506c-620d-433c-afce-d5d93ef7e01e/environment-agency-potential-evapotranspiration-dataset)

[53] [EA Rainfall API](https://environment.data.gov.uk/flood-monitoring/doc/rainfall)

[54] [ISRIC SoilGrids global soil predictions](https://isric.org/explore/soilgrids/)

[55] [UKCEH 1 km daily modelled soil moisture, 1965–2018](https://www.data.gov.uk/dataset/361f67ed-c9f4-4e75-a41b-0f1a2beae712/modelled-daily-soil-moisture-and-soil-temperature-at-1km-resolution-across-the-uk-mai-1965-2018)

[56] [EA flood-monitoring river level/flow API](https://environment.data.gov.uk/flood-monitoring/doc/reference)

[57] [UK Water Resources Portal](https://ukwrp.ceh.ac.uk/about/)

[58] [EA WFD Cycle 3 River Water Body Catchments 2022](https://environment.data.gov.uk/dataset/cd84a955-fd0a-4f5d-9bcb-b869c8906f9e)

[59] [University of Sheffield SuDS research datasets](https://sudsresearchgroup.sites.sheffield.ac.uk/publications)

[60] [EA Help for Water Rights Trading data (restricted)](https://www.data.gov.uk/dataset/ca3eae98-1b84-444c-820b-d33dd8c1dfa8/help-for-water-rights-trading-data-england)

[61] [EA Catchment Abstraction Management Strategy Assessment Points](https://environment.data.gov.uk/dataset/394cde56-5cf9-42bf-8d20-86c182f9ce68)

[62] [EA WFD Surface Water Management Catchments Cycle 4](https://environment.data.gov.uk/dataset/2ccc5b58-685d-433e-a613-2d91166a0526)
