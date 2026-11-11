# Sources and evidence boundaries

These sources were inspected during the preceding research preparation, not freshly re-audited by writing these development docs. Links support source facts, not compatibility, performance, originality or completed-product claims. Verify relevant current versions/licences again during implementation.

**User-reported precedent:** on 11 November 2026, Ben reported that the previous team developed a week before its hackathon and stated the intention to document then develop before this event. That timing was not independently verified here. UCL confirms a prior winning project [23], not current advance-code permission. The official event page [6] and organiser clarification, not precedent, govern eligibility.

**Known source limitations:** planting-area records are historical, School Localities are not grounds/buildings, tree points lack full crown dimensions, and some park/street-tree sources link restrictive INSPIRE terms. Downloadability is not a blanket reuse licence. No restricted raw assets are included in this documentation pack.

The working stack is a proposal. NVIDIA hardware capabilities and Warp/platform documentation do not prove this application's runtime, RT-core use or acceleration. TreePlanter is relevant prior art; our intended agent value still needs the same-tools comparison in VALIDATION.

## Research papers: direct full-text or publisher article links

**Start here for scientific literature.** These are published research articles, systematic reviews and one clearly marked arXiv preprint, **not dataset metadata, ArcGIS records or product landing pages**. The links go to the paper's publisher article, DOI landing page, open full text or PDF. Some journals may restrict full-text access. Relevance is judged against [SPEC](SPEC.md) and [NUMERICS](NUMERICS.md), not a hypothetical completed carbon/water model.

The two studies already present in the source index are **[1] [Wallenberg et al. (2022), TreePlanter](https://gmd.copernicus.org/articles/15/1107/2022/)** (peer-reviewed, open full article) and **[31] [Schrodi et al. (2023), Climate-sensitive Urban Planning through Optimization of Tree Placements](https://arxiv.org/pdf/2310.05691)** (arXiv **preprint**, not independently verified here as journal peer reviewed). Both are **High** relevance for search/model comparison. [1] uses radiant-temperature reduction rather than this project's initial direct-shade units.

### Direct shade, 3D geometry and tree placement

| Paper (direct article link) | Application to the Sheffield Tree Planner | Relevance | Access |
| --- | --- | --- | --- |
| **[1] [Wallenberg et al. (2022), TreePlanter](https://gmd.copernicus.org/articles/15/1107/2022/)** | Benchmark greedy vs hill-climbing and multi-tree shadow overlap, without mislabelling radiant-temperature benefits as direct shade | **High** | Open full article |
| **[31] [Schrodi et al. (2023), Climate-sensitive Urban Planning](https://arxiv.org/pdf/2310.05691)** | Compare local-search strategy and surrogate thermal modelling only as a separate approach | **High** | Open arXiv preprint PDF |
| **[63] [Tree shade coverage optimization in an urban residential environment](https://doi.org/10.1016/j.buildenv.2017.01.036)** | Design 3D façade/ground shade placement and test budget-aware spatial optimisation against existing baseline; unlike this project's ground target, paper also evaluates façades and roofs | **High** | Publisher article; open accepted manuscript available via University of Glasgow |
| **[64] [Optimal representation of tree foliage for local urban climate modeling](https://doi.org/10.1016/j.scs.2024.105857)** | Compare ellipsoid/other crown representations against measured 3D foliage and shadow extents before claiming physical accuracy | **High** | Open-access journal article |
| **[65] [Strategic tree placement for urban cooling: A novel optimisation approach for desired microclimate outcomes](https://doi.org/10.1016/j.uclim.2024.102084)** | Consider multi-objective optimisation alternatives and controlled benchmark comparisons only after shared objective and constraints are defined | **Medium** | Open-access journal article |
| **[66] [Towards climate-responsible tree positioning: Detailed effects of trees on heat exposure in complex urban environments](https://doi.org/10.1016/j.ufug.2024.128500)** | Check placement sensitivity to existing buildings, time of day and sun exposure, particularly missing context and scenario comparison | **High** | Publisher article; full-text access may vary |

### Urban stormwater, flood mitigation and tree hydrology

| Paper (direct article link) | Application to the Sheffield Tree Planner | Relevance | Access |
| --- | --- | --- | --- |
| **[67] [Towards optimized runoff reduction by urban tree cover: A review of key physical tree traits, site conditions, and management strategies](https://doi.org/10.1016/j.landurbplan.2023.104849)** | Define which crown and soil properties a future stormwater-interception or infiltration module would actually need | **Medium** | Open-access review |
| **[68] [A comparative analysis of urban forests for storm-water management](https://www.nature.com/articles/s41598-023-28629-6)** | Review interception, transpiration and infiltration mechanisms and sensitivity to species; avoid copying aggregate outcomes to one Sheffield planting site | **Medium** | Open-access full article |
| **[69] [Quantifying the stormwater runoff volume reduction benefits of urban street tree canopy](https://doi.org/10.1016/j.scitotenv.2021.151296)** | Use measured catchment runoff outcomes to plan a future model validation, including the distinction between total runoff and peak discharge | **Medium** | Publisher article; full text may require access |
| **[70] [How robust is the evidence for beneficial hydrological effects of urban tree planting?](https://doi.org/10.1080/02626667.2021.1922692)** | Set standards for future hydrology claims and controls, highlighting weak field validation and uncertain scaling from individual trees to catchments | **High** | Journal article with full-text publisher link |
| **[78] [Benefits of an urban isolated tree combined with ground covers for stormwater management through interception–infiltration–runoff processes](https://doi.org/10.1016/j.ufug.2026.129366)** | Consider coupled canopy/ground-cover modelling and how an isolated tree interacts with permeable ground in a possible later SWMM-style feature | **Low** | Open-access journal article |
| **[79] [Rainfall interception by urban trees: Event characteristics and tree morphological traits](https://doi.org/10.1002/hyp.15146)** | Study event-specific interception and crown morphology relationships for later stormwater parameterisation and seasonal cases | **Medium** | Open-access research article |

### Irrigation, drought and water balance

| Paper (direct article link) | Application to the Sheffield Tree Planner | Relevance | Access |
| --- | --- | --- | --- |
| **[71] [Supporting Growth and Transpiration of Newly Planted Street Trees With Passive Irrigation Systems](https://doi.org/10.1029/2020WR029526)** | Inform future design of rain-fed passive irrigation and tree establishment cases, with explicit limits on transfer of field results across climates | **Medium** | Free full-text research article |
| **[72] [Urban tree drought stress: Sap flow measurements, model validation, and water management simulations](https://doi.org/10.1016/j.scitotenv.2024.177221)** | Use measured sap flow and soil moisture to identify parameters and failure cases for future drought/watering scenarios | **Medium** | Open-access journal article |
| **[73] [Ecohydrology of street trees: design and irrigation requirements for sustainable water use](https://doi.org/10.1002/eco.1369)** | Use its soil–tree water-balance formulation as a future research starting point; do not equate rainfall or reference grass PET with tree-specific watering volumes | **Medium** | Publisher article; access may require subscription |

### Traffic, air quality and carbon accounting

| Paper (direct article link) | Application to the Sheffield Tree Planner | Relevance | Access |
| --- | --- | --- | --- |
| **[74] [Air pollution abatement performances of green infrastructure in open road and built-up street canyon environments – A review](https://doi.org/10.1016/j.atmosenv.2017.05.014)** | Review why roadside trees sometimes reduce or increase local pollutant exposure depending on geometry and ventilation; avoid CO2-versus-NO2/PM confusion | **Medium** | Open-access review |
| **[75] [Air pollution removal by urban forests in Canada and its effect on air quality and human health](https://doi.org/10.1016/j.ufug.2017.10.019)** | Examine pollutant-removal modelling and evidence needs if a future pollution module is proposed; cannot estimate vehicle CO2 removal from these results | **Low** | Research paper; open USDA hosted paper also available |
| **[76] [Carbon storage and sequestration by trees in urban and community areas of the United States](https://doi.org/10.1016/j.envpol.2013.03.019)** | Understand measurement, biomass assumptions and distinction between carbon stock and annual sequestration before any CO2-offset comparison | **Medium** | Journal article; free USFS paper available |

### Public-health motivation (not a current output)

| Paper (direct article link) | Application to the Sheffield Tree Planner | Relevance | Access |
| --- | --- | --- | --- |
| **[77] [The potential of urban trees to reduce heat-related mortality in London](https://pmc.ncbi.nlm.nih.gov/articles/PMC11009716/)** | Explain UK heat-health motivation and potential future evaluation targets, but not translate current m2·h shade into prevented deaths | **Low** | Open-access full article |

**Paper/source distinction:** data.gov.uk, the Environment Agency, council feature services, DfT, Met Office and similar pages below remain important **dataset acquisition and provenance records**, but are not academic papers and do not themselves justify physical carbon, rainfall or flood benefits. Spark/API/GitHub documentation and competitor product galleries are **engineering or UX references**, not research evidence. Avoid treating a publisher paper's modelled impacts as measured Sheffield outcomes.

---

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

## Complete source-by-source application and relevance register

This table covers **every numbered link [1]–[79]**, including research papers, datasets, official technical documentation, licence terms, products and project-workflow references. Every HTTPS link elsewhere in this file resolves to one of those numbered sources; it does not create an unassessed extra source. **Relevance is assessed against the currently documented product** (site-specific direct-sun shade analysis, credible tree placement, inspectable evidence and the local-agent/Spark demonstration), not an invented carbon, irrigation or flood-reduction model.

- **Core**: necessary to a required calculation, data-rights gate, or event/compliance requirement, where applicable
- **High**: directly informs planned delivery, real-site validity, search quality or required local runtime
- **Medium**: credible optional map/site context, supporting engineering reference, or design precedent
- **Low**: largely historical, indirect or only useful if a separately validated future feature is approved

These are **project-fit judgements, not verified ingestion status or a ranking of dataset quality**. Conditional references still require appropriate licences, available data, real-site checks and V03 validation. References that support similar purposes are not automatically interchangeable. References cited through the same URL in the narrative or source list inherit the matching entry below.

| Ref / source | Concrete application to this project | Relevance and reason |
| --- | --- | --- |
| **[1] TreePlanter paper** | Use its greedy and hill-climbing placement methods as scientific comparators for the deterministic reference and search; examine joint shading, crown sizes and seasonal cases, without equating its radiant-temperature objective to our direct-shade metric. | **High**: directly informs B06 search design, scientific comparison and limitations |
| **[2] DGX Spark hardware** | Plan device-memory, CPU/GPU and potential RT-core experiments; record what actually ran instead of inferring acceleration from specifications. | **High**: supports R09/B09 device-proof work, not an achieved benchmark |
| **[3] NeMo-Ray agent source** | Study the implemented model–tool–observation loop and trace design as an agent integration reference; adapt only compatible ideas to the registered domain dispatcher. | **High**: direct design comparator for B09/B10, not reusable project data |
| **[4] Nemotron on Spark** | Evaluate a local model/serving candidate for interpreting briefs, selecting approved tools and explaining result-backed observations. | **High, conditional**: B09 local-model candidate requiring compatibility tests |
| **[5] NVIDIA Nemotron Spark playbook** | Guide reproducible inference setup and model/tool-call smoke tests if this serving approach is chosen. | **Medium**: implementation aid conditional on selected model/runtime |
| **[6] Official Sheffield hackathon page** | Check event eligibility, Spark/model obligations, dates, prior-code/AI rules, entry format and permitted demonstration materials. | **Core**: participation and release gate D07; confirm actual current rules |
| **[7] pvlib solar position documentation** | Implement/test sun azimuth and elevation from geolocation plus timezone-aware timestamps, then verify against independent references. | **Core**: R02/B02 solar computation input |
| **[8] NVIDIA Warp mesh-ray API** | Investigate an optional GPU ray-query implementation for static obstruction meshes against the CPU reference. | **Medium**: optional acceleration; correctness first |
| **[9] NVIDIA Warp project** | Assess Warp APIs and execution model for an optional ray-tracing kernel; do not require it for the MVP. | **Medium**: conditional performance engineering |
| **[10] Warp installation/platform guide** | Check version, architecture and device compatibility on actual laptop/Spark before relying on GPU ray tracing. | **Medium**: conditional deployment feasibility and reproducibility |
| **[11] Warp FAQ and limitations** | Anticipate kernel/platform limitations and fallback conditions; maintain validated CPU behaviour. | **Medium**: conditional risk and fallback reference |
| **[12] Community Forestry Trees metadata** | Identify candidate existing-tree records/species/locations for a Sheffield site and compare them with imagery/field evidence; do not infer crown dimensions or survival. | **High**: site semantics for B03, subject to coverage and rights |
| **[13] Street Trees metadata** | Locate possible street-tree obstructions and candidate context; independently verify position, size and INSPIRE-linked reuse limitations. | **High, conditional**: B03 tree context with rights/accuracy gate |
| **[14] Historical planting areas metadata** | Provide historical planting-activity context and possible site leads, never automatic future plantability or permission. | **Low**: research background, not an eligible-planting mask |
| **[15] Parks and Countryside Sites metadata** | Find candidate parks and provisional boundary polygons for site selection; establish layer rights before display/export. | **High, conditional**: B03 site leads but INSPIRE restrictions |
| **[16] School Localities metadata** | Use only to identify administrative locality names or further research leads; it is not a map of school grounds/buildings. | **Low**: avoids an incorrect site-selection assumption |
| **[17] Council parks FeatureServer layer** | Test whether the mapped park boundaries can delimit a pilot site after rights, currentness and geometry checks. | **High, conditional**: convenient B03 input, no unapproved redistribution |
| **[18] INSPIRE End User Licence** | Determine whether relevant council/OS-derived layers may be used, team-shared, publicly displayed or exported; reject prohibited actions. | **Core where applicable**: a legal/source-readiness gate under R01/R08 |
| **[19] GitHub MCP server** | Understand the repository-connector workflow for scoped file reads/updates and constrained collaboration. | **Medium**: development tooling rather than simulation data |
| **[20] GitHub pull-request documentation** | Use scoped draft PRs, reviews and safe integration of physics, UI and agent changes. | **Medium**: collaboration and integration quality |
| **[21] GitHub Projects guidance** | Consider small dependency-ready tasks and one source of truth if the team adopts a task board; do not duplicate BUILD. | **Low**: optional team organisation aid |
| **[22] GitHub branch protection guidance** | Evaluate review/merge restrictions if the team later configures shared branch governance. | **Low**: repository administration, not product functionality |
| **[23] UCL previous winner report** | Understand hackathon precedent and possible presentation style; do not infer current eligibility or required technical features. | **Low**: historical context only |
| **[24] Defra survey download** | Select/download bounded Sheffield LiDAR tiles for an auditable local site-bundle pilot. | **High**: practical B03 acquisition route |
| **[25] EA 1 m LiDAR DSM** | Model approximate roofs, tree crowns and other surface obstructions after classifying, cropping and validating raw elevations. | **High**: candidate static scene geometry; not semantic by itself |
| **[26] EA 1 m LiDAR DTM** | Build ground terrain, surface sample heights and height-above-ground comparisons with co-registered DSM. | **High**: candidate terrain foundation for B03/B08 |
| **[27] Defra survey download FAQ** | Use area-of-interest/tile/product/resolution instructions to perform reproducible source retrieval. | **Medium**: practical download support |
| **[28] TreePlotter project gallery** | Review visualisation, inventory and tree-management workflows when designing project comparison and provenance panels. | **Medium**: product/UX inspiration, not an open data feed |
| **[29] Tree Equity Score UK** | Compare neighbourhood canopy gaps and equity indicators when prioritising Sheffield demonstration sites; evaluate downloadable LSOA-scale data separately. | **Medium**: useful prioritisation context, not a per-tree shade metric or planting permission |
| **[30] ShadeMap** | Compare intuitive sun/shadow controls and time-slider interaction with the planned UI; do not treat service visuals as solver geometry. | **Medium**: UI comparator only |
| **[31] Schrodi et al. tree-placement optimisation** | Review learned radiant-temperature surrogates and iterated local search as prior art; benchmark only under equivalent inputs and keep radiant comfort distinct from direct-beam shade. | **High for research comparison; future surrogate modelling is outside current validation** |
| **[32] Autodesk Forma site-design tools** | Review site exploration, alternatives and trade-off presentation patterns; no assumed export of proprietary simulations. | **Medium**: UX/workflow comparator |
| **[33] OS Open Zoomstack** | Supply a rights-checked map baselayer for roads, green space and context behind the 3D site view. | **Medium**: helpful display layer, not measurement-grade 3D terrain |
| **[34] DESNZ local-authority greenhouse gases** | Show historical Sheffield road-transport CO2/CO2e totals as city context or future emissions module validation baseline. | **Low in current shade scope; no roadside or tree-offset estimate** |
| **[35] DfT Sheffield road traffic** | Overlay traffic-count points and vehicle classes to contextualise busy roads when discussing sites or exposure; do not derive CO2 without a separate model. | **Medium**: optional local prioritisation overlay |
| **[36] NAEI gridded emissions** | Investigate sector/pollutant gridded inventory for coarse transport/emissions context; verify CO2 coverage/year before importing. | **Low**: later emissions analysis, coarse relative to park |
| **[37] NAEI major-road emissions** | Assess a road-link emissions inventory if downloadable and relevant pollutants/CO2 fields and geometries exist. | **Low, conditional**: later road-emissions context; file not yet checked |
| **[38] EA planning Flood Zones** | Overlay mapped river/sea floodplain zones to flag site risk and prompt survey/authority review; not a tree-flood-benefit model. | **Medium**: useful optional site-risk context |
| **[39] EA surface-water flood risk** | Overlay likelihood/depth information for rain-driven surface flooding near a park; label model assumptions and resolution. | **Medium**: useful optional planning context |
| **[40] EA surface-water planning extents/depths** | Use likelihood/depth-band scenario layers to inform flood-risk warnings, not estimate planting-caused reduction. | **Medium**: optional risk overlay |
| **[41] Recorded Flood Outlines** | Compare historical recorded flood events with proposed site; absence of an outline cannot be treated as safety evidence. | **Low–Medium**: corroborating history, not exhaustive |
| **[42] Sheffield Strategic Flood Risk Assessment** | Provide Sheffield-specific planning interpretation and references for flood-risk decisions; check currency against newer EA maps. | **Medium**: supplementary local planning reference |
| **[43] EA Flood Zones plus Climate Change** | Show potential future floodplain exposure for long-horizon site context, without attributing changes to proposed trees. | **Low–Medium**: later resilience scenario context |
| **[44] Sheffield SuDS Regions** | Overlay mapped sustainable-drainage system regions and identify possible compatibility or evidence gaps. | **Medium**: actionable site context, not permission/benefit proof |
| **[45] Sheffield SuDS Links** | Overlay mapped drainage links to inform potential planting conflicts and site observations. | **Medium**: contextual site-screening layer |
| **[46] Sheffield Highway Drain Links** | Flag possible conflicts near road drainage and roots/planting locations; require on-site utility checks. | **Medium–High**: site-screening evidence, not excavation clearance |
| **[47] Sheffield Open Watercourse Links** | Show stream corridors and riparian context, guiding preliminary location/exclusion review. | **Medium**: optional physical site context |
| **[48] Sheffield Watercourse Culvert Links** | Flag mapped culverts and potential root-clearance constraints; do not assume positions are surveyed. | **Medium–High**: site-screening evidence |
| **[49] Sheffield Section 21 flood-asset register** | Check mapped flood/drainage assets for provisional planting conflicts or opportunities for site inspection. | **Medium–High**: site-screening evidence, incomplete asset coverage |
| **[50] OS Open Rivers** | Use vector rivers and channels as an OGL geographic context layer, especially if more specific council data is restricted. | **Medium**: alternate contextual basemap |
| **[51] Met Office HadUK-Grid rainfall** | Provide historical rainfall/dry-season context and potential future climate inputs for an irrigation/moisture model. | **Low in current scope; useful future water-demand input** |
| **[52] EA potential evapotranspiration** | Inform a later water-balance and atmospheric evaporative-demand model; grass-reference PET is not tree irrigation volume. | **Low in current scope; useful future modelling input** |
| **[53] EA rainfall API** | Plot recent local rain-gauge observations alongside the study site for explanatory context and future validation. | **Low–Medium**: optional recent weather overlay |
| **[54] ISRIC SoilGrids** | Provide coarse soil-texture/properties context for candidate evaluation and a list of survey uncertainties, not pit-scale certainty. | **Medium**: preliminary site uncertainty input only |
| **[55] UKCEH modelled soil moisture** | Explore past drought and moisture patterns for a future tree-establishment model; not field measurement. | **Low**: future seasonal context |
| **[56] EA flood-monitoring API** | Display nearby river stage/flow observations and alerts separately from flood risk models and planning constraints. | **Low**: optional live context, not core |
| **[57] UK Water Resources Portal** | Research drought, rainfall and flow context for Sheffield; verify datasets and export rights for any reuse. | **Low**: supplementary future hydrology context |
| **[58] WFD Cycle 3 river catchments** | Identify larger drainage catchments and ecological status context; too coarse for tree-scale hydrology. | **Low**: broader geographic context |
| **[59] Sheffield SuDS research datasets** | Use experimental bioretention/green-roof evidence to inform a future hydrology validation plan; do not transfer parameters to trees without tests. | **Low**: future research comparator |
| **[60] Water rights trading/abstraction data** | Investigate permitted water abstraction only if a future irrigation-supply feature explicitly needs it; obey special location/use restrictions. | **Low**: out of initial scope, restricted |
| **[61] EA abstraction assessment points** | Identify catchment-level water-resource pressure for future planning, not park irrigation supply. | **Low**: indirect catchment context |
| **[62] WFD Cycle 4 management catchments** | Map current management catchment geography for optional long-term water strategy/context, not park runoff predictions. | **Low**: broad future context |
| **[63] Tree shade coverage optimization in an urban residential environment** | Design 3D façade/ground shade placement and test budget-aware spatial optimisation against existing baseline; unlike this project's ground target, paper also evaluates façades and roofs | **High**: Direct quantitative shade-optimisation precedent |
| **[64] Optimal representation of tree foliage for local urban climate modeling** | Compare ellipsoid/other crown representations against measured 3D foliage and shadow extents before claiming physical accuracy | **High**: Direct check on simplified crown geometry |
| **[65] Strategic tree placement for urban cooling: A novel optimisation approach for desired microclimate outcomes** | Consider multi-objective optimisation alternatives and controlled benchmark comparisons only after shared objective and constraints are defined | **Medium**: Algorithmic comparator but models more than direct solar shade |
| **[66] Towards climate-responsible tree positioning: Detailed effects of trees on heat exposure in complex urban environments** | Check placement sensitivity to existing buildings, time of day and sun exposure, particularly missing context and scenario comparison | **High**: Directly justifies real-building shadow context |
| **[67] Towards optimized runoff reduction by urban tree cover: A review of key physical tree traits, site conditions, and management strategies** | Define which crown and soil properties a future stormwater-interception or infiltration module would actually need | **Medium**: Direct evidence framework for a separately validated hydrology feature |
| **[68] A comparative analysis of urban forests for storm-water management** | Review interception, transpiration and infiltration mechanisms and sensitivity to species; avoid copying aggregate outcomes to one Sheffield planting site | **Medium**: Hydrology evidence synthesis, not a tree-by-tree simulator |
| **[69] Quantifying the stormwater runoff volume reduction benefits of urban street tree canopy** | Use measured catchment runoff outcomes to plan a future model validation, including the distinction between total runoff and peak discharge | **Medium**: Field evidence for future runoff model validation |
| **[70] How robust is the evidence for beneficial hydrological effects of urban tree planting?** | Set standards for future hydrology claims and controls, highlighting weak field validation and uncertain scaling from individual trees to catchments | **High**: Critical review helps prevent unjustified flood-reduction claims |
| **[71] Supporting Growth and Transpiration of Newly Planted Street Trees With Passive Irrigation Systems** | Inform future design of rain-fed passive irrigation and tree establishment cases, with explicit limits on transfer of field results across climates | **Medium**: Experimental water-use/establishment data; outside current objective |
| **[72] Urban tree drought stress: Sap flow measurements, model validation, and water management simulations** | Use measured sap flow and soil moisture to identify parameters and failure cases for future drought/watering scenarios | **Medium**: Direct study of tree water balance, but site- and species-dependent |
| **[73] Ecohydrology of street trees: design and irrigation requirements for sustainable water use** | Use its soil–tree water-balance formulation as a future research starting point; do not equate rainfall or reference grass PET with tree-specific watering volumes | **Medium**: Direct irrigation model precedent requiring new calibration and tests |
| **[74] Air pollution abatement performances of green infrastructure in open road and built-up street canyon environments – A review** | Review why roadside trees sometimes reduce or increase local pollutant exposure depending on geometry and ventilation; avoid CO2-versus-NO2/PM confusion | **Medium**: Useful constraints for future traffic air-quality modelling |
| **[75] Air pollution removal by urban forests in Canada and its effect on air quality and human health** | Examine pollutant-removal modelling and evidence needs if a future pollution module is proposed; cannot estimate vehicle CO2 removal from these results | **Low**: Broader urban forest impact, unrelated to core direct shade |
| **[76] Carbon storage and sequestration by trees in urban and community areas of the United States** | Understand measurement, biomass assumptions and distinction between carbon stock and annual sequestration before any CO2-offset comparison | **Medium**: Methodological reference only; US per-area factors are not Sheffield estimates |
| **[77] The potential of urban trees to reduce heat-related mortality in London** | Explain UK heat-health motivation and potential future evaluation targets, but not translate current m2·h shade into prevented deaths | **Low**: UK impacts context; health modelling outside current scope |
| **[78] Benefits of an urban isolated tree combined with ground covers for stormwater management through interception–infiltration–runoff processes** | Consider coupled canopy/ground-cover modelling and how an isolated tree interacts with permeable ground in a possible later SWMM-style feature | **Low**: Optional future hydrology; Tokyo findings not Sheffield outputs |
| **[79] Rainfall interception by urban trees: Event characteristics and tree morphological traits** | Study event-specific interception and crown morphology relationships for later stormwater parameterisation and seasonal cases | **Medium**: Measured rain-event evidence but not a validated Sheffield runoff model |

## Source index: papers, datasets, technical guidance, licensing and contextual links

**Numbers [1]–[62] are retained** to preserve cross-references elsewhere in the documentation. They include many **non-paper** entries, which are maintained for original dataset/rights/engineering provenance only. **[63]–[79] add actual research-paper links**; use the research-paper tables at the top for literature reading. Some links below may need a subscription to access full text. The project must not make new modelling claims based on a paper without implementing and validating the relevant physics.


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

[31] [Schrodi et al., Climate-sensitive Urban Planning through Optimization of Tree Placements (arXiv PDF)](https://arxiv.org/pdf/2310.05691)

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

[63] [Zhao, Wentz & Murray (2017): Tree shade coverage optimization in an urban residential environment](https://doi.org/10.1016/j.buildenv.2017.01.036)

[64] [Rodriguez et al. (2024): Optimal representation of tree foliage for local urban climate modeling](https://doi.org/10.1016/j.scs.2024.105857)

[65] [Shaamala et al. (2024): Strategic tree placement for urban cooling: A novel optimisation approach for desired microclimate outcomes](https://doi.org/10.1016/j.uclim.2024.102084)

[66] [Urban Forestry & Urban Greening study (2024): Towards climate-responsible tree positioning: Detailed effects of trees on heat exposure in complex urban environments](https://doi.org/10.1016/j.ufug.2024.128500)

[67] [Dowtin et al. (2023): Towards optimized runoff reduction by urban tree cover: A review of key physical tree traits, site conditions, and management strategies](https://doi.org/10.1016/j.landurbplan.2023.104849)

[68] [Rahman et al. (2023): A comparative analysis of urban forests for storm-water management](https://www.nature.com/articles/s41598-023-28629-6)

[69] [Selbig et al. (2022): Quantifying the stormwater runoff volume reduction benefits of urban street tree canopy](https://doi.org/10.1016/j.scitotenv.2021.151296)

[70] [Baker, Hutchins & Miller (2021): How robust is the evidence for beneficial hydrological effects of urban tree planting?](https://doi.org/10.1080/02626667.2021.1922692)

[71] [Thom et al. (2022): Supporting Growth and Transpiration of Newly Planted Street Trees With Passive Irrigation Systems](https://doi.org/10.1029/2020WR029526)

[72] [Tams, Paton & Kluge (2024): Urban tree drought stress: Sap flow measurements, model validation, and water management simulations](https://doi.org/10.1016/j.scitotenv.2024.177221)

[73] [Vico, Revelli & Porporato (2014): Ecohydrology of street trees: design and irrigation requirements for sustainable water use](https://doi.org/10.1002/eco.1369)

[74] [Abhijith et al. (2017): Air pollution abatement performances of green infrastructure in open road and built-up street canyon environments – A review](https://doi.org/10.1016/j.atmosenv.2017.05.014)

[75] [Nowak et al. (2018): Air pollution removal by urban forests in Canada and its effect on air quality and human health](https://doi.org/10.1016/j.ufug.2017.10.019)

[76] [Nowak, Greenfield, Hoehn & Lapoint (2013): Carbon storage and sequestration by trees in urban and community areas of the United States](https://doi.org/10.1016/j.envpol.2013.03.019)

[77] [Taylor et al. (2024): The potential of urban trees to reduce heat-related mortality in London](https://pmc.ncbi.nlm.nih.gov/articles/PMC11009716/)

[78] [Zhao & Asawa (2026): Benefits of an urban isolated tree combined with ground covers for stormwater management through interception–infiltration–runoff processes](https://doi.org/10.1016/j.ufug.2026.129366)

[79] [Hydrological Processes study (2024): Rainfall interception by urban trees: Event characteristics and tree morphological traits](https://doi.org/10.1002/hyp.15146)
