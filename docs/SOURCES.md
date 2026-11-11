# Sources and evidence boundaries

These sources were inspected during the preceding research preparation, not freshly re-audited by writing these development docs. Links support source facts, not compatibility, performance, originality or completed-product claims. Verify relevant current versions/licences again during implementation.

**User-reported precedent:** on 11 November 2026, Ben reported that the previous team developed a week before its hackathon and stated the intention to document then develop before this event. That timing was not independently verified here. UCL confirms a prior winning project [23], not current advance-code permission. The official event page [6] and organiser clarification, not precedent, govern eligibility.

**Known source limitations:** planting-area records are historical, School Localities are not grounds/buildings, tree points lack full crown dimensions, and some park/street-tree sources link restrictive INSPIRE terms. Downloadability is not a blanket reuse licence. No restricted raw assets are included in this documentation pack.

The working stack is a proposal. NVIDIA hardware capabilities and Warp/platform documentation do not prove this application's runtime, RT-core use or acceleration. TreePlanter is relevant prior art; our intended agent value still needs the same-tools comparison in VALIDATION.

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
