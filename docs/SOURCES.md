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
