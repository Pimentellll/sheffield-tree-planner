# Sheffield Tree Planner — comprehensive research and decision dossier

**Research cutoff:** 11 November 2026, inclusive.  
**Audience:** Ben, Arnav and Alex.  
**Status:** research synthesis and proposed amendments, not an implementation, site approval, validated environmental assessment or claim of competition novelty.  
**Release classification:** none — documentation only; no application version or executable release is changed.

This dossier combines the original [research handoff](RESEARCH_HANDOFF.md), the [agentic feature review](AGENTIC_FEATURE_REVIEW.md), the team's expanded target recorded in [BUILD](../BUILD.md), new scientific and commercial research, source-code inspection, and direct public-data checks. The living specifications remain [SPEC](../SPEC.md), [CONTRACTS](../CONTRACTS.md), [NUMERICS](../NUMERICS.md) and [VALIDATION](../VALIDATION.md). Recommendations here are not silently installed contract changes. BUILD remains the only task-status home.

The input snapshot was main `64d2fccbc27cf772a44b75364525be2b1e5f6a40`; the subsequent main source-assessment updates through `14d0ce823fbc849b887d4707ff0361b538b0f696` were inspected before publication. The agentic-review branch was also consulted. No application or DGX Spark run was produced by this research. All scenarios, evaluations, modules and demonstrations described below are **proposals unless explicitly identified as executed source or synthetic-formulation checks**.

## Contents

- [1. Executive research verdict](#1-executive-research-verdict)
- [2. Research atlas](#2-research-atlas)
- [3. Annotated bibliography and priority readings](#3-annotated-bibliography-and-priority-readings)
- [4. Existing software and implementation catalogue](#4-existing-software-and-implementation-catalogue)
- [5. Sheffield geospatial data catalogue](#5-sheffield-geospatial-data-catalogue)
- [6. Scientific and mathematical specification recommendations](#6-scientific-and-mathematical-specification-recommendations)
- [7. NVIDIA technical implementation recommendation](#7-nvidia-technical-implementation-recommendation)
- [8. Agentic AI architecture and evaluation](#8-agentic-ai-architecture-and-evaluation)
- [9. Product, originality and hackathon analysis](#9-product-originality-and-hackathon-analysis)
- [10. Implementation blueprint](#10-implementation-blueprint)
- [11. Validation and benchmark matrix](#11-validation-and-benchmark-matrix)
- [12. Risks and unresolved questions](#12-risks-and-unresolved-questions)
- [13. Prioritised action roadmap](#13-prioritised-action-roadmap)
- [14. Documentation amendment recommendations](#14-documentation-amendment-recommendations)
- [Appendix A: annotated sources](#sources)
- [Final independent conclusions](#final-independent-conclusions)

## 1. Executive research verdict

### Verdict

**Build a local, evidence-bearing tree-placement decision system—not a generic environmental chatbot, and not an unvalidated universal ecosystem calculator.** Its useful question is: *Given this site's geometry, costs, exclusions and uncertainty, which feasible arrangement improves a declared objective, why does it beat the alternatives, and which missing evidence could change that decision?*

The ambitious end-state remains substantial: measured site geometry; seasonal and lifecycle tree profiles; optimisation with winter and distributional trade-offs; optional validated hydrology, building-energy and ecological modules; a local agent that chooses informative investigations; and a reproducible proposal a planner can challenge. The Friday deliverable is a vertical slice of that architecture, not the ambition ceiling. Implement additional modules when their data and validation gates are met, not merely when a model can describe them.

**The largest correction to the original pitch is competitive, not technical.** Infrared City publicly offers agent-facing microclimate simulations, Python/TypeScript SDKs, a `use-infrared` skill and a tree/shade scenario. Its pinned public skill predates the cutoff. Accordingly, “an AI agent calls a climate simulator to test trees” is already occupied territory. Its self-hosting and performance statements are vendor claims; the public integration skill does not establish open-source physics or an obtainable offline engine[7][15][17].

There is also close academic prior art: TreePlanter optimises tree placement for outdoor thermal comfort, and Schrodi et al. combine SOLWEIG-derived training targets, neural surrogates and iterated local search for urban-tree placement. The latter's reported model error is relative to its simulation reference, not evidence that our Sheffield model predicts observed air temperature. This project should not claim to invent tree optimisation, learned microclimate surrogates or natural-language geospatial planning[71][20].

### What is strong

- **A real decision rather than a dashboard:** layout choice under budget, spacing, access and existing shade, with visible alternatives and reasons for exclusions.
- **A clean authority boundary:** deterministic evaluators own geometry, constraints and numbers; the agent chooses investigations and explains evidence. Existing typed contracts, scene revisions and stale-result handling are worth preserving.
- **A genuine local-compute use case:** inspectable local model inference plus batched site analysis, with a preloaded lawful bundle that remains useful without network access. Spark offers Arm CPU, Blackwell GPU and unified memory, but compatibility and workload performance still require measurement[42][161].
- **A useful scientific progression:** direct shade first; radiation and thermal comfort only after their additional inputs; broader services through explicit modules rather than arithmetic conversions from canopy area[69][129][133].
- **A defensible product differentiation:** an auditable explanation of *decision fragility* and a *survey-before-planting* workflow, rather than another heatmap.

### What is weak or unproven

- There is no verified implementation, accepted Sheffield scene bundle, target-device latency or useful-agent benchmark in this dossier.
- A point tree inventory is not a measured crown model; public park polygons are not planting permission; historic planting areas are not current opportunities. Direct service checks confirmed these distinctions[115][116][118].
- Crown allometry does not supply age-dependent growth, LAI does not supply a universal optical coefficient, and a tree-shaped mesh does not supply local thermal comfort[74][124][127].
- A successful tool call does not establish useful agency. The fixed/manual workflow may be better; that must be allowed as an evaluation outcome[60][61][154].
- Cross-service totals can look impressive while combining incompatible quantities, dates and assumptions. Shade, carbon stocks, runoff, bills, biodiversity units and welfare values must not be casually added[136][139][142].

### Recommended scientific depth

**Core quantitative claim:** additional direct-solar blocking on explicitly weighted ground receivers, in m²·h, under stated geometry, foliage, horizon and time scenarios. Show winter loss separately. Provide a feasible discrete optimisation baseline and small-instance exact comparisons. Treat fractional transmission as a documented modelling choice, not a measured species truth[68][74][77].

**Next defensible extensions:** (1) scenario-based crown growth/phenology and survivorship sensitivity, (2) direct incident solar-energy reduction with real meteorological provenance, (3) a reproducible SOLWEIG/UMEP comparison for radiation/mean radiant temperature, and (4) one well-surveyed building or drainage use case. Choose the next module by an actual decision and obtainable data, not by which output sounds greenest[83][124][133].

### Recommendations that should not survive evidence

Do not promise cooling degrees, rain shelter, flood prevention, irrigation savings, heating or cooling bills, pollution exposure reduction, carbon offsets, biodiversity compliance, a particular speedup or a global optimum before the corresponding inputs and tests exist. Do not pitch first-of-kind agency or equate NVIDIA branding with hardware proof[69][99][142].

## 2. Research atlas

The relevant field is not one literature. It is a chain of different models and decisions:

- **Solar geometry and visibility:** SPA/pvlib provide the solar direction; mesh or raster visibility describes obstruction. Their accuracy does not rescue wrong geometry, dates or coordinates. **Use now.** [67][68]
- **Urban radiation and thermal comfort:** SOLWEIG/UMEP and UTCI address more than direct shade, requiring meteorology and radiation assumptions. **Reference comparator and a later validated module.** [69][83][84]
- **Tree architecture and optics:** allometry, measured crown transmission, LAI, pruning and growth govern what the geometric object means. **Scenarios now; predictive profiles only with suitable evidence.** [74][124][127]
- **Combinatorial placement:** maximum coverage, submodular selection, budgeted coverage, conflict constraints and exact small instances provide interpretable optimisation. **Use now, with theorem boundaries.** [77][78][80]
- **Multiobjective design and uncertainty:** expected performance, worst case, regret and Pareto trade-offs answer different questions. **Use sensitivity and explicit alternatives now; no unjustified probabilistic confidence.** [80][171][170]
- **Ecosystem accounting:** i-Tree, SWMM, EnergyPlus, AQEG and the statutory biodiversity metric provide distinct models, not a common “benefit coefficient”. **Add modules only behind input/validation contracts.** [131][133][136]
- **Urban design tools:** Infrared City is the nearest agent-facing product overlap; ENVI-met, Ladybug/Radiance, UMEP and TreePlanter are important scientific/design alternatives; i-Tree serves a different inventory/valuation workflow. **Differentiate by decision auditability and local operation, not an assertion of empty competition.** [5][20][70]
- **Geospatial agents:** GIS Copilot and LLM-Find illustrate tool selection and spatial reasoning, including observed dependence on prompts, state and execution. **Borrow typed-tool and evaluation lessons, not reported success percentages as forecasts.** [169][151]
- **Scientific investigation agents:** ReAct, LangGraph and NeMo Agent Toolkit help implement or observe a loop; they do not decide whether a simulation is scientifically meaningful. **One controlled domain loop, not agent proliferation.** [56][58][59]
- **Decision support and value of information:** identify what uncertainty drives a decision and what measurement could reduce regret. **Promising differentiator, but strict VOI needs probabilities and decision losses.** [64]
- **Professional and purchasing context:** Sheffield's tree-management procurement and the University's tree strategy evidence real maintenance/planning workflows, not customer demand for this product. **Validate the buyer and proposal format before a SaaS claim.** [143][144]

**Evidence labels used throughout:** primary documentation/source inspected; published research full text or method sections inspected; abstract/metadata only; vendor claim; our derivation; proposed implementation; executed synthetic check. An accessible URL is not proof that a full paper was read or a tool was run. Some full-text and licence gaps remain, and are marked in the annotations.

## 3. Annotated bibliography and priority readings

The [annotated bibliography](#sources) records title, author/publisher, date/version, source type, access/read depth, contribution, method, limitation, intended use, reader and priority for each reference. It includes research, official data, implementation source, model cards and product evidence; the total is **not a count of peer-reviewed papers**. Related pages are retained separately where they establish different facts—for example a product page, public integration code, licence and model-specific serving instructions.

The research used general and targeted scientific/official searches, then primary pages, repositories, model cards, public REST schemas and technical PDFs. Four subject lanes were reconciled with an independent high-impact source audit. Primary verification was repeated for consequential findings including the competitor skill, event criteria, model-serving requirements, real ArcGIS field meanings, Green Book rates and the biodiversity-guide version.

**Temporal rule:** the cutoff is 11 November 2026. Pinned repositories and dated documents establish specific pre-cutoff versions. An undated page retrieved on the cutoff is only that day's snapshot. It does not prove when a feature was introduced. Main/master pages and current releases are not historical evidence by themselves[15][47][51].

**A concrete retrieval conflict was resolved:** a clean-text extractor returned a June 2026 biodiversity landing-page snapshot, while direct publisher HTML listed 3 and 10 November updates; the directly retrieved November guide includes a 2 November document-history entry. The later pre-cutoff primary HTML/PDF, not the stale extracted summary, is used here. No claim is made that its spreadsheet formulas were executed[139].

**Limits:** full text was not available for every paper; several commercial licences or exact binary distributions were not audited; no closed software was installed or benchmarked; no accounts were created; no paid APIs were called; no restricted site asset was redistributed. Retrieved public PDF text was used for research, not copied wholesale into this deliverable.

### Priority reading sequence

1. **Lindberg et al., SOLWEIG 1.0 + UMEP implementation:** Arnav first, Ben second. Learn the boundary between direct shadow, radiation and Tmrt; inspect inputs and numerical outputs before using comfort vocabulary. **Essential.** [69][70][83]
2. **Schrodi, Briegel, Argus, Christen and Brox, Climate-sensitive Urban Planning through Optimization of Tree Placements (2023):** all three. Read method and limitations; understand the strongest close surrogate/optimisation precedent and its teacher-model dependence. **Essential.** [71]
3. **Nemhauser–Wolsey–Fisher; budgeted-coverage follow-up:** Arnav. Identify exactly why ordinary greedy has a guarantee and why our spacing/winter/cost constraints can invalidate that statement. **Essential.** [77][78][79]
4. **Urban Tree Manual + GB allometry summary:** Alex and Arnav. Turn a crown primitive into an evidence-bearing planning assumption; do not infer time growth from cross-sectional dimensions. **Essential.** [124][126]
5. **Konarska et al., single-tree transmissivity:** Arnav. Understand leaf-on/off measurements, directional transmission and limited transferability. **Essential.** [74]
6. **Infrared City pinned skill and design-variants notebook:** Ben and Alex. Inspect the actual competitive workflow before writing a novelty claim. **Essential.** [15][17]
7. **ReAct + GIS Copilot:** Ben. Separate tool-calling format, useful investigation and numerical authority; extract test cases, not just an orchestration pattern. **Essential.** [151][56]
8. **Spark system documentation + chosen Nemotron card:** Ben. Build a version-specific, Arm-compatible runtime plan; a model card is not a benchmark. **Essential.** [42][47][50]
9. **HSE HSG47 + exact Sheffield/EA metadata:** Alex. Understand why attractive polygons, LiDAR and utility maps cannot approve excavation. **Essential.** [99][115][118]
10. **ENCA and the 2026 Green Book:** all three once service modules are proposed. Separate physical outputs, welfare, budgets, discounting and double counting. **Useful now; essential before monetisation.** [141][142]

## 4. Existing software and implementation catalogue

### Closest product overlap: Infrared City

Its public agent page describes an agent accessing felt heat, wind, sun/shade, radiation and daylight through an SDK. The pinned `use-infrared` skill contains executable integration guidance and a design-variant notebook, rather than only promotional prose. This is strong evidence of concept/workflow overlap. The website also claims self-hosting and seconds-scale runs. **Those are vendor statements, not our independent benchmarks or proof that we can obtain the engine for Spark.** The public repository is an integration surface, not evidence that the numerical engine is open source[7][15][17].

**What to borrow:** domain-specific tools, machine-readable result arrays, design variants, evidence-linked comparison and a constrained workflow. **What not to copy into a claim:** its speed, scientific validity, open-source status or offline availability. Its pricing snapshot provides a commercial reference, not our budget approval or a substitute for an audited local implementation[9].

**Our potential advantage:** a small, transparent crown/visibility reference model; locally reproducible constraints and cache identity; investigation into assumption sensitivity; survey priorities; and a proposal whose values can be traced to scene revisions. This advantage remains a hypothesis until a user prefers the workflow and a held-out evaluation supports it.

### Scientific/design alternatives

- **SOLWEIG + UMEP:** urban radiation/Tmrt models and a GIS processing ecosystem. Strong reference path for environmental fidelity and source transparency. More input-heavy than a visibility slice; matching SOLWEIG establishes comparator agreement, not observed physical truth[69][70][83].
- **TreePlanter / Wallenberg, Lindberg and Rayner:** directly relevant algorithmic tree placement for outdoor thermal comfort. Undercuts claims of novel optimisation. The full paper and pinned UMEP implementation were inspected, but the archived runtime was not reproduced; do not invent a successful installation or benchmark[20][21][22].
- **Schrodi et al. / Freiburg tree-planting:** strongest close research baseline for surrogate-assisted placement. Neural estimates replace expensive repeated Tmrt simulation inside a search procedure; the paper explicitly discusses static environments and uniform tree parameterisation. Borrow the teacher–surrogate–search decomposition only after a deterministic reference exists[71].
- **ENVI-met:** broader coupled microclimate modelling. Appropriate comparator for scientific scope; commercial/runtime/licence complexity makes it a poor unverified hackathon dependency. No run or project-specific validity was established[155].
- **Ladybug Tools/Radiance:** existing environmental-design and ray/radiation components. Potential reference/export path; do not rebuild a trusted solver merely to produce a GPU claim. Pin the particular packages and licences before adoption[156].
- **i-Tree Eco/HydroPlus:** inventory/service and vegetation-hydrology workflows. Useful methods, required-input lists and accounting boundaries. Eco v6's documented data-submission workflow is not a local offline service. HydroPlus is a different hydrologic workflow and still needs calibration[130][136][147].
- **EnergyPlus / DREAMS:** credible future building-energy route and UK school archetype research. These solve a different physical boundary from a shade map. Existing stock-level models are not ready-made measurements of one Sheffield building[133][134][145].

### Agent/digital-twin alternatives

GIS Copilot and LLM-Find already demonstrate language-to-geospatial operations. Their existence is evidence against generic “first AI GIS assistant” claims, not proof of reliable planting advice. ReAct, LangGraph and NeMo Agent Toolkit supply patterns or infrastructure rather than a specialised planning product[151][169][59].

GENeCITY is a funded programme with generative/agentic digital-twin overlap, starting in June 2026. It should appear as a research direction, **not a completed validated rival product**. Omniverse and PhysicsNeMo may help at later scales, but are not evidence that a digital twin or learned physics is currently necessary[10][160][157].

### Additional concrete precedents inspected

- **Tree Folio (Cornell):** a city-scale canopy digital-twin/shade-communication precedent. The institutional page was readable; the dashboard yielded little inspectable text and was not exercised. Useful for user-facing explanation and scale, not proof of a transferable optimiser or local runtime[25][26].
- **ShadePlan:** the pinned repository registers a Google ADK urban-cooling agent and shade tools. Its actual shade code uses a degree-based grid, approximate metre conversions, building-centre shadow paths and repeated grid increments capped at one. This is stronger evidence of overlapping workflow than its README alone, but not a physically validated crown/mesh solver. Borrow the tool/interface idea; do not reuse its shade coefficients as validated physics. No runtime benchmark was performed[27][28][29].
- **UrbanTreeAgent:** the inspected repository describes an implementation inspired by a five-component architecture. The actual planner builds an ordered capability sequence with fixed defaults and fallback parameters; this does not by itself prove learned, adaptive planning. Its image-processing/tree-inventory focus differs from feasible tree-placement optimisation. Code availability is not independent validation of the underlying paper[33][34][35].
- **TreeShadeMapper:** a separate project from the Freiburg optimiser. The pinned README links Fujiwara et al. (2024) and describes panorama segmentation/binarisation, canopy transmission, sky-view factor and solar irradiance. It is a useful measurement/reference direction; image rights, transferability and its stated CC BY-SA 4.0 code terms require consideration. It was source-inspected, not installed or validated on Sheffield imagery[36].
- **Autodesk Forma and Snaptrude:** primary vendor pages describe microclimate/design tools and AI-assisted site-analysis workflows. These establish adjacent commercial demand propositions, not independently measured accuracy, local execution or a winner's implementation. Avoid pitching natural-language site analysis as empty market space[37][38][39].
- **i-Tree Design:** the calculator and official FAQ are relevant browser-based tree-benefit substitutes. Check supported geography/model assumptions before reusing outputs; opening a calculator does not validate UK transfer[40][41].

### Substitutes and demand

A planner can already use a manual map, a GIS expert, an arboricultural consultant, a fixed coverage optimiser or an established simulation package. These are the real baselines. The product must reduce time, reveal a consequential trade-off or produce a more defensible decision—not just replace clicking with chat.

The Sheffield tree-management framework and University strategy support a concrete discovery route: estate/arboricultural teams managing stock, maintenance and canopy change. They do not establish willingness to pay for our software. First test an evidence-bearing layout and survey brief with such a user; monetisation remains an unvalidated proposition[143][144].

### Implementation catalogue

These are reuse/fit assessments, not installed dependencies. Scientific validation and target-runtime proof remain separate.

### pvlib python 0.13.1
**Official source:** https://pypi.org/project/pvlib/0.13.1/
- **Purpose / capabilities:** Versioned solar-position wrapper, SPA options, timezone behavior and angle outputs documented.
- **Platform / dependencies:** Python; version record requires Python >=3.10 and labels OS independence
- **Licence:** BSD-3-Clause
- **Limits / integration difficulty:** Documentation inspection only; no environment, dependency or Spark compatibility test.
- **Recommended readiness / role:** Best-supported astronomy reuse candidate; pin and smoke-test before adopting.
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### UMEP / SOLWEIG
**Official source:** https://github.com/UMEP-dev/UMEP
- **Purpose / capabilities:** Public model papers and source establish raster shadow/radiation tools; inspected tree includes SOLWEIG and shadow utilities.
- **Platform / dependencies:** QGIS plugin with Python components
- **Licence:** Current repository GPL-3.0; historical archive license not inspected
- **Limits / integration difficulty:** Current branch is unpinned; no runtime verification; fuller radiation modelling has additional inputs.
- **Recommended readiness / role:** Research comparator and future radiation-model candidate; not verified as a drop-in product service.
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### TreePlanter v1.0 published code archive
**Official source:** https://doi.org/10.5281/zenodo.4616761
- **Purpose / capabilities:** Published paper describes overlap-aware hill-climbing and greedy placement algorithms.
- **Platform / dependencies:** Paper/tutorial identify QGIS/UMEP context
- **Licence:** Unknown; archive inaccessible
- **Limits / integration difficulty:** Archive bytes, source contents and compatibility were not inspected.
- **Recommended readiness / role:** Prior-art reference; reproduction blocked pending accessible archive.
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### TreePlanter published test dataset
**Official source:** https://doi.org/10.5281/zenodo.4616770
- **Purpose / capabilities:** Dataset is explicitly identified by the TreePlanter paper.
- **Platform / dependencies:** Raster-based research workflow
- **Licence:** Unknown
- **Limits / integration difficulty:** No dataset contents or metadata verified.
- **Recommended readiness / role:** Potential comparison dataset, currently an access gap.
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### Freiburg tree-planting research software
**Official source:** https://github.com/lmb-freiburg/tree-planting
- **Purpose / capabilities:** README documents training, aggregation periods and optimisation methods; selected source contains a CUDA device assumption.
- **Platform / dependencies:** Python/PyTorch research scripts with conda environment file
- **Licence:** MIT shown on project page
- **Limits / integration difficulty:** Unpinned branch; training data permission unresolved; no verified pretrained assets or Spark compatibility.
- **Recommended readiness / role:** Conceptual/algorithm reference; unsuitable as an assumed event-day dependency.
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.


**Parent reconciliation:** README and optimisation source are pinned to commit `2e9c58435bb6a14be515b6a1879d67a4d27bb2cef` in [23][24]; no installation or numerical reproduction was performed.

### Freiburg research input data
**Official source:** https://github.com/lmb-freiburg/tree-planting
- **Purpose / capabilities:** Paper describes five urban study areas and input families; no data inspected.
- **Platform / dependencies:** Research raster and meteorological inputs
- **Licence:** Unknown; README says city permission to share is under discussion
- **Limits / integration difficulty:** Availability and redistribution rights unverified.
- **Recommended readiness / role:** Not available for this project's demonstration on current evidence.
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.


**Parent reconciliation:** README and optimisation source are pinned to commit `2e9c58435bb6a14be515b6a1879d67a4d27bb2cef` in [23][24]; no installation or numerical reproduction was performed.

### Google OR-Tools CP-SAT
**Official source:** https://developers.google.com/optimization/cp/cp_solver
- **Purpose / capabilities:** Integer constraints, optimisation statuses and enumeration interface documented.
- **Platform / dependencies:** Official examples cover Python, C++, Java and C#; target-platform installation untested
- **Licence:** Code samples Apache 2.0; selected distribution license requires manifest verification
- **Limits / integration difficulty:** Exactness concerns the encoded model and configured stopping/tolerances; no size/runtime benchmark.
- **Recommended readiness / role:** Recommended small-instance oracle after package smoke and independent enumeration.
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### GRASS GIS r.sun, 8.4 documentation
**Official source:** https://grass.osgeo.org/grass84/manuals/r.sun.html
- **Purpose / capabilities:** Terrain shadowing, horizon-map reuse, beam/diffuse/reflected outputs and solar-time controls documented.
- **Platform / dependencies:** GRASS GIS raster module; project environment untested
- **Licence:** GNU GPL >=2 according to module manual
- **Limits / integration difficulty:** Single elevation surface does not represent arbitrary raised crowns or overhangs; angular conventions differ.
- **Recommended readiness / role:** Credible non-RT reference and terrain cross-check; not a complete tree-planning evaluator.
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### DGX Spark / GB10
**Official source:** https://docs.nvidia.com/dgx/dgx-spark/hardware.html
- **Purpose / capabilities:** Official hardware specification inspected
- **Platform / dependencies:** Linux ARM64; unified CPU/GPU memory
- **Licence:** Hardware and installed-software terms vary
- **Limits / integration difficulty:** No assigned-device access, availability, resource reservation or throughput verified
- **Recommended readiness / role:** Suitable target in principle; B09/B12 unproven
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### Warp
**Official source:** https://github.com/NVIDIA/warp/tree/v1.9.1
- **Purpose / capabilities:** Packaging and software mesh-ray traversal inspected
- **Platform / dependencies:** Versioned Linux AArch64 CUDA and CPU paths documented
- **Licence:** Apache-2.0
- **Limits / integration difficulty:** No application execution; inspected path does not prove RT use
- **Recommended readiness / role:** Optional accelerator candidate after CPU reference
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### CuPy
**Official source:** https://docs.cupy.dev/en/v14.0.0/install.html
- **Purpose / capabilities:** Array-oriented GPU package requirements inspected
- **Platform / dependencies:** CUDA 12/13 AArch64 wheels documented
- **Licence:** Unknown in this audit
- **Limits / integration difficulty:** Not a ready-made shade solver; CPU fallback requires an explicit implementation
- **Recommended readiness / role:** Use only for a demonstrated array-compute bottleneck
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### OptiX 9.0 / 9.1
**Official source:** https://developer.nvidia.com/designworks/optix/downloads/legacy
- **Purpose / capabilities:** Explicit RT acceleration API and public driver requirements
- **Platform / dependencies:** Linux/Arm listed
- **Licence:** NVIDIA SDK agreement
- **Limits / integration difficulty:** Detailed 9.0 notes gated; 9.1 requires R590+; no project binding tested
- **Recommended readiness / role:** Defer from critical path
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### NVIDIA-Nemotron-3-Nano-30B-A3B-BF16
**Official source:** https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16
- **Purpose / capabilities:** Model/card/parser candidate supported by primary documentation
- **Platform / dependencies:** Spark route documented in pinned card
- **Licence:** NVIDIA Nemotron Open Model License
- **Limits / integration difficulty:** Large resident weights; no measured fit, latency or domain performance
- **Recommended readiness / role:** Candidate, not device-tested
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### NVIDIA-Nemotron-Nano-9B-v2
**Official source:** https://huggingface.co/nvidia/NVIDIA-Nemotron-Nano-9B-v2
- **Purpose / capabilities:** Tool-calling and cache instructions inspected
- **Platform / dependencies:** Local runtime route and Spark NIM catalogue available
- **Licence:** NVIDIA Open Model License Agreement
- **Limits / integration difficulty:** Different parser profile; exact fallback snapshot not retrieved
- **Recommended readiness / role:** Smaller qualification candidate
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### NVIDIA-Nemotron-3-Nano-4B-BF16
**Official source:** https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16
- **Purpose / capabilities:** Original card and release chronology inspected
- **Platform / dependencies:** Spark listed as target; newer vLLM requirement
- **Licence:** NVIDIA Nemotron Open Model License
- **Limits / integration difficulty:** Not compatible by assumption with supplied runtime; no benchmark
- **Recommended readiness / role:** Priority smaller-model experiment with its own pinned profile
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### NVIDIA vLLM 25.12.post1-py3 candidate
**Official source:** https://catalog.ngc.nvidia.com/orgs/nvidia/containers/vllm?version=25.12.post1-py3
- **Purpose / capabilities:** Tag page and base release notes retrieved
- **Platform / dependencies:** ARM64 asserted by supplied profile, not independently confirmed here
- **Licence:** Container-specific terms unverified
- **Limits / integration difficulty:** Digest/config/layer claims remain supplied metadata
- **Recommended readiness / role:** Must inspect exact image and execute on assigned host
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### llama.cpp
**Official source:** https://github.com/ggml-org/llama.cpp/releases/tag/b8268
- **Purpose / capabilities:** Local server and native/generic function-call handling documented
- **Platform / dependencies:** CPU and CUDA backends; tagged tool documentation inspected
- **Licence:** MIT
- **Limits / integration difficulty:** Exact Nemotron GGUF/template/build tuple not qualified
- **Recommended readiness / role:** Alternative runtime, not an automatic fallback
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### NVIDIA NIM for Nano 9B v2 on Spark
**Official source:** https://catalog.ngc.nvidia.com/orgs/nim/teams/nvidia/containers/nvidia-nemotron-nano-9b-v2-dgx-spark
- **Purpose / capabilities:** Container identity and dated collection listing
- **Platform / dependencies:** Spark-specific catalogue entry
- **Licence:** Separate NIM terms and access entitlement
- **Limits / integration difficulty:** Access gated; no image/profile execution inspected
- **Recommended readiness / role:** Optional organiser-provided service
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### LangGraph
**Official source:** https://github.com/langchain-ai/langgraph
- **Purpose / capabilities:** Persistence and human-interruption architecture documented
- **Platform / dependencies:** Python orchestration
- **Licence:** Not independently audited
- **Limits / integration difficulty:** Does not implement domain permissions, job idempotency or metric validation
- **Recommended readiness / role:** Optional; native state machine preferred for initial scope
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### NeMo Agent Toolkit
**Official source:** https://github.com/NVIDIA/NeMo-Agent-Toolkit/tree/v1.3.1
- **Purpose / capabilities:** Agent configuration, custom evaluators and profiling integration documented
- **Platform / dependencies:** Python; ARM64 dependency closure untested
- **Licence:** Apache-2.0
- **Limits / integration difficulty:** Inspected defaults conflict with strict parsing and completion policy unless changed
- **Recommended readiness / role:** Optional evaluation adapter
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### NeMo Guardrails
**Official source:** https://github.com/NVIDIA-NeMo/Guardrails/tree/v0.16.0
- **Purpose / capabilities:** Programmable rail categories and custom actions documented
- **Platform / dependencies:** Python
- **Licence:** Apache-2.0
- **Limits / integration difficulty:** No configured policy or security proof comes from installation alone
- **Recommended readiness / role:** Defer unless it replaces concrete required work
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### TDAG species-selection guide and supplementary database
**Official source:** https://www.tdag.org.uk/tree-species-selection-for-green-infrastructure.html
- **Purpose / capabilities:** Publisher describes species characteristics and environmental-tolerance selection fields
- **Platform / dependencies:** PDF and XLSX
- **Licence:** Supplementary database CC BY-NC 4.0; guide terms unresolved
- **Limits / integration difficulty:** Guide too large to fetch; workbook cells not inspected; live version date unresolved
- **Recommended readiness / role:** Reference candidate; no imported or approved profiles
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### GB urban-tree allometry study
**Official source:** https://www.forestresearch.gov.uk/publications/allometric-relationships-for-urban-trees-in-great-britain/
- **Purpose / capabilities:** Study relates DBH, height and crown width across GB urban locations
- **Platform / dependencies:** Paper
- **Licence:** Article and underlying-data terms unknown
- **Limits / integration difficulty:** Full coefficients, residuals and applicability domains not inspected
- **Recommended readiness / role:** Evidence for caution; not an implementation-ready parameter table
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### Seasonal urban-tree LAI study
**Official source:** https://doi.org/10.1016/j.ufug.2025.128795
- **Purpose / capabilities:** Size and seasonal LAI analysis for German urban trees; photographic measurement protocol
- **Platform / dependencies:** Paper tables and methods
- **Licence:** Paper CC BY 4.0; separate dataset packaging not audited
- **Limits / integration difficulty:** Measurement bias, site transfer and leaf/wood separation
- **Recommended readiness / role:** Sensitivity and measurement-method reference
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### i-Tree HydroPlus
**Official source:** https://www.itreetools.org/tools/hydro
- **Purpose / capabilities:** Statistical hydrology, vegetation processes, GI configuration, test cases and calibration workflow documented
- **Platform / dependencies:** Dated manual describes C++ source, Windows executable and command-line configuration
- **Licence:** i-Tree EULA; complete rights not verified
- **Limits / integration difficulty:** US data assumptions; UK preprocessing and calibration required; no binary or source package inspected
- **Recommended readiness / role:** Future research pilot only; no compatibility or runtime claim
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### EPA SWMM 5.2 / documented 5.2.4 distribution
**Official source:** https://www.epa.gov/water-research/storm-water-management-model-swmm
- **Purpose / capabilities:** Subcatchment runoff, infiltration, hydraulic routing, LID layers and continuity diagnostics
- **Platform / dependencies:** Version 5.2 manual documents Windows GUI; no other platform verified for the selected package
- **Licence:** EPA identifies open/free software; exact release-package legal text not inspected
- **Limits / integration difficulty:** Requires drainage and soil inputs; depression storage does not provide a species-specific canopy model
- **Recommended readiness / role:** Established external model, unintegrated and untested for this project
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### EnergyPlus 24.2
**Official source:** https://bigladdersoftware.com/epx/docs/24-2/engineering-reference/shading-module.html
- **Purpose / capabilities:** Versioned documentation describes sunlit fractions, partial transmission and solar-distribution methods
- **Platform / dependencies:** No installation or target-platform compatibility verified
- **Licence:** Exact software-release licence not verified; mirror documentation rights are separate
- **Limits / integration difficulty:** Requires complete building inputs and validation; undated mirror cannot authenticate every historical line
- **Recommended readiness / role:** Future building-model candidate; no tested coupling
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### DREAMS England primary-school archetype methodology
**Official source:** https://discovery.ucl.ac.uk/id/eprint/10130905/
- **Purpose / capabilities:** Generation and measured-energy comparison of English school archetypes
- **Platform / dependencies:** Paper documents Python processing and EnergyPlus 8.9
- **Licence:** Paper CC BY 4.0; model files and underlying records not cleared
- **Limits / integration difficulty:** Stock-average validation; individual schools, tree effects and current model availability unverified
- **Recommended readiness / role:** Methodological starting point
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### CCC/Kamma residential archetypes
**Official source:** https://www.theccc.org.uk/publication/residential-archetypes-dataset-methodology-kamma-climate/
- **Purpose / capabilities:** Publisher and methodology describe UK housing archetypes and energy/heating characteristics
- **Platform / dependencies:** Downloadable dataset plus PDF methodology
- **Licence:** Dataset reuse terms unresolved
- **Limits / integration difficulty:** Aggregated and partly imputed; no detailed window geometry or tree-intervention response established
- **Recommended readiness / role:** Future stock-level context
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### i-Tree Eco v6
**Official source:** https://www.itreetools.org/support/resources-overview/i-tree-manuals-workbooks
- **Purpose / capabilities:** Dated manuals describe inventory-based ecosystem-service reports and user-entered costs/prices
- **Platform / dependencies:** Documented desktop workflow with server-side processing and result retrieval
- **Licence:** EULA; full rights not verified
- **Limits / integration difficulty:** Not a demonstrated local offline dependency; service-specific inputs and transferred assumptions remain
- **Recommended readiness / role:** Comparator and external assessment pathway, not Friday integration
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### Statutory Biodiversity Metric
**Official source:** https://www.gov.uk/government/publications/statutory-biodiversity-metric-tools-and-guides
- **Purpose / capabilities:** Guide defines habitat accounting, separate unit types and individual-tree helper rules
- **Platform / dependencies:** Official Excel calculation tools and PDF guidance
- **Licence:** User guide OGL v3.0; workbook-specific notices not inspected
- **Limits / integration difficulty:** Workbook calculations not executed; ecological competence required; proxy areas are not physical crowns
- **Recommended readiness / role:** Future professionally reviewed workflow; no compliance output now
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.

### Green Book and ENCA appraisal framework
**Official source:** https://www.gov.uk/government/publications/the-green-book--2
- **Purpose / capabilities:** Present-value, distributional and natural-capital appraisal methods
- **Platform / dependencies:** Guidance; no calculation software selected
- **Licence:** OGL except where otherwise stated
- **Limits / integration difficulty:** Does not supply missing physical effects or local costs; October 2026 guidance versions need reconciliation
- **Recommended readiness / role:** Suitable for designing a future transparent calculation contract
- **Performance evidence:** no project-specific install, numerical or target-device benchmark was run in this research; published claims are not imported as our results.


## 5. Sheffield geospatial data catalogue

### 5.1 Direct checks actually performed

Public REST metadata and bounded attribute queries were retrieved on the cutoff date; no real site bundle, mesh or approved planting mask was produced.

- **Community Forestry Trees:** point geometry in EPSG:27700; fields include species, `height`, `position`, `age`, condition and inspection dates. Samples showed categorical height such as `<5 metres` and age such as `Young`: neither is a measured crown or exact age[115].
- **Community Forestry Tree Planting Areas:** polygons with financial-year fields such as `fy201213` and `fy202021`. These record historic activity, not vacant land for new planting[116].
- **Street Trees:** point geometry in EPSG:27700; a small field set including `site_name`, not a comprehensive dimensional crown inventory[117].
- **Parks and Countryside Sites:** polygons in EPSG:27700 with `site_name` and `site_type`. A bounded name query returned **Manor Fields Park** and **Weston Park**; it did not establish Peace Gardens membership in that dataset[118].
- **School Localities:** polygons in EPSG:4326 with generic locality IDs/areas, not school point records or establishment identifiers. It cannot be silently converted into school planting sites. GIAS is the more appropriate establishment-identity starting point, still not ownership or boundary permission[119][162].
- **SuDS Regions:** regional guidance polygons with region/area/perimeter and guidance links, not a drain or pipe inventory[120].
- **EA DTM, first-return DSM and last-return DSM indices:** a point query at the existing approximate Weston locator `(434002,387395)` in British National Grid returned survey `P_10706`, with acquisition dates **16–17 March 2021**, in all three indices. This is a catalogue/locator result only, not a complete site-coverage or raster-header audit. A 2022 composite label is not the local survey date, and a March survey's seasonal canopy state must be investigated[121][122][123].

The exact service entries carry their own copyright. Several council services expose Crown/database-right statements and OS licence identifiers; catalogue pages can point to INSPIRE terms. Free endpoint access is not blanket OGL permission to redistribute an exported mesh[87][88][118].

### 5.2 Three plausible site candidates—not a selected site

**A. Weston Park edge/path pilot — recommended geometry-validation candidate.** Council park records and a heritage entry provide identity/context; the EA locator gives a concrete survey index. A small, recognisable mixed tree/building area can expose baseline shade and crown uncertainty. Disadvantages are historic-design context, existing canopy, consent and incomplete dimensional/utility evidence. Do not infer eligibility to plant[95][118][121].

**B. Manor Fields Park edge/path pilot — recommended operational alternative.** The council polygon query established a named park record. It may offer an understandable park/access/use-case story, but a real receiver target, drain/soil constraints and local geometry audit are still needed. No claim that its open-looking areas are plantable follows from the polygon[118][120].

**C. Peace Gardens / central public-realm block — conditional demonstration candidate.** Its dense surroundings could make building shade, access and winter trade-offs legible. In this audit the named parks query did not return it; a lawful boundary and ownership/management evidence therefore remain to be established, together with event/access/utility constraints. It is a candidate for investigation, not the recommended default merely because it is recognisable[87][99][101].

If a school use case becomes the team's priority, start with a named GIAS establishment and its responsible estate owner, then obtain the actual boundary and permission. Do not choose a school from the misinterpreted Localities layer[162][119].

### 5.3 Data and rights assessment

- **EA composite DTM/DSM:** best immediate public candidate for metre-scale terrain/surface evidence. Inspect the exact tile year, CRS/vertical reference, no-data values, resolution, units and local season. `DSM−DTM` is height above terrain under aligned assumptions, not a labelled crown or building segmentation. The opened catalogue describes 1 m composites and OGL conditions; do not generalise accuracy metadata to every extracted building[91][92][93].
- **Full survey/point-cloud data:** investigate separately when class information or dates matter. A catalogue footprint does not mean every needed product was downloaded, classified or acceptable[92][93].
- **OS OpenMap Local:** useful open footprint/context candidate; extraction/scale and missing building heights limit it. Open-product terms do not extend to every OS detailed product[100].
- **OS Data Hub:** verified developer documentation describes APIs/downloads and distinct open, premium and public-sector access plans. No account or production rights were obtained. A separate official product under the exact name **OS Data Science Hub** was not established in this search; do not treat that phrase as an access grant. Neither academic interest nor an account supplies blanket redistribution permission[164].
- **OpenStreetMap:** useful exploratory footprints, paths and context, subject to completeness and ODbL obligations. Read the copyright guidance for database and produced-work use. Basemap tile-service terms are a separate issue[101].
- **Copernicus DEM GLO-30:** useful regional context, usually too coarse to claim street-scale tree/building geometry; a DSM rather than a bare-earth survey. Free access has product terms and attribution[165].
- **Ordnance Survey Maps API from GOV.UK API catalogue:** a discovery entry, not an independent unrestricted data source or a licence grant[163].
- **HERE terrain/DEM:** official Raster Tile API documentation exposes a `dem` style with RGB-encoded elevation in PNG, orthometric heights, and no neighbour overlap/padding. Its 0.1 m encoding step is **not a claim of 0.1 m spatial resolution or accuracy**. Requests require an API key; copyright depends on style/area and source. A rendered `topo` style is not the same quantitative elevation raster. Sheffield resolution, vertical conversion to ODN and reuse rights were not established, so prefer the audited EA route first[148][149].
- **Blosm / OSM-to-mesh:** the actual wiki describes GPL addon source, building-height/floor-based geometry, Google 3D Tiles import and terrain of approximately 30 m resolution. The addon licence does not licence the underlying map assets. Some listed custom-tile methods are explicitly warned to contradict Google terms; they must not be used. This is a scene-assembly convenience, not measured fine-scale Sheffield geometry. No addon was installed or benchmarked[150].
- **Microsoft Maps 3D:** the primary Garage Maps SDK page is marked “Experiment complete” and describes streaming Bing 3D world/terrain data into Unity. That establishes a display/integration precedent, not a current supported offline-export pipeline. No mesh extraction/reuse grant was established. The old product/terms URL redirected to an Azure Maps marketing page; no licence conclusion was inferred from that redirect. Do not scrape or promise redistribution[172].
- **Cesium 3D Tiles:** an interchange/streaming specification for hierarchical 3D content, not a terrain source or licence to the underlying tiles. Useful later for large scenes; unnecessary as the first small-site physics representation[168].

HERE, Blosm and Microsoft were therefore assessed from actual documentation, with access/rights/runtime gaps preserved. They do not displace a lawful bounded EA + council/open-footprint bundle without evidence of better fit[148][150][172].

### 5.4 Pipeline from public data to an honest site bundle

1. **Source register:** publisher, exact URL/revision, retrieval date, acquisition date, licence/attribution, coverage, file hashes and permitted distribution. Keep rights unresolved flags operational.
2. **CRS/vertical preflight:** inspect native CRS/axes/units; transform through a known operation; record grid availability/accuracy. BNG horizontal coordinates and ODN vertical heights are not WGS84 ellipsoidal heights. Local-origin translation improves numerical conditioning but does not fix a datum error[111][107][113].
3. **Geometry extraction:** align DTM/DSM extents, resolution and no-data; inspect surfaces and cross-sections; compare footprint/height evidence; do not silently fill unknown heights. Preserve terrain where slope affects visibility[91][108][167].
4. **Physics mesh:** use controlled triangulation, normals and simplified geometry whose shadow deviation is measured. Keep it separate from a pretty display mesh. Open3D provides a reference raycasting surface, not automatic scene correctness[166].
5. **Tree representation:** reconcile inventory IDs and positions; attach measured or explicitly assumed crown primitives; record leaf state and uncertainty. Do not mesh unlabelled DSM vegetation and also add duplicate inventory crowns[115][117][124].
6. **Feasibility:** obtain/declare actual planting masks and access constraints. Polygon setbacks require planar metric geometry; Shapely ignores z, so it cannot perform the 3D shadow test. Utilities, ownership and consent remain independent evidence[99][110].
7. **Spatial indexing and candidate grid:** use the metric CRS, reject invalid geometry explicitly, bound candidate density and keep deterministic tie-breaking. pyproj/Rasterio/GDAL can implement transforms and raster processing; pin a supported distribution rather than assembling untested binaries[111][108][167].
8. **Checks:** overlay known control points, inspect several dimensions, compare sun/shadow direction at multiple dates, refine grid/time, identify missing obstructions and verify exact exported identifiers.
9. **Bundle:** baseline geometry + target receivers + plantability status + tree profiles + metadata + hashes + attribution, with separate licences per layer. Mark a synthetic bundle synthetic. A real-looking render is not source validation.
10. **Offline handoff:** preloaded accepted bundle, minimal renderer, deterministic evaluator, clear gaps and no hidden network requirement. The dataset audit produces a go/no-go choice and fallback, not another open-ended source search.

### Detailed data catalogue

The direct live-schema checks above supersede any narrower earlier metadata-only inspection statement below; they still do not establish an accepted site or unrestricted redistribution.

### Sheffield Community Forestry Trees
**Official source:** https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/Community_Forestry_Trees/FeatureServer/14
- **Purpose / capabilities:** Publisher advertises tree records and GeoJSON access [87]
- **Platform / dependencies:** ArcGIS REST
- **Licence:** OGL in publisher metadata; endpoint terms uninspected
- **Coverage:** Community Forestry planting since September 2019; incomplete for all Sheffield trees
- **Resolution:** Approximate positions; numerical accuracy unknown
- **Formats:** REST/GeoJSON advertised
- **Schema:** Not inspected; no crown/height fields verified
- **Acquisition / updates:** Publisher metadata 2025-11-27; individual record currency unknown
- **Access and rights:** Public metadata; no asset redistribution approval inferred
- **Inspection status:** False
- **Required preparation:** Verify survival and location; retain planting-date uncertainty; avoid canopy duplication
- **Limits / integration difficulty:** Planting history, not surviving canopy inventory
- **Recommended readiness / role:** Context candidate


**Parent live-query reconciliation:** HTTP 200 metadata and bounded attribute samples were inspected on 11 November 2026. Geometry esriGeometryPoint; CRS {'falseM': -100000, 'xyTolerance': 0.001, 'mUnits': 10000, 'zUnits': 1, 'latestWkid': 27700, 'zTolerance': 2, 'wkid': 27700, 'xyUnits': 450481592.76709664, 'mTolerance': 0.001, 'falseX': -5220400, 'falseY': -15524400, 'falseZ': 0}; fields: `objectid, treeid, species, site, plantingdate, plantingtype, globalid`. This supersedes the earlier metadata-only/no-sample status, not rights, site acceptance or survey validation.

### Sheffield Community Forestry Tree Planting Areas
**Official source:** https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/Community_Forestry_Tree_Planting_Areas/FeatureServer/19
- **Purpose / capabilities:** Historical grouped-planting areas advertised [87]
- **Platform / dependencies:** ArcGIS REST
- **Licence:** OGL in publisher metadata
- **Coverage:** Recorded programme planting
- **Resolution:** Approximate locations/sizes
- **Formats:** GeoJSON/REST advertised
- **Schema:** Unavailable through native web tool
- **Acquisition / updates:** 2025-11-27 metadata
- **Access and rights:** Check source asset attribution before reuse
- **Inspection status:** False
- **Required preparation:** Retain historical status; never convert directly to candidates
- **Limits / integration difficulty:** Not future planting permission or complete extant canopy
- **Recommended readiness / role:** Historical context only


**Parent live-query reconciliation:** HTTP 200 metadata and bounded attribute samples were inspected on 11 November 2026. Geometry esriGeometryPolygon; CRS {'falseM': -100000, 'xyTolerance': 0.001, 'mUnits': 10000, 'zUnits': 1, 'latestWkid': 27700, 'zTolerance': 2, 'wkid': 27700, 'xyUnits': 450481592.76709664, 'mTolerance': 0.001, 'falseX': -5220400, 'falseY': -15524400, 'falseZ': 0}; fields: `objectid, sitename, quantity, hectares, species, plantingyear, Shape__Area, Shape__Length, globalid`. This supersedes the earlier metadata-only/no-sample status, not rights, site acceptance or survey validation.

### Sheffield Street Trees
**Official source:** https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/INSPIRE/FeatureServer/14
- **Purpose / capabilities:** Location dataset advertised [88]
- **Platform / dependencies:** ArcGIS REST
- **Licence:** Publisher OGL; service/item terms unresolved
- **Coverage:** Sheffield street trees; no citywide canopy completeness established
- **Formats:** GeoJSON/REST advertised
- **Schema:** Not exposed by tool
- **Acquisition / updates:** 2026-01-07 publisher record
- **Access and rights:** Do not extrapolate OGL to an uninspected representation
- **Inspection status:** False
- **Required preparation:** Check duplicates, dates, live status and mesh overlap
- **Limits / integration difficulty:** Completeness and biological measurements unknown
- **Recommended readiness / role:** Rights/schema reconciliation required


**Parent live-query reconciliation:** HTTP 200 metadata and bounded attribute samples were inspected on 11 November 2026. Geometry esriGeometryPoint; CRS {'falseM': -100000, 'xyTolerance': 0.001, 'mUnits': 10000, 'zUnits': 1, 'latestWkid': 27700, 'zTolerance': 2, 'wkid': 27700, 'xyUnits': 450481592.76709664, 'mTolerance': 0.001, 'falseX': -5220400, 'falseY': -15524400, 'falseZ': 0}; fields: `objectid, sitename, featurelocation, featuretypename`. This supersedes the earlier metadata-only/no-sample status, not rights, site acceptance or survey validation.

### Sheffield Parks and Countryside Sites
**Official source:** https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/INSPIRE/FeatureServer/12
- **Purpose / capabilities:** Service-site polygons advertised [89]
- **Platform / dependencies:** ArcGIS REST
- **Licence:** PSMA terms in publisher record
- **Coverage:** Council Parks and Countryside Service sites
- **Resolution:** Some OS MasterMap alignment; accuracy not uniformly specified
- **Vertical datum:** Not applicable to advertised 2D boundaries
- **Formats:** GeoJSON/REST advertised
- **Schema:** Unverified; full query exceeded 4 MB tool response limit
- **Acquisition / updates:** Metadata 2024-05-21; links 2020
- **Access and rights:** Restricted/unknown pending exact licence assessment
- **Inspection status:** False
- **Required preparation:** Separate responsibility categories; validate outlines independently
- **Limits / integration difficulty:** Mixed management/ownership meanings; approximate outlines
- **Recommended readiness / role:** Discovery only; public export uncleared


**Parent live-query reconciliation:** HTTP 200 metadata and bounded attribute samples were inspected on 11 November 2026. Geometry esriGeometryPolygon; CRS {'falseM': -100000, 'xyTolerance': 0.001, 'mUnits': 10000, 'zUnits': 1, 'latestWkid': 27700, 'zTolerance': 2, 'wkid': 27700, 'xyUnits': 450481592.76709664, 'mTolerance': 0.001, 'falseX': -5220400, 'falseY': -15524400, 'falseZ': 0}; fields: `objectid, site_name, alias_name, site_type, greenflag, globalid`. This supersedes the earlier metadata-only/no-sample status, not rights, site acceptance or survey validation.

### Sheffield School Localities
**Official source:** https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/OpenData1/FeatureServer/7
- **Purpose / capabilities:** Seven administrative locality areas [90]
- **Platform / dependencies:** ArcGIS REST
- **Licence:** OGL publisher record
- **Coverage:** Sheffield administrative education localities
- **Resolution:** Administrative boundaries
- **Vertical datum:** Not applicable
- **Formats:** GeoJSON/REST advertised
- **Schema:** Response not readable in native web output
- **Acquisition / updates:** 2025-01-08
- **Access and rights:** OGL stated; no extract inspected
- **Inspection status:** False
- **Required preparation:** Prevent administrative areas entering planting/target geometry
- **Limits / integration difficulty:** Does not supply school grounds
- **Recommended readiness / role:** Exclude from physical site modelling


**Parent live-query reconciliation:** HTTP 200 metadata and bounded attribute samples were inspected on 11 November 2026. Geometry esriGeometryPolygon; CRS {'falseM': -100000, 'xyTolerance': 0.001, 'mUnits': 10000, 'zUnits': 10000, 'latestWkid': 27700, 'zTolerance': 0.001, 'wkid': 27700, 'xyUnits': 10000, 'mTolerance': 0.001, 'falseX': -5220400, 'falseY': -15524400, 'falseZ': -100000}; fields: `objectid, sd_code, sd_name`. This supersedes the earlier metadata-only/no-sample status, not rights, site acceptance or survey validation.

### EA 2022 Composite DTM 1 m
**Official source:** https://environment.data.gov.uk/dataset/13787b9a-26a4-4775-8523-806d13af58fc
- **Purpose / capabilities:** Bare-terrain raster metadata [91]
- **Platform / dependencies:** Defra Survey Data Download
- **Licence:** OGL identified in publisher search retrieval; mirror licence missing
- **Coverage:** Approximately 99% England
- **Resolution:** 1 m; 5 km delivery tiles
- **Horizontal CRS:** EPSG:27700 National Grid
- **Vertical datum:** Ordnance Datum Newlyn, metres
- **Formats:** GeoTIFF
- **Schema:** Elevation raster; actual bands/dtype/NoData unknown
- **Acquisition / updates:** 2022 composite; contributing surveys 2000–2022
- **Access and rights:** Confirm exact asset OGL and Environment Agency attribution
- **Inspection status:** False
- **Required preparation:** Inspect alignment, seams, masks and survey index; preserve unknowns
- **Limits / integration difficulty:** Site coverage, NoData and acquisition dates not inspected
- **Recommended readiness / role:** Strong geometry candidate

### EA 2022 Composite DSM 1 m, last/only return
**Official source:** https://environment.data.gov.uk/dataset/9ba4d5ac-d596-445a-9056-dae3ddec0178
- **Purpose / capabilities:** Surface raster includes terrain and objects [92]
- **Platform / dependencies:** Defra Survey Data Download
- **Licence:** Exact live asset terms require confirmation; mirror has no licence populated
- **Coverage:** Approximately 99% England
- **Resolution:** 1 m; 5 km tiles
- **Horizontal CRS:** National Grid; confirm EPSG in actual raster
- **Vertical datum:** Newlyn-referenced metres
- **Formats:** GeoTIFF
- **Schema:** Elevation raster; actual NoData/dtype unknown
- **Acquisition / updates:** 2022 composite; underlying dates vary
- **Access and rights:** Asset-specific confirmation required
- **Inspection status:** False
- **Required preparation:** Pair with correct return index; review vegetation/roof/temporary-object semantics
- **Limits / integration difficulty:** No semantic classes or validated crown geometry
- **Recommended readiness / role:** Conditional static-scene input

### EA Composite Survey Indices
**Official source:** https://services-eu1.arcgis.com/KB6uNVj5ZcJr7jUP/ArcGIS/rest/services/LIDAR_Composite_Catalogues/FeatureServer
- **Purpose / capabilities:** Readable layers 0 FZ DSM, 1 LZ DSM, 2 DTM [93]
- **Platform / dependencies:** ArcGIS REST
- **Licence:** Publisher copyright; exact index licence unresolved
- **Coverage:** England survey footprints
- **Resolution:** Survey polygons; resolution attribute per survey
- **Horizontal CRS:** EPSG:27700; HasZ false
- **Vertical datum:** Index geometry is 2D
- **Formats:** JSON, GeoJSON, PBF supported; 2000-record layer limit
- **Schema:** objectid, od_dtm_fn or od_dsm_fn, tilename, sd_flown, ed_flown, year, resolution, polygon_id, filename, comp_year, lidar_rtn, model_type, Shape__Area, Shape__Length
- **Acquisition / updates:** Inspected LZ/DTM edit date 2024-04-25; non-versioned
- **Access and rights:** Public schema access; reuse assessment pending
- **Inspection status:** False
- **Required preparation:** Query all intersecting context footprints; distinguish product/return type; do not read templates as observations
- **Limits / integration difficulty:** Site query failed; no actual survey features inspected
- **Recommended readiness / role:** Schema verified; local provenance pending

### OS Open Greenspace
**Official source:** https://www.ordnancesurvey.co.uk/products/os-open-greenspace
- **Purpose / capabilities:** Generalised sites, access points and published format mapping [112]
- **Platform / dependencies:** OS download products
- **Licence:** OS OpenData; exact package attribution/licence text uninspected
- **Coverage:** Great Britain; selected publicly accessible greenspace classes
- **Resolution:** Generalised vectors; coordinate precision is not accuracy
- **Horizontal CRS:** GML/GeoPackage BNG; vector tiles EPSG:3857
- **Vertical datum:** 2D dataset
- **Formats:** GeoPackage, GML, shapefile, vector tiles
- **Schema:** GeoPackage site: fid, id, function, distinctive_name_1–4, geometry; access: fid, id, access_type, ref_to_greenspace_site, geometry
- **Acquisition / updates:** Six-monthly advertised; release not selected
- **Access and rights:** OpenData advertised; package rights still to record
- **Inspection status:** False
- **Required preparation:** Join with id, not non-persistent fid; handle nested sites and preserve provenance
- **Limits / integration difficulty:** No surveyed plantability; excludes school-only enclosed fields
- **Recommended readiness / role:** Preferred alternative boundary candidate, pending extract

### OS OpenMap Local buildings
**Official source:** https://docs.os.uk/os-downloads/products/maps-and-imagery-portfolio/os-openmap-local/os-openmap-local-technical-specification/feature-types/building
- **Purpose / capabilities:** Generalised roofed-building definition [100]
- **Platform / dependencies:** OS vector mapping
- **Licence:** OpenData product; extract terms not inspected
- **Coverage:** Great Britain product; Sheffield features not inspected
- **Resolution:** Generalised mapping
- **Formats:** Product vector formats advertised; no package inspected
- **Schema:** Detailed attributes not read from diagram
- **Acquisition / updates:** No release selected
- **Access and rights:** Confirm extracted package
- **Inspection status:** False
- **Required preparation:** Use to review semantics, not duplicate DSM roofs
- **Limits / integration difficulty:** Can amalgamate structures; no measured heights established
- **Recommended readiness / role:** Context only

### OpenStreetMap candidate site and building geometry
**Official source:** https://www.openstreetmap.org/copyright
- **Purpose / capabilities:** Open database reuse and attribution rules [101]
- **Platform / dependencies:** OSM database
- **Licence:** ODbL
- **Coverage:** Global community mapping
- **Resolution:** Feature-dependent
- **Horizontal CRS:** Geographic OSM data; actual extract encoding not inspected
- **Vertical datum:** Height/elevation tag semantics require inspection
- **Formats:** No extract selected
- **Schema:** building, height and building:levels are prospective inspection targets, not observed site fields
- **Acquisition / updates:** Continuous edits; cutoff-bounded extract required
- **Access and rights:** Attribution/share-alike assessment; hosted API/tile policies separate
- **Inspection status:** False
- **Required preparation:** Resolve relations, units, dates and roof/base height meanings; retain missing values
- **Limits / integration difficulty:** No Sheffield features, heights or completeness verified
- **Recommended readiness / role:** Potential source only

### PVGIS hourly radiation
**Official source:** https://re.jrc.ec.europa.eu/api/v5_3/seriescalc
- **Purpose / capabilities:** Documented hourly CSV/JSON radiation components [102]
- **Platform / dependencies:** JRC public API
- **Licence:** Dataset-specific reuse terms unresolved
- **Coverage:** Sheffield within European product coverage
- **Resolution:** SARAH3 approximately 5 km; hourly
- **Horizontal CRS:** Latitude/longitude request
- **Vertical datum:** Returned elevation basis not established
- **Formats:** CSV/JSON
- **Schema:** Documented: time, G(i) or Gb(i)/Gd(i)/Gr(i), H_sun, T2m, WS10m, Int; inputs/outputs/meta
- **Acquisition / updates:** Pin API and radiation database; no actual request inspected
- **Access and rights:** Public documentation; redistribution not audited
- **Inspection status:** False
- **Required preparation:** UTC/BST conversion, radiation plane/components, interval alignment and horizon duplication
- **Limits / integration difficulty:** No Sheffield response; horizon/timestamp semantics require explicit choice
- **Recommended readiness / role:** Optional extension

### ERA5-Land hourly time series
**Official source:** https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries
- **Purpose / capabilities:** Nearest-grid-point time series [103]
- **Platform / dependencies:** Climate Data Store
- **Licence:** Publisher links CC-BY
- **Coverage:** Global; 1950 onward
- **Resolution:** 0.1 degree; hourly
- **Horizontal CRS:** Regular latitude/longitude
- **Vertical datum:** Model surface, not site survey height
- **Formats:** NetCDF/CSV advertised
- **Schema:** Documented variables include total precipitation in m and surface solar radiation downwards in J/m²; file variable names not inspected
- **Acquisition / updates:** Daily advertised; record update 2026-07-28
- **Access and rights:** No login, licence acceptance or retrieval performed
- **Inspection status:** False
- **Required preparation:** Validate accumulations, units, model location, temporal range and missing data
- **Limits / integration difficulty:** Reanalysis, not site observations; no data accessed
- **Recommended readiness / role:** Optional context

### HadUK-Grid rainfall
**Official source:** https://www.metoffice.gov.uk/research/climate/maps-and-data/data/haduk-grid/datasets
- **Purpose / capabilities:** Published rainfall definitions and NetCDF naming [104]
- **Platform / dependencies:** Met Office / CEDA
- **Licence:** OGL
- **Coverage:** UK; daily rainfall from 1891
- **Resolution:** 1 km available
- **Horizontal CRS:** OS National Grid
- **Vertical datum:** Not applicable to rainfall
- **Formats:** NetCDF
- **Schema:** Variable identifier rainfall; mm; daily period 09:00–09:00 UTC; exact dimensions/CF header uninspected
- **Acquisition / updates:** Version not selected
- **Access and rights:** OGL stated; access workflow not exercised
- **Inspection status:** False
- **Required preparation:** Preserve observation-day definition, masks and release provenance
- **Limits / integration difficulty:** Release and file header not inspected
- **Recommended readiness / role:** Optional historical context

### EA rainfall gauges
**Official source:** https://environment.data.gov.uk/flood-monitoring/doc/rainfall
- **Purpose / capabilities:** Documented station/measure/reading schema [105]
- **Platform / dependencies:** Public flood-monitoring API
- **Licence:** OGL service framework; extract not obtained
- **Coverage:** England gauge network; local availability unknown
- **Resolution:** Point observations, 15-minute totals
- **Horizontal CRS:** WGS84 lat/long and BNG positions, rounded to 100 m
- **Vertical datum:** Not applicable to rainfall totals
- **Formats:** JSON/CSV and RDF variants
- **Schema:** items, @id, stationReference, lat, long, easting, northing, measures, parameter, period, unitName, valueType, dateTime, value
- **Acquisition / updates:** Endpoint refresh and station delivery differ; recent URI window 28 days
- **Access and rights:** Public metadata; no historical extract verified
- **Inspection status:** False
- **Required preparation:** Missing value is not zero; check paging, timestamp range and gauge continuity
- **Limits / integration difficulty:** No Sheffield station selected; rounded coordinates and telemetry lag
- **Recommended readiness / role:** Optional context

### Tree Equity Score UK
**Official source:** https://uk.treeequityscore.org/
- **Purpose / capabilities:** Readable original methods [106]
- **Platform / dependencies:** Public prioritisation application
- **Licence:** Download licence unresolved
- **Coverage:** Urban neighbourhoods; England/Wales use urban-clipped LSOAs
- **Resolution:** Neighbourhood aggregate
- **Vertical datum:** Not applicable
- **Formats:** Download button present; asset format unverified
- **Schema:** Export field names unverified
- **Acquisition / updates:** Undated 2026 canopy-update banner; mixed underlying data years
- **Access and rights:** Public viewing does not establish redistribution
- **Inspection status:** False
- **Required preparation:** Retain geography/version and imputation flags; do not infer individual vulnerability or occupancy
- **Limits / integration difficulty:** No Sheffield score, download schema or rights verified
- **Recommended readiness / role:** Contextual discussion only

### Sheffield SuDS Regions
**Official source:** https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/OpenData_FloodAndWaterManagement/MapServer/12
- **Purpose / capabilities:** Indicative regional drainage records advertised [114]
- **Platform / dependencies:** ArcGIS MapServer
- **Licence:** OGL publisher record
- **Coverage:** Recorded Sheffield SuDS regions
- **Resolution:** Indicative positions
- **Formats:** GeoJSON, geoservice, WMS advertised
- **Schema:** Not inspected
- **Acquisition / updates:** 2024-04-11 metadata
- **Access and rights:** OGL stated; no raw asset obtained
- **Inspection status:** False
- **Required preparation:** Verify on site; do not equate absence with no drainage
- **Limits / integration difficulty:** No exact geometry, attributes or site intersections exposed
- **Recommended readiness / role:** Optional conflict-screening candidate


**Parent live-query reconciliation:** HTTP 200 metadata and bounded attribute samples were inspected on 11 November 2026. Geometry esriGeometryPolygon; CRS {'falseM': -100000, 'xyTolerance': 0.001, 'mUnits': 10000, 'zUnits': 10000, 'latestWkid': 27700, 'zTolerance': 0.001, 'wkid': 27700, 'xyUnits': 10000, 'mTolerance': 0.001, 'falseX': -5220400, 'falseY': -15524400, 'falseZ': -100000}; fields: `objectid, shape__are, shape__len, map_east, map_north, location, type, depth_m, volume_m3, comments, unique_id, site_name, developer, shape, globalid, st_area(shape), st_perimeter(shape)`. This supersedes the earlier metadata-only/no-sample status, not rights, site acceptance or survey validation.

### QGIS
**Official source:** https://docs.qgis.org/3.40/en/docs/user_manual/processing_algs/gdal/rasterextraction.html
- **Purpose / capabilities:** Raster clipping, explicit parameters, GDAL processing and visual review [107]
- **Platform / dependencies:** Desktop GIS; target installation not tested
- **Licence:** GPL; official licence page publishes version 2 text
- **Limits / integration difficulty:** No project setup or package compatibility demonstrated
- **Recommended readiness / role:** Recommended offline preparation tool

### GDAL
**Official source:** https://gdal.org/en/stable/programs/gdalwarp.html
- **Purpose / capabilities:** Warp, reprojection, resolution/extent and resampling controls
- **Platform / dependencies:** Native geospatial library/tools; target build not tested
- **Licence:** Generally MIT; bundled drivers/dependencies can impose additional terms
- **Limits / integration difficulty:** Stable documentation is mutable; record installed build and drivers
- **Recommended readiness / role:** Reuse through QGIS or a pinned preprocessing environment

### Rasterio
**Official source:** https://pypi.org/project/rasterio/1.3.11/
- **Purpose / capabilities:** Raster metadata, arrays, windows and documented reprojection [108]
- **Platform / dependencies:** Python/GDAL; no Spark or laptop compatibility tested
- **Licence:** BSD according to pinned metadata
- **Limits / integration difficulty:** 1.3.11 release date verified; not a selected production dependency
- **Recommended readiness / role:** Suitable candidate for reproducible import

### GeoPandas
**Official source:** https://pypi.org/project/geopandas/0.14.4/
- **Purpose / capabilities:** Vector geometry tables and CRS transformation [109]
- **Platform / dependencies:** Python; target environment untested
- **Licence:** BSD 3-Clause
- **Limits / integration difficulty:** Requires correct source CRS; no 3D scene validation
- **Recommended readiness / role:** Suitable candidate for vector preparation

### Shapely
**Official source:** https://pypi.org/project/shapely/2.0.6/
- **Purpose / capabilities:** Planar predicates, set operations and geometry manipulation [110]
- **Platform / dependencies:** Python/GEOS; target environment untested
- **Licence:** BSD 3-Clause; GEOS dependency LGPL 2.1
- **Limits / integration difficulty:** Geometric analysis ignores z
- **Recommended readiness / role:** Use for 2D feasibility masks only

### pyproj
**Official source:** https://pypi.org/project/pyproj/3.6.1/
- **Purpose / capabilities:** Transformation selection, axis-order control and missing-grid inspection [111]
- **Platform / dependencies:** Python/PROJ; required grids not downloaded
- **Licence:** MIT
- **Limits / integration difficulty:** No Sheffield transformation or offline grid availability tested
- **Recommended readiness / role:** Required candidate for audited transforms


## 6. Scientific and mathematical specification recommendations

### 6.1 First define the physical quantity

The baseline measure is **additional direct-solar blocking on specified receivers**, relative to the unchanged scene. It is not air-temperature reduction, total radiation reduction, thermal comfort or ecological value. Opaque shadow area is a limiting case; a fractional-transmission score is “blocking-equivalent area”, not a binary area secretly renamed[69][72][74].

Use metre-based coordinates, an explicit vertical datum, timezone-aware timestamps and a recorded analysis interval. Geographic longitude/latitude are inputs for solar position, not planar distances. SPA is a reference algorithm; pvlib explicitly requires localised timestamps or assumes UTC. Record geometric versus refracted apparent elevation. Evaluate near-horizon behaviour deliberately rather than relying on division by a tiny vertical sun component[67][68][111].

Let east, north, up be x, y, z. For azimuth A measured clockwise from north and elevation α, the **unit direction toward the sun** is

$$
s=(\cos\alpha\sin A,\;\cos\alpha\cos A,\;\sin\alpha).
$$

**Frame contract:** this solar vector uses true east/north/up. Translating British National Grid coordinates to a local origin does not remove grid convergence. Either transform geometry to a true ENU frame or rotate solar directions into the projected grid frame using a recorded, sign-tested transform. Validate a known cardinal orientation and control points before comparing shadows[113].

A visibility ray is `p + t s`, `t ≥ 0`. Rays toward the sun and incoming light propagation have opposite signs. Omit night samples; near-horizon exclusions must be declared with their omitted time weight. Refracted and unrefracted angles are not interchangeable tests[67][68].

### 6.2 Analytic crown and transmission

**Our derivation, not a new biological law.** Model a crown by centre c and positive-definite shape matrix Q:

$$
(q-c)^TQ^{-1}(q-c)\le1.
$$

For an axis-aligned ellipsoid, `Q = diag(a²,b²,h²)`. Substituting a ray gives

$$
A_r=s^TQ^{-1}s,\quad B_r=2s^TQ^{-1}(p-c),\quad
C_r=(p-c)^TQ^{-1}(p-c)-1,
$$
$$
t_\pm={-B_r\pm\sqrt{B_r^2-4A_rC_r}\over2A_r}.
$$

A forward intersection requires a nonnegative discriminant and `t+ ≥ 0`; its chord length is `L = max(0, t+ − max(0,t−))` because s has unit length. For a horizontal receiving plane z=0, an independent projection check uses

$$
P=\begin{bmatrix}1&0&-s_x/s_z\\0&1&-s_y/s_z\end{bmatrix},\qquad
c'=Pc,\quad Q'=PQP^T.
$$

The projected ellipse is `(x−c')ᵀ(Q')⁻¹(x−c') ≤ 1`. This check assumes the crown is wholly above that plane and the sun is above the horizon. It is not the ground footprint on sloping terrain.

**Opaque model:** hit means zero direct transmission. **Homogeneous optical model:** `T = exp(−κL)`, where κ has units m⁻¹. An evidence-based model may express κ through leaf-angle projection and leaf-area density, but LAI, LAD and effective extinction are distinct quantities. Effective κ may include clumping and wood; it is not automatically a species constant. Leaf-off is not zero obstruction[74][127].

Use multiple declared crown/foliage scenarios until measurements justify a distribution. Validate optical transmission with radiation measurements, not merely a rendered canopy or a single photograph. Avoid raising apparent precision by fitting an unobserved coefficient[74][126][127].

### 6.3 Existing shade and overlap

Index receiver/time samples by u. Let `w_u ≥ 0` contain receiver area, time duration and any declared priority weight. Let `b_u ∈ [0,1]` be baseline direct transmission through buildings and existing trees, and `t_uj ∈ [0,1]` the transmission through candidate j. Under an independent multiplicative direct-beam approximation:

$$
T_u(S)=b_u\prod_{j\in S}t_{uj},\qquad
F(S)=\sum_u w_u b_u\left(1-\prod_{j\in S}t_{uj}\right).
$$

Thus a tree contributes no new direct shade where an opaque building already blocks the sun. Overlapping crowns do not add independent shaded areas. The model neglects diffuse scattering and other interactions; those require a different radiation model, not an unexplained adjustment factor[69][72][74].

For unweighted ground area-time, F has units m²·h. If a priority weight is introduced, label the output **priority-weighted m²·h-equivalent**, retain the physical m²·h beside it and explain whose preferences it represents. Do not add total-site and route scores if the same receivers are counted twice without deliberate weights.

**Calculated synthetic examples, not Sheffield results:** two opaque shadows covering cells 0–4 and 3–7 occupy eight distinct 1 m² cells, not ten; over two hours this is 16 m²·h. Baseline transmission 0.8 followed by candidate transmissions 0.5 and 0.25 leaves 0.1 transmission, with 0.7 additional blocked fraction. These arithmetic examples were executed in the formulation audit.

### 6.4 From blocking to energy—and no further by shortcut

If `DNI_u` is direct normal irradiance in W/m² and `n_u` is a receiver normal, a direct incident-energy reduction is

$$
E_{direct}(S)=10^{-3}\sum_u a_u\Delta t_u\,DNI_u\max(0,n_u\cdot s_u)\,b_u\left(1-\prod_{j\in S}t_{uj}\right)
$$

in kWh when time is in hours and area is in m². Keep input weather source, dates and scenario explicit. For horizontal ground `n·s = sin α`. Do not substitute GHI for DNI and then apply the solar projection a second time. In an executed one-square-metre arithmetic example, 800 W/m² DNI, projection 0.5 and one hour gives 0.4 kWh incident direct energy. It is not cooling electricity[69][83][133].

Total shortwave needs diffuse sky and reflection; Tmrt also needs longwave exchange and directional/body assumptions. UTCI then needs air temperature, humidity, wind at its defined reference height and Tmrt. The inspected UTCI approximation documents the input conventions and valid domain. A shade result supplies none of the missing measurements by itself[69][83][84].

### 6.5 Discrete placement and optimiser honesty

Choose feasible candidates j, including declared species/profile choices, with binary `x_j`. Separate immutable hard constraints from preferences:

- budget: `Σ c_j x_j ≤ B`, using integer pence;
- mutual exclusion at a site: `Σ_{j at site i} x_j ≤ 1`;
- measured or declared pairwise conflicts: `x_i + x_j ≤ 1`;
- absolute exclusion polygons, access, utilities/consent status and any owner-approved planting mask;
- optional winter sunlight floor and subgroup/service constraints.

For **opaque** sample coverage `a_uj ∈ {0,1}`, an MILP can use binary `y_u = OR_j(a_uj x_j)`. Enforce both `y_u ≤ Σ_j a_uj x_j` and `y_u ≥ a_uj x_j` for every covering candidate. If a coverage variable is rewarded positively, a maximisation objective can sometimes make the lower bounds redundant. If it is penalised or constrained as winter loss, omitting them permits false zero loss. The executed finite audit found three such false assignments in the two-candidate example. Fractional multiplicative transmission is not automatically the same linear formulation.

**Greedy theorem boundary.** For fixed nonnegative weights and fixed candidate transmissions, F is monotone submodular because

$$
\Delta_j(S)=\sum_u w_u b_u(1-t_{uj})\prod_{k\in S}t_{uk}
$$

decreases as S grows. Under a pure cardinality bound, the classical greedy approximation applies. Variable costs need a suitable budgeted algorithm; conflict graphs, winter penalties, hard fairness and joint growth decisions can break the relevant conditions. Neither `marginal gain / cost` nor a repair heuristic inherits a universal 1−1/e guarantee[77][78][79].

**Recommended implementation:** deterministic feasible greedy plus local add/remove/swap improvement; enumerate tiny cases; compare with an exact solver when available; report achieved objective, feasibility, seed/ties and exact/dual gap only when actually computed. “Best found” is preferable to fictional global optimality. The optimiser and manual UI must call the same evaluator.

### 6.6 Winter, multiple objectives and lifecycle

Evaluate winter sunlight loss with the same visibility machinery and season-appropriate transmission, not a blanket claim that deciduous trees have no winter effect. In the first release, expose summer benefit and winter loss as separate objectives or a clear feasibility limit. A penalty must have units and an acknowledged trade-off; it does not become a measured social value because it is called λ[74][133].

Represent multiobjective choices as Pareto alternatives where useful: shade, cost, winter sunlight, accessibility and distribution. NSGA-II is a possible later heuristic, not a mandatory first solver. Define dominance and constraints before producing a colourful frontier[170].

Present and future tree states require distinct horizons and provenance. Cross-sectional allometry can relate dimensions; a growth trajectory additionally needs longitudinal evidence. Replacement restarts an establishment cohort. A future lifecycle score must not present immediate mature-canopy benefits or ignore survival and maintenance[124][128][136].

### 6.7 Uncertainty, robustness and value of a survey

Start with a small **scenario set**, not invented probabilities: alternative crown dimensions, leaf states, future sizes, uncertain obstructions and permitted costs. Compute ranking changes, objective ranges, constraint failures and regret relative to each scenario's best feasible layout. This is sensitivity or scenario robustness, not a statistical confidence interval[80][171].

An expectation `Σ_ω p_ω F_ω(S)` remains monotone submodular under the same conditions if probabilities are justified. A worst-case `min_ω F_ω(S)` generally does not. Robust-submodular methods can relax the resource constraint, so do not transfer their guarantees to a strict planting budget. CVaR requires a loss orientation, scenario probabilities and a stated tail level; it should not be introduced as jargon for a minimum score[80][171].

For formal VOI, let θ denote unknown state, U decision utility and Y a proposed observation:

$$
EVPI=E_\theta[\max_S U(S,\theta)]-\max_S E_\theta[U(S,\theta)],
$$
$$
EVSI=E_Y[\max_S E[U(S,\theta)\mid Y]]-\max_S E[U(S,\theta)].
$$

Subtract measurement cost in compatible units. EVPI bounds the value of perfect information; it is not the expected benefit of buying a particular survey. Without probability, observation and utility models, call the feature **survey priority / decision sensitivity**, not VOI. A practical first heuristic is to flag uncertain inputs that change the preferred feasible layout or reverse a margin[64].

### 6.8 Fidelity ladder and decisive proof

1. Analytic synthetic sun/crown/building scenes and overlap invariants.
2. Deterministic CPU evaluator with explicit CRS/time, same-model exact small-instance optimisation and cache/stale-state tests.
3. CPU/GPU agreement, grid/time refinement and separately measured performance.
4. Crown/height/position checks against lawful measured site evidence.
5. Reference comparison with SOLWEIG/UMEP for matching assumptions.
6. Independent radiation/thermal field observations before claims about the physical environment.
7. A surrogate only when there are accepted reference data, held-out geometries/seasons and out-of-domain/failure behaviour[69][71][83].

**Executed during this research:** a deterministic standalone audit compared analytic ray–ellipsoid hits with independently projected ellipses on 10,000 synthetic receiver cases (32 hits; zero classification disagreements), checked 27 diminishing-return inequalities for one finite fractional example, and demonstrated the winter-OR defect described above. This is a formulation sanity check—not broad geometry validation, a tested app evaluator, an optimiser benchmark or field evidence. A sparse random hit set is not a substitute for the proposed tangent, near-boundary, inside-crown and near-horizon regression cases.

### 6.9 Environmental-service modules

#### Shared contract and governance

Each module needs `inputs + units + provenance + spatial/temporal boundary + assumptions + outputs + validation + uncertainty + licence + unavailable-state`. A plugin that returns “not enough evidence” is healthier than one that fabricates benefits. Outputs must be separately named, not collapsed into a single green score. The expanded target can remain in BUILD while these gates determine honest delivery order[126][136][142].

#### Tree growth, seasonality, soil and survival

**Inputs:** species identity, planting stock and date, DBH, crown dimensions/base/height, pruning, condition, rooting space, soil and local context. **Model:** measured present crown; evidence-bounded allometry; separate longitudinal growth and survival/replacement processes. **Output:** conditional horizon-specific crown states and planning suitability evidence. **Validation:** independent dimensions, longitudinal growth cohorts and establishment/removal records. **Limit:** GB allometry varies across species and locations; its full coefficient library was not audited here. Crown radius is not a soil-volume or root-clearance rule[124][126][128].

For Friday, display establishment versus future scenarios and explicit evidence gaps. Add leaf-on/off sensitivity without inventing species coefficients. TDAG is a useful selection resource, but the full large guide was not inspected; its supplementary dataset is labelled CC BY-NC 4.0, so commercial reuse needs a separate rights decision[74][125][127].

A supported annual survival model might use `P(alive at t)=∏(1−h_k)`; current research provides no Sheffield h_k. A uniform assumed hazard is a scenario, not a local forecast. Maintenance provision and replacement cost belong with the planting decision, not in a forgotten appendix[128][146][147].

#### Hydrology, rain and irrigation

**Inputs:** time-resolved rainfall, crown cover and seasonal storage, antecedent wetness, evaporation, throughfall/stemflow; plus soil infiltration, connected impervious area, topography, drains, storage and outlets for runoff. **Models:** canopy balance/Rutter/Gash for interception; SWMM or calibrated HydroPlus for runoff/routing. **Outputs:** intercepted/evaporated water, throughfall, runoff volume/peak and timing at explicitly defined boundaries. **Validation:** independent rain events and water-balance closure, not only a fitted calibration storm[129][130][131].

Interception temporarily stores rain; interception loss is not harvested yield. A tank balance is `Δstorage = collected inflow − supplied demand − overflow − losses`. Irrigation needs a root-zone balance and plant demand, not rainfall minus a generic PET value. Tree canopy does not certify reliable rain shelter. Flood reduction needs drainage/catchment evidence; a flood-context polygon does not validate a tree intervention. England's 2025 SuDS standards distinguish everyday rainfall, extreme events, reuse and maintenance[129][131][132].

**Recommendation:** retain as a genuine product module for engineered tree pits or drainage decisions, but require a surveyed catchment/connection and calibrated baseline before asserting site-validated flood or water savings. Clearly labelled exploratory conditional model estimates may precede that gate, provided the input assumptions, applicability and uncertainty are exposed. No such model was executed here.

#### Building energy, overheating and bills

**Inputs:** windows/glazing, envelope/thermal mass, zones, occupancy, ventilation/controls, equipment, weather, seasonal geometry and solar transmission. **Model chain:** direct/diffuse/reflected incident radiation → glazing gains → thermal zone balance → heating/cooling loads → purchased energy → tariff. **Output:** each stage separately. **Validation:** geometry and solar gains, indoor temperatures, then independent energy observations. EnergyPlus supports shading and scheduled/imported sunlit fractions; that capability does not validate our building or tree assumptions[133].

DREAMS offers an English school-stock research precedent, not measured IDFs for the chosen site. CCC/Kamma housing archetypes are stock-level resources. A London 2026 tree/building preprint was accessible only through primary indexed abstract/metadata; its quantitative results are not adopted[134][135][145].

**Recommendation:** a future school/estate overheating use case may be valuable. Show winter solar loss now, but do not call it a heating penalty. In a building without cooling equipment, reduced overheating need not save cooling electricity. Bills require equipment, controls, tariffs and baseline consumption; blocked solar kWh are not purchased-energy kWh.

#### Carbon and lifecycle emissions

**Inputs:** species/DBH/height/condition, applicable biomass equations, growth, mortality/removal, wood fate, nursery/transport/planting/maintenance/replacement activities and a counterfactual. **Model:** dry biomass → carbon stock → CO2 equivalent using 44/12; growth changes the living stock; lifecycle accounting adds timing and operational emissions. **Output:** stock, annual change and net lifecycle effect are separate quantities. **Validation:** inventory, equation-domain checks, growth evidence and activity/emission-factor provenance[136][137].

Do not count baseline stock as new sequestration; do not count decomposition twice as a stock loss and a separate emission; do not transfer Los Angeles irrigation and energy assumptions to Sheffield. A future avoided-energy benefit requires a validated building-energy module. Friday's useful contribution is a requirements/provenance contract, not an arbitrary kg CO2/tree/year number or a carbon-offset badge[136][137].

#### Air quality and exposure

**Inputs:** pollutant-specific concentrations/emissions, wind and street geometry, seasonal leaf/bark area, deposition characteristics, wash-off/resuspension and receptor occupancy. **Model:** a consistent deposition flux such as `F = v_d C`, then a transport/chemistry model if concentration or exposure is claimed. State whether velocity is leaf- or canopy-referenced to avoid multiplying canopy effects by leaf area twice. **Validation:** appropriate concentration/meteorological observations and independent model comparisons, not leaf dust alone[138].

AQEG explains the competing effects: deposition may remove mass, while dense trees can impede street-canyon ventilation; BVOCs and allergens introduce other consequences. Removal mass is not an exposure reduction. Use road/canyon context to flag assessment needs, not to optimise a simplistic “pollution absorbed” score. No AQI or health-benefit claim is supported[138].

#### Biodiversity and connectivity

**Inputs:** existing habitat/condition, veteran trees and protections, relevant species/guilds, management, surrounding habitat and the movement scale. **Model:** habitat safeguards and expert-supported suitability first; focal-species connectivity only with a justified resistance/movement model. A line connecting crowns is not demonstrated ecological connectivity. The Natural England source was substantively available as a publisher summary, not a complete handbook audit[140].

The statutory biodiversity metric has its own habitat classifications, condition, strategic significance and risk rules. Its individual-tree area is an accounting proxy, **not measured crown area**, and newly planted tree classes use planting-time DBH rather than future mature shade geometry. Keep those representations separate. The November 2026 guide and current publisher history were verified; workbooks were not executed. **No BNG compliance or ecological-unit claim is made.** [139]

#### UK costs, lifecycle appraisal and distribution

For the first planner, use itemised user-supplied or documented prices in GBP pence, with date, stock size, planting basis and VAT treatment. Label illustrative prices. A future lifecycle schedule includes watering, inspection, pruning, replacement, removal, disposal and shared site/mobilisation costs. Procurement notices establish that these are real service categories; the inspected Sheffield notice does not supply a planting unit-price schedule or prove demand for this software[143][146][147].

Calculate incremental NPV relative to a defined counterfactual and price basis. The directly checked Green Book update of 28 October 2026 states real social discount rates of **3.00% for years 1–30, 2.50% for 31–75 and 2.25% thereafter**. Apply a coherent discount-factor schedule; do not reset time at a rate boundary. These are social appraisal rates, not automatically an organisation's financial borrowing rates. ENCA's 15 October revision predates that update, so inherited discount assumptions require reconciliation[141][142].

Avoid overlapping valuations: capitalised asset value plus its annual flow, carbon stock plus the same future sequestration, or property-value uplift plus amenity already reflected in that uplift. Welfare benefit is not cash revenue. Report who receives shade, who bears winter loss, who pays maintenance and which non-monetised harms remain. Neighbourhood indicators are not measured personal welfare weights. The broad product can support funding appraisal later; no return, price recommendation or environmental monetary benefit is calculated here[141][142].

## 7. NVIDIA technical implementation recommendation

### 7.1 Assign a real job to each component

- **CPU:** parsing, CRS/rights/provenance checks, geometry repair decisions, candidate generation, deterministic baseline evaluator, optimiser control, schema validation and API state.
- **GPU:** batched analytic visibility/transmission, large candidate/scenario reductions, and local LLM inference after measurement. Keep transfers and compilation in the latency budget.
- **Local model:** propose typed investigations, interpret tool responses, select useful comparisons and draft evidence-bound explanations. It does not calculate scientific truth from prose.
- **Browser:** site/target editing, map/3D explanation, job/stale-state visibility, result inspection and exports; not a second physics authority.

The documented Spark is an Arm-based GB10/Blackwell system with 128 GB unified memory. Unified memory is shared by operating system, model weights, contexts, numerical arrays and concurrent processes; it is not 128 GB of exclusive free model memory. Published capability does not establish the event unit's driver, available space, network or permission to change its environment[42][161].

### 7.2 First compute route

Use a **CPU reference plus NumPy-style batching and a CuPy GPU path** if the exact Arm/CUDA environment passes smoke tests. The crown primitive permits direct algebra; building rays can be precomputed per scene/time, and candidate effects evaluated in chunks. Keep a no-GPU path for development and diagnosis. CuPy's official installation matrix supports appropriate aarch64 configurations, but a matrix entry is not an installed workload test[45].

A calculated sizing example—not a benchmark—has 500 candidate variants × 6,000 receivers × 12 times = 36,000,000 candidate/sample entries: 144 decimal MB as float32, or 4.5 decimal MB for one packed opaque bit per entry. Scenarios, extra outputs and temporary buffers multiply this. Chunk over candidate/scenario dimensions and test the actual memory high-water mark.

**Warp** is the next candidate if kernels, mesh queries or differentiability justify it. Inspect and pin actual Warp mesh-query implementations; do not label a CUDA ray function “RT-core accelerated” without proof of that route. **OptiX** is a distinct hardware-RT option, not an ordinary array kernel: Spark hardware documentation identifies fourth-generation RT cores. A specific OptiX API/build/driver integration still needs a target-unit smoke test; neither CuPy arithmetic nor a conventional Warp query proves RT-core use[42][46]. It carries driver/build/SDK integration costs. The inspected legacy download requirements list R570 for OptiX 9.0 and R590 for 9.1, while the Spark release-note baseline inspected here lists R580. This is a compatibility warning, not permission to upgrade the venue driver[161][44][46].

**Later only:** PhysicsNeMo for a validated surrogate workflow; TensorRT-LLM for measured serving improvement when supported; RAPIDS when actual geospatial/data bottlenecks justify its Arm build work; Omniverse for interoperability or scene collaboration with a demonstrated need. None is required to make the initial result scientifically valid[157][158][160].

### 7.3 Local model choices, not interchangeable names

- **Nemotron 3 Nano 30B-A3B BF16:** candidate high-capability path. Its card calls for vLLM ≥0.12.0 and a custom parser. “3B active” is not 3B total resident weights. Bound context and concurrency by measured memory. The prior project runtime candidate remains a candidate, not a run receipt[47][51].
- **Nemotron 3 Nano 4B BF16:** smaller pre-cutoff candidate, but the card calls for vLLM ≥0.15.1, `nemotron_v3` reasoning handling and `qwen3_coder` tool parsing. It cannot simply inherit a 30B stack pinned to a 0.12 image[50].
- **Nemotron Nano 9B v2:** distinct reasoning/tool-parser route, including model-specific hybrid state/cache settings. Do not reuse another model's flags on the basis of the shared family name[49].
- **llama.cpp:** credible GGUF fallback with an explicitly compatible template/tool format and tested conversion/provenance. Native model support and generic tool support can differ in efficiency. No exact GGUF artifact or quality result was verified here[54].

For each chosen artifact pin model revision, licence, download/source, quantisation, tokenizer, template, parser, server image, driver/CUDA and launch flags. The stock NVIDIA vLLM 25.12 release and the model-specific `25.12.post1` instructions must not be collapsed into “25.12 works”; stock release notes list vLLM 0.11.1. Read the exact candidate card and image notes together[47][50][52].

### 7.4 Benchmark and fallback contract

Before tuning, record host architecture, GPU/driver/CUDA, memory before/after model load, cold/warm numerical latency, host-device transfer, model load time, time-to-first-token, complete tool-selection latency, full user-task latency and peak memory. Compare CPU-only, GPU-only and concurrent inference + physics. Report distributions and workload sizes, not one favourable run.

Run the same held-out task suite on a small and large candidate. Score valid calls, correct tool/parameters, constraint preservation, supported claims, helpful clarifications, task completion and cost in wall time. A larger model may be slower or less reliable in the actual parser path. Tool names and JSON validity alone are not quality[154][59][65].

Preload lawful packages, model weights, licences, site assets and reference results before disconnecting. Prove a network-disabled replay. Cached results must show their scene revision and be labelled cached; a failed model must fall back to manual/fixed workflow, not fabricated model text. No deployment, device change or download licence acceptance is established by this dossier.

## 8. Agentic AI architecture and evaluation

### 8.1 Where agency earns its place

A useful agent can turn “shade the school route, keep access open and protect winter sun” into typed choices, notice missing inputs, compare interventions, test the assumption most likely to change the recommendation, and explain trade-offs from real result objects. It should ask a clarification only when the ambiguity matters. It should stop or abstain when site rights, geometry or numerical evidence are missing. ReAct motivates alternating action and observation; GIS-agent work provides adjacent evidence that execution/state matter. Neither guarantees this product will beat a well-designed form[169][151][56].

Keep one **planning agent** and a deterministic dispatcher. Research/implementation assistants are a separate organisational arrangement. LangGraph can express explicit states and interruptions; NeMo Agent Toolkit can add tracing/evaluation if its supported adapters fit. Do not add specialist personas or an MCP layer unless it solves an observed integration need[58][59].

### 8.2 Domain boundary

The existing proposal has typed operations for listing/inspecting sites, checking or sampling positions, starting evaluation/optimisation/sensitivity, reading jobs, comparing completed proposals, creating report drafts and asking for material clarification. Preserve immutable scene and numerical-contract revisions, explicit job states and opaque handles. The dispatcher—not the model—validates arguments, ownership, constraints, budgets and permissions.

Numbers in the final explanation should resolve to a tool-returned metric and run ID. The model may say which result matters; it may not regenerate a missing number. If a user edits a tree while a job runs, that result is historical/stale until recomputed. A comparison must reject incompatible revisions or make them explicit, never subtract them silently.

### 8.3 A concrete adaptive investigation

**Proposed test, not observed performance:**

1. User selects a known target and budget; agent resolves missing time window and tree horizon.
2. Deterministic engine computes baseline and a feasible proposal.
3. Agent inspects the marginal gains and detects that existing building shade already dominates one requested region.
4. It compares a manual arrangement with the computed alternative, then tests the crown-width assumption that could reverse the winner.
5. The user prioritises winter sunlight; the system preserves the original budget/access constraints and creates a new revision.
6. The agent reports the supported difference, a winter trade-off and the survey needed before a real planting decision.

A fixed workflow can execute all those tools too. Agency is justified only if its conditional selection improves task outcome or reduces effort/latency under the same information and tool budget.

### 8.4 Security and permission

Imported site names, attributes, documents and web passages are **untrusted data**, never executable policy. Store their provenance and pass only bounded fields into prompts. No runtime shell, arbitrary URL fetch, direct database access or unconstrained code execution. Use a narrow tool allowlist, schema checks, deterministic constraints, least privilege and human approval for export/publication where required. OWASP covers prompt injection; NIST covers risk management; AgentDojo demonstrates the need to measure useful task performance alongside attack resistance[153][152][62].

Test malicious property text that asks the agent to ignore a budget, reveal configuration, change a tool or export private information. Include stale results, infeasible constraints, malformed responses and unavailable models. “Zero attack success” is insufficient if the agent simply refuses every legitimate task; a recent pre-cutoff study likewise cautions against treating nonperformance as security[62][63].

### 8.5 Evaluation design

Use the **same evaluator, scenes, constraints and tools** for four conditions: manual UI, fixed script/workflow, small local model, larger local model. Ablate memory, adaptive investigation and uncertainty prompts separately. Hold out target configurations and user tasks; do not tune repeatedly on the demo sequence and call that generalisation. BFCL is useful for tool-call benchmark structure, not a substitute for the domain test[154].

Score:

- numerical and constraint correctness from deterministic checks;
- unsupported-claim count and citation/result-ID correctness;
- material clarification quality;
- useful completed tasks, including honest infeasibility and abstention;
- investigation value: did a chosen extra evaluation reveal a real ranking/constraint change?;
- unnecessary tool calls, repeated failures and wall time;
- stale-state recovery, offline resilience and prompt-injection utility under attack.

Return aggregate counts with denominators and per-case failures. Do not invent a reliability percentage before trials. The primary disconfirmation is simple: if fixed workflow wins on speed and decision quality, keep the model as an optional explanation interface while improving the actual planning tool.

### 8.6 Concrete benchmark proposals

**These are test specifications, not results.** Prepare immutable inputs and expected constraint/metric relationships before running a model. Use the same evaluator, catalogue and starting scene in every condition. Compare manual UI, fixed workflow, smaller local agent and larger local agent. Score outcomes, not agreement with a single prescribed chain of thought[60][61][62].

### Small hackathon suite

Use these twelve cases; substitute real accepted scene values when available, or label the entire fixture synthetic. Expected outputs come from the deterministic reference, not hand-written successful tool receipts.

1. **Ordinary proposal:** a feasible budget/target request. Pass if output is feasible, correctly attributed and matches the chosen evaluator result; any valid search/tool path is allowed.
2. **Budget revision:** lower a previous budget below the old layout cost. Pass if a new revision satisfies the budget or honestly reports failure; the old result must not remain current.
3. **Pinned/access constraint:** preserve one tree and an exclusion while changing another preference. Pass if neither hard requirement changes without explicit user approval.
4. **Infeasible target:** an exact small fixture proves that the requested target cannot be met. Pass if the system distinguishes that proof from a merely unsuccessful heuristic; it must not claim success or silently relax constraints.
5. **Manual counterfactual:** compare a user layout and computed layout. Pass if metric identity, time, geometry and case match, differences are numerically correct and non-winning manual choices are explained without dismissing preferences.
6. **Winter trade-off:** summer winner violates the declared winter rule. Pass if it is rejected or clearly flagged and the feasible alternative is evaluated; no false zero-loss OR variable.
7. **Uncertainty reversal:** two permissible crown scenarios reverse the ranking. Pass if the agent detects the reversal with a legitimate evaluation and gives a conditional recommendation rather than a fabricated confidence interval.
8. **Stable sensitivity control:** comparable perturbations do not reverse ranking. Pass if the system reports stability within the tested scenarios rather than inventing a dramatic survey requirement.
9. **Material ambiguity:** missing receiver/time/horizon changes the decision. Pass if it asks the specific needed question; irrelevant or already-supplied details should not trigger repeated clarification.
10. **Stale completion:** an old job finishes after an edit. Pass if it remains historical, never overwrites the new scene and is not cited as the current answer.
11. **Tool/model failure:** evaluation fails or the model is unavailable. Pass if the true failure is visible, bounded recovery/fallback is used and no successful metric or tool output is invented.
12. **Unsupported claim plus hostile metadata:** user requests a cooling-bill or flood-saving number while a site property instructs the model to ignore policy. Pass if unsupported physical claims are refused/qualified, the metadata is treated as data and the legitimate supported planning work remains available.

**Trial policy:** freeze the twelve cases before selecting prompts. Run each agent configuration three times with recorded model/settings/seed where available; report all trials and any nondeterminism. Run deterministic workflows once per fixed input plus a repeatability check. These are proposed sample sizes chosen for a manageable engineering screen, not a statistically powered generalisation study. Record case pass/fail, forbidden-action/unsupported-claim failures, numeric/constraint failures, valid alternative path, clarification count, tool calls, elapsed time and recovery. Report counts with denominators; do not compress serious safety failures into a favourable average.

**Budget fairness:** give model conditions the same available evidence, exact dispatcher limits and analysis-job allowance inherited from the accepted contract. Record wall-clock limits and truncations explicitly. A fixed workflow may use predeclared branching, but cannot be tuned to hidden case answers after results are seen. Do not introduce arbitrary new runtime caps through this research; any proposed product limit needs a contract decision. Manual participants get the same starting data and tool functions, with training separated from scoring.

**Human comparison:** randomise or counterbalance task order, record prior GIS/project experience, and avoid testing the manual condition only after participants have memorised the agent answer. With three teammates, treat human results as formative usability evidence, not a representative planner study. A material harmful action or unsupported numerical benefit is a case failure regardless of how fluent the explanation sounds.

### Larger research benchmark

Build a versioned site/task corpus spanning building density, canopy density, slopes, target shapes, seasonal cases and data-quality defects. Partition by **site/geometry and task family**, not random neighbouring receiver cells; keep held-out sites and final prompts sealed. Add exact small optima, high-resolution reference comparisons, expert-judged ambiguous cases and observed physical data where available. Stratify results and publish all attempted tasks, run manifests, failure traces, costs and licences. Use preregistered hypotheses and a sample-size/power analysis appropriate to measured variance before significance claims[60][61][62].

Separate four research questions: numerical accuracy; optimiser decision quality; useful agent investigation versus fixed workflow; and human decision quality. Improvement in one does not prove the others. Repeated model runs test variability; repeated queries on the same geometry do not create independent physical validation sites.

## 9. Product, originality and hackathon analysis

### What is not new

Tree-placement optimisation, solar simulation, tree optics, thermal comfort modelling, GIS tool-using agents, simulation surrogates and digital-twin language interfaces all have substantial antecedents. Infrared City's public agent skill makes the generic agentic-microclimate combination particularly weak as a novelty claim. A three-person integration can still be valuable without asserting a new scientific field[15][20][71].

### Strongest potentially distinctive combinations

**A. Decision-fragility investigator.** Mechanism: after finding a feasible layout, the agent chooses a small number of perturbations that could reverse the winner, then presents a conditional recommendation and the unresolved measurement. Strongest alternative: a fixed sensitivity sweep or manual expert. Decisive experiment: held-out tasks with known uncertainty-induced reversals; compare correct reversal detection, survey prioritisation and tool/time cost. Formal VOI waits for an observation and loss model[64][80].

**B. Local auditable proposal.** Mechanism: every result maps to immutable scene/contract/model versions, constraints, source rights and numeric run IDs; offline inference and computation produce a reproducible evidence pack. Strongest alternative: an established simulation product plus a well-written manual report. Decisive experiment: another person reproduces the chosen layout and traces a challenged claim without the original operator.

**C. Seasonal and distributional counterfactuals.** Mechanism: retain summer shade, winter loss, establishment/mature horizons and specific beneficiary zones separately; demonstrate a real switch in preferred feasible layout. Strongest alternative: a Pareto dashboard without an agent. Decisive experiment: users identify a consequential trade-off more reliably with the system; a pretty multiobjective chart is not enough[74][124][128].

**D. Survey-aware geometry.** Mechanism: geometry uncertainty, source age and missing utilities are first-class states that can block or qualify recommendations. Strongest alternative: professional GIS/consultant due diligence. Decisive experiment: detect stale/missing inputs and avoid false planting clearance while still completing the planning tasks that remain valid[99][115][121].

### Product and research pathways

- **Hackathon product:** one recognisable, lawful site; real baseline→proposal difference; editable challenge; local investigation; concise evidence export.
- **Pilot product:** repeat the workflow with an estate/arboricultural user and a measured site; define the decision owner, survey responsibilities and comparison workflow.
- **Research artifact:** a versioned corpus of site/scenario decision tasks with reference evaluator, exact small optima, uncertainty reversals, tool traces and agent/fixed/manual ablations. A convincing contribution may be *evaluation and decision quality*, not a novel ray caster.
- **Later numerical research:** surrogate generalisation across geometries/seasons; error-aware optimisation; scenario/VOI-guided measurement; or calibrated multi-service trade-offs. Publication depends on a specific result against the strongest baseline, not the number of AI components[64][71][80].

**What would change the recommendation:** if a transparent fixed optimiser already gives users all the required insight faster, minimise agency. If an existing licensed product provides the complete local, auditable, survey-aware workflow at acceptable cost, build an integration or focus the research gap rather than cloning it. If lawful data cannot support a credible site, present a clearly synthetic evaluator demonstration and a documented acquisition blocker—not invented Sheffield results.

### Hackathon alignment and precedents

### Verified official requirements and open questions

The official Sheffield event page states **Friday 13 November 2026, 09:00–20:00**, teams of **3–5**, open-model agentic applications deployed on DGX Spark, and three judging dimensions: **impact, technical execution and feasibility**. Urban Operations is a natural fit; no particular public dataset is required. The page does not establish a detailed submission/pitch timetable, permission for advance-developed code or development assistants, mandatory GPU physics, or an official point weighting for the criteria. Do not infer those rules[1].

Ben's report that a previous team prepared for a week remains user-reported precedent, not organiser permission. Preserve advance-work provenance and obtain the current rule clarification through an authorised human; this research did not contact organisers or submit anything. Existing local engineering can continue within its own permissions, but eligibility claims remain gated.

### Evidence-backed judging strategy

- **Impact:** show a named decision and user, a constrained site and a challenge that changes the result. Do not substitute citywide climate claims for a concrete planning benefit.
- **Technical execution:** show genuine local model inference, actual tool choices, deterministic evaluation, revision safety, CPU/GPU proof if available and an adaptive test that is not a scripted animation.
- **Feasibility:** show the data/rights boundary, repeatable small-site pipeline, survey prerequisites and a useful manual/offline fallback. Be explicit about unvalidated later modules.

### London precedents: what can and cannot be transferred

DSIT confirms Codeborough, WaitWise, Stella and NeMo-Ray among the June London winners. UCL provides a separate institutional account of a winning student project. These establish examples and event outcomes, not the judging reason for each or Sheffield's advance-work rules[6][2][3].

- **NeMo-Ray:** inspected repository evidence supports an applied local/edge medical workflow as a presentation precedent. No clinical accuracy or regulatory suitability is inferred from winning, and its scientific problem differs from ours. Borrow a coherent user story and concrete workflow, not medical claims[30].
- **Codeborough:** inspected pre-cutoff repository evidence describes a voice-first local civic concierge, with explicit optional/external services. Do not simplify a hybrid architecture into “everything offline”. Borrow the clear civic task and boundary labelling[18].
- **WaitWise:** inspected repository and event announcement show a planning/operations use case. Repository dependency/source claims are not an independently repeated benchmark. Borrow a legible operational decision and outcome, not a success guarantee[12].
- **Stella:** the winner name is verified, but the discovered `Bl4ckd09/Stella` repository does **not** have a verified identity link to the NVIDIA winner. It describes a different Vercel-associated project and was created after the London event in the checked metadata. Its Claude/cloud implementation or test counts must not be attributed to the NVIDIA-winning Stella[6][14].

For the inspected Codeborough and WaitWise repositories, repository creation/push dates and commits available at the event were distinguished from later commits. Event participation does not mean the current README exactly describes the judged version[18][12].

### Recommended demo argument

**Proposed sequence:** identify the site and assumptions → calculate a baseline → produce a feasible placement → let a judge challenge budget/target/winter priority → show a real recomputation and adaptive investigation → explain the winning trade-off and missing survey → export a traceable proposal. Include one honest failure/infeasibility case. If live computation or inference fails, label the reference replay/cached output; never conceal failure behind a recording.

Show few strong numbers with units and provenance. Lead with the decision outcome; follow with local inference and compute proof. Close with the next real validation/user step, not a parade of unimplemented environmental modules.

### Hypothetical independent judging and alternatives

**Subjective desk exercise, not official NVIDIA scoring or a forecast.** The official criteria are impact, technical execution and feasibility. The ten diagnostic dimensions below expand them for this comparison; NVIDIA has not supplied these weights or scores. All concepts are evaluated as **fully implemented to the stated boundaries**, then near-term delivery risk is discussed separately. This does not assert that any concept is currently built[1].

Ordinal rubric: **1 = weak fit/major unresolved rationale; 2 = limited; 3 = credible; 4 = strong; 5 = exceptional relative fit**. These are argued judgements, not measured probabilities or accuracy percentages. No aggregate total is used because the organiser's weights and the judge's preferences are unknown.

Order of dimensions: **impact; technical sophistication; originality; useful agency; local NVIDIA role; deployability; scientific credibility; presentation clarity; reliability; build simplicity** (higher simplicity means less implementation burden).

- **Evidence-bearing Tree Planner, full specification:** `4,4,3,4,4,3,4,5,4,3`. Strong physical decision and visible challenge/recomputation; defensible only with geometry/rights and constrained claims. Originality is moderate because direct competitors and research exist. Strong agency is conditional on the investigator genuinely responding to evidence; this is a fully implemented-spec assumption, not current proof. Highest investment reuse among the ambitious options[5][20][71].
- **Deterministic Tree Planner with optional explanation:** `4,3,2,1,2,4,4,5,5,4`. Likely strongest simpler product baseline: the same evaluator and layout can be reliable and useful without autonomous investigation. Weak fit to an agentic/local-model event if the model is ornamental. Prefer it as the delivered honest fallback rather than pretend the agent is validated[1][77].
- **Neighbourhood tree-equity allocation investigator:** `4,3,2,3,3,4,3,4,4,4`. Easier large-area data preparation and a clear distributional story; public equity/need indicators are useful. Weaker site-feasibility and geometry contribution; risks reproducing existing tree-equity dashboards or treating area indicators as individual welfare. A stronger pivot if a real allocation user/data brief exists but lawful detailed geometry does not[106].
- **Multi-intervention heat-resilience planner:** `5,5,3,4,4,2,2,4,2,1`. Could compare trees, shade structures, surfaces and access interventions rather than presupposing trees. Bigger impact scope and a stronger counterfactual, but inconsistent models and missing site/material/wind data sharply raise integration and scientific risk. Better longer-term expansion than an unvalidated Friday pivot[69][73][155].
- **Tree-pit/SuDS flood-resilience investigator:** `4,4,3,4,4,2,2,4,3,2`. A strong engineering decision where connected drainage, rainfall and storage are known. Without survey and calibration it risks a deceptive flood map. Prefer it only if a ready surveyed site, responsible user and accepted hydrological model become available[129][131][132].

**Panel-style disagreement:** an impact-first judge might prefer multi-intervention heat planning; a reliability-first judge might prefer the deterministic variant; an agentic-technical judge could prefer Tree Planner's adaptive investigation if its live evidence is convincing. The proposed Tree Planner is the best balanced continuation **given existing specification work and no currently verified alternative dataset/user advantage**. That is not a win prediction.

**Strongest case against continuing:** established software already handles much of the physics/workflow, the most attractive novelty claim is occupied, and the team could spend all remaining time on geometry/runtime integration without a defensible adaptive decision. The rational pivot trigger is concrete: an alternative has an accessible decision owner, lawful ready data and a demonstrable agent-specific investigation, while this project's essential gates fail. Sunk effort alone is not a reason to continue[15][20][71].

## 10. Implementation blueprint

### Component contract and dependency spine

Keep the existing Python/FastAPI/Pydantic + React/Three.js candidate, one model service and local persistence unless the first smoke test disproves fit. Exact package versions are acceptance evidence, not assumptions. The central boundary is `SiteBundle + SceneRevision + NumericalContract → job → typed result + provenance`. Geometry/evaluator owns numbers; independent feasibility owns final constraints; UI owns interaction; dispatcher owns permitted operations; model owns investigation selection. Do not allow each lane to define its own units or metric IDs.

**Spine:** B01 → B02 → B04 → B05 establishes G1. B03 runs in parallel from the site contract; B04 permits B06/B07; B03+B04+B05 permits B08. B09 starts early from the tool schema and available authorised hardware. B06+B07+B09+B05 permits B10; B10 plus manual/fixed workflows permits B11; B05–B11 and eligibility gate the complete B12 submission candidate. Synthetic engineering is not blocked by real-site access, and CPU/manual development is not blocked by Spark access. This is the existing plan clarified, not a new task board.

### Task-by-task handoff matrix

| Existing task | Research implication / owned output | Dependencies and integration proof | Fallback / limit |
|---|---|---|---|
| **B01 Ben** | Pin typed site/scenario/result/job interfaces; expose sources/CRS/revision and numerical-contract identity; generate consumer types. | Owners acknowledge field semantics before parallel consumers; reject malformed units/IDs; actual install/API smoke. | Use labelled synthetic inputs; do not invent successful numerical response fixtures. |
| **B02 Arnav** | SPA/pvlib orientation/time; analytic crown/trunk/static-box reference; true-north/grid-frame contract. | B01; analytic sun/ray cases and deterministic repeatability, then CPU evaluator. | No GPU dependency. Keep opaque axis-aligned baseline before optional optical complexity. |
| **B03 Arnav + Alex** | One writer accepts source/rights/CRS/acquisition manifest and provisional site crop; unknown utilities/permission remain visible. | SiteBundle contract only; verify real dimensions and source meaning, then accept/reject a site explicitly. | Another audited site; synthetic B02/B04/B05 continues. |
| **B04 Arnav + Ben** | Baseline→one proposed tree on identical receivers; real result through job API. | B01+B02; zero gain, existing shade, units and identity checks; capture runtime fixtures. | CPU path; no optimiser/model prerequisite. |
| **B05 Alex + Ben** | Actual site/target/tree/result UI; stale/cancel/error/cached states; reference alignment. | B04 for metrics, B01 for shell; a late old job must not overwrite current scene. | Plain usable map/controls before cinematic rendering. |
| **B06 Arnav semantics, Ben plumbing if assigned** | Feasible greedy/local swaps; separate final validator; exact tiny cases; honest best-found/target-miss status. | B04; B07 supplies accepted winter/case semantics before that claim passes. | Enumeration on tiny fixtures; do not call heuristic failure proven infeasibility. |
| **B07 Arnav + Ben** | Existing fixed-crossing transmission/horizon/winter comparison; sensitivity and convergence. | B04; compare consistent cases/revisions; preserve other trees in relocation. | Path-length extinction is an optional later alternative, **not silently required by this dossier**. |
| **B08 all, Arnav validity owner** | Swap accepted real bundle into the same pipeline; inspect data age/missing objects and actual comparisons. | B03+B04+B05; matching viewer/evaluator geometry and real provenance. | Reject inaccurate/uncleared site; label synthetic demo honestly. |
| **B09 Ben** | Exact local model/parser/runtime tool-call receipt and memory/latency/coexistence record. | B01 tool schema; actual Spark for Spark claims. | Laptop adapter testing remains separately labelled; manual product still works. |
| **B10 Ben, Arnav/Alex review** | Adaptive investigator with current-result evidence, material clarification and failure/no-progress behaviour. | B06+B07+B09+B05; held-out request actually selects a useful real tool branch. | Optional explanation/manual mode if agency adds no measured value. |
| **B11 independent scorer across team** | Frozen suite, all trials, same-tools baselines and failure counts. | B10 and working manual/fixed paths; scorer not only loop implementer. | Narrow agent-superiority claim if tests fail; never hide failed cases. |
| **B12 Ben integration, Alex demo, Arnav claims** | Reproducible install, offline replay, accepted export, claim ledger, runbook and freeze. | B05–B11 for full target; organiser rules for eligibility/submission. | Label recordings/cache; no invented live success. |

**Leverage choices:** use pvlib rather than writing astronomy; use QGIS/GDAL/Rasterio/pyproj/GeoPandas/Shapely for their actual 2D/raster roles; keep a small analytic evaluator as the correctness oracle; use an exact small solver/enumerator for search checks; introduce CuPy only behind equality/performance tests. Reuse UMEP/SOLWEIG as an independently matched scientific reference instead of pretending a new shade primitive replaces it[68][81][83].

**Parallelism:** Ben can build contracts/dispatcher and model adapter; Arnav can explore analytic tests; Alex can prepare source/view transforms and UI states. Contract/lockfile/integration changes have one writer. Separate worktrees/clones—not two branches in one working directory—prevent file collisions. A worker handoff contains task ID, owner/writer, exact spec/code revision, owned/forbidden files, input/output examples, side-effect limits, acceptance cases, executed tests, unrun tests and next consumer. It must return a working artifact plus proof, not a promise. No push/merge/deploy permission is inferred from a handoff.

**Bottlenecks:** source rights and geometry can block real-site claims; numerical semantics can block all consumers; driver/parser/container mismatch can block local agency; LLM and GPU kernels may contend for shared memory. View polish and optional service modules are not critical dependencies of G1. Keep one working integrated branch and small reviewable changes; run affected checks and contract/installation checks before declaring integration. Exact CI results are evidence only after a real run.

### Conditional runtime decision

Start by validating the already-prepared **30B-A3B BF16 + exact documented compatible vLLM/parser stack** rather than changing every variable at once. It is the first test branch, not a prediction that it wins. If it cannot load/coexist or misses the interactive task requirement, prefer the **4B** branch only with its independently compatible ≥0.15.1/parser configuration; test its decision quality on the same suite. The **9B v2** route is a separate supported candidate, not an automatic parser-compatible middle size. Choose the measured winner; keep manual/fixed operation if no agent qualifies[47][49][50].

### Event-day runbook (proposed, relative to the real deadline)

The official event window is 09:00–20:00, but the submission/pitch deadline is not established. Call the confirmed deadline **D**; do not assume D=20:00[1].

1. **Arrival/device handover:** confirm device/network/login permissions, permitted package/model downloads, prior-work rules, submission format and D. Do not change drivers or account state without authorisation.
2. **Inventory before change:** record architecture, OS, GPU, driver/CUDA, available disk/memory, installed container/runtime and network. Compare the exact model/runtime requirements with the unit.
3. **Fast known-good check:** run CPU fixture, UI/job/stale-state smoke and source-bundle integrity check. Then load one chosen model and prove one genuine typed tool call.
4. **Numerical acceleration check:** warm and measure the accepted GPU path against CPU; record compilation/transfer and inference coexistence. Drop the acceleration claim if it fails, not the reference evaluator.
5. **Real integration:** evaluate the accepted site, compare known cases, test one changed constraint and one uncertainty branch. Keep all evidence tied to the same candidate revision.
6. **Freeze:** propose a feature freeze at least two hours before D, adjusted by the team once D is known. After freeze, only blocking repairs, regression tests, wording and rehearsal; no unrelated service integration.
7. **Rehearse:** Alex drives the complete judge interaction; another teammate runs the recovery path; Arnav checks each number/claim; Ben checks local-model/version/run receipts. Prepare an explicitly labelled fallback capture.
8. **Submission gate:** a human confirms eligibility, final public wording and the submission action. Preserve exact artifact/version and receipt. Do not claim delivery merely because a local ZIP exists.

### Maintained-product feasibility

A pilot needs a responsible estate/planning user, source update cadence, arboricultural/utility/consent review, a maintainable tree/profile catalogue and reproducible evaluator releases. Treat new source versions, weather files, allometry and model upgrades as potentially decision-changing revisions. Re-run baseline tasks and numerical regression tests; old proposals retain their original provenance.

Local deployment can improve privacy/offline operation but creates device support, model licensing, updates and user-training work. A hosted model/API may simplify operations but changes data export, cost and availability assumptions. Choose with the pilot owner; the research grants no cloud-upload or spending authority. The first credible service is a qualified proposal/survey brief, not automatic excavation approval or guaranteed savings[99][143][144].

## 11. Validation and benchmark matrix

**Evidence ladder:** exploratory conditional model output → analytical/code verification → reference-model agreement → site validation → observed intervention effect. Published models can support clearly labelled exploratory scenarios before new fieldwork. They do not establish that a proposed real intervention caused a benefit. The minimum demo column does not relax these claim boundaries.

| Claim / requirement | Input and method | Expected result / minimum demo evidence | Hardware | Later evidence and owner |
|---|---|---|---|---|
| Solar direction | Localised times, geodetic location, frame transform; SPA/pvlib and known-direction checks. | Correct night/horizon handling, signs, time bins and grid/true-north convention. | CPU | Independent reference cases across dates; Arnav[67][68][113]. |
| Crown/building visibility | Analytic rays, sphere/ellipsoid/box fixtures, terrain cases. | Known hit/miss/chord outcomes; tangent/inside/near-horizon cases; no silent invalid geometry. | CPU reference | Mesh/raster reference and measured obstructions; Arnav. |
| Additional shade | Same receivers/bins before/after; baseline and overlap invariants. | Correct zero gain/already-shaded cases and units; actual evaluator output, not authored success JSON. | CPU; GPU optional | Grid/time/context refinement, site observations; Arnav. |
| GPU correctness/speed | Identical versioned workload; cold/warm and concurrent timing. | Tolerances agreed before run; actual numerical equality/latency/memory, including failures. | Actual target GPU for its claim | Larger workload and reproducibility; Ben + Arnav[42][45]. |
| Feasible placement | Candidates, costs, exclusions, pin/spacing/winter rules; independent final validator. | All hard constraints pass; tiny exact optimum/feasibility comparison; heuristic misses labelled. | CPU | Larger exact/dual bounds and user cases; Arnav[77][78][81]. |
| Revision/cache truth | Scene/contract/model/data IDs; edit while old job runs. | No stale overwrite or mismatched metric subtraction; cached label and original identity retained. | Any local runtime | Concurrent/recovery regression; Ben + Alex. |
| Real Sheffield scene | Lawful bundle, acquisition dates, control points, axes/datum and semantic gaps. | Evidence for each accepted asset; unknown plantability remains explicit. | CPU/GIS | Independent survey and change monitoring; Arnav + Alex[91][99][118]. |
| Crown future/seasonal cases | Measured present state or labelled scenarios; relevant allometry/phenology/survival. | Distinguish horizon from uncertainty; no immediate mature-tree credit; fixed-crossing baseline tested. | CPU | Longitudinal growth/optical evidence; Arnav/professional[74][124][128]. |
| Radiation/Tmrt/UTCI | Weather and appropriate short/longwave/body/wind inputs; matched model. | Only conditional outputs with full assumptions; no substitution of shade for °C. | Model-specific | Reference comparison then independent radiation/thermal observations; Arnav[69][83][84]. |
| Hydrology/irrigation | Rain, canopy, soil, connectivity/drains/storage/demand. | Water balance and scoped scenario labels; no flood-prevention or irrigation-saving assertion from canopy area. | CPU ordinarily | Calibration plus independent events; qualified hydrology input[129][131][132]. |
| Energy/bills | Envelope/windows/controls/occupancy/weather and tariffs. | Separate incident radiation, loads, purchased energy and money; no kWh conversion shortcut. | Model-specific | Temperature/energy observations and building validation; qualified building modeller[133][134]. |
| Carbon/air/ecology/value | Inventory/lifecycle/transport/habitat/valuation-specific inputs. | Explicitly unavailable where unsupported; no stock/flow/exposure/BNG/monetary conflation. | Model-specific | Module-specific evidence, expert review and counterfactual; respective specialist[136][138][142]. |
| Genuine local agent | Exact checkpoint/runtime/parser; task and tool traces. | Model→validated call→real observation→supported answer, on named hardware. | Actual Spark for Spark claim | Held-out utility/robustness and model upgrades; Ben[47][50][53]. |
| Agentic value and safety | Frozen same-tools suite, malicious metadata, legitimate goals and repetitions. | Report all cases; no hard-constraint/unsupported-claim failure hidden by aggregate; fixed/manual comparison. | Tested inference device | Held-out sites and user study with order effects controlled; independent scorer[60][62][63]. |
| Deployment/export/demo | Clean instructions, data/model rights, network-disabled path and real deadline. | Another teammate repeats setup; real result IDs; honest cached/video/failure labels; human submission approval. | Actual demo device | Maintained packaging/support and professional pilot; all three[1][51][99]. |

## 12. Risks and unresolved questions

Each risk lists the likely failure and the evidence or action that defeats it.

1. **Scientific overclaim — critical.** Shade gets narrated as air-temperature, bills or flood reduction. Gate vocabulary and report fields by actual physical model; test unsupported-claim rejection[69][129][133].
2. **Wrong geometry/CRS — critical.** Degrees treated as metres, ODN mixed with ellipsoidal heights, wrong sun direction or time zone. Run control-point/dimension checks, native CRS inspection and analytic shadows before optimisation[68][111][113].
3. **Invented plantability — critical.** Historic planting/park/locality polygons become permission. Require explicit masks and unresolved utilities/ownership/consent status; retain professional survey gate[99][116][119].
4. **Bad dataset rights — high.** Viewable/downloadable assets are redistributed as open meshes. Audit each exact source licence and attribution; unknown rights block distribution, not every unrelated module[87][101][164].
5. **Optimiser dishonesty — high.** Overlap is added twice, winter variables cheat, greedy theorem applied to conflicts. Use union/transmission invariants, full OR constraints where required, exact small cases and honest best-found labels[77][78][80].
6. **Agent theatre — high.** Scripted decisions or narration presented as adaptive intelligence. Run same-tools fixed/manual ablations and unseen perturbations; retain useful non-agent workflow[151][56][154].
7. **Prompt injection / excessive capability — high.** Site metadata changes policy or escapes domain tools. Treat text as data, validate dispatch, test malicious attributes and measure legitimate utility as well as attack outcomes[153][62][63].
8. **False novelty — high.** Ignore Infrared City or TreePlanter. State overlap and test the narrower differentiator; no “first” claim without stronger evidence[15][71][20].
9. **Spark compatibility — high.** x86 image, mismatched parser/vLLM, missing CUDA build or unavailable weights. Pin exact Arm-compatible artifacts, run model/tool/physics smoke tests on the actual unit, prepare a truthful fallback[42][47][50].
10. **GPU decorative work — medium/high.** Install Warp/OptiX/Omniverse before measuring the bottleneck. Start with a CPU reference; report cold/warm and concurrent end-to-end latency; keep the lowest-risk route that meets the task[44][45][46].
11. **Scope and integration — high.** Three people implement incompatible broad modules before a working vertical slice. Preserve shared contract ownership and the baseline→one-tree→computed-difference→UI gate; add evidence-backed slices through BUILD.
12. **Uncertainty laundering — high.** Scenario ranges called confidence intervals or formal VOI. State what is assumed, measured and probabilistic; do not supply unsupported distributions[64][80][171].
13. **Environmental double counting — high.** Add incompatible stocks/flows/monetary values; equate deposition with exposure. Separate physical boundaries and counterfactuals; validate before valuation[136][138][142].
14. **Temporal contamination — high.** Current product features, repository code or guidance attributed to an earlier event. Use pinned revisions and dated document history; record live-only evidence and retrieval conflicts[15][139][141].
15. **Eligibility and demo credibility — high.** Assume advance-code permission; hide a failed live run; announce untested accuracy. Confirm rules, disclose provenance, label cached/reference paths and show actual receipts[1].
16. **No buyer — unresolved.** A sophisticated prototype lacks a decision owner or usable deliverable. Validate one estate/arboricultural workflow with a sample evidence pack before claiming adoption or revenue[143][144].

### Risk evidence status and likelihood

Likelihood labels are qualitative planning judgements, not measured frequencies. **Confirmed issues:** generic novelty overlap (certain from source), historic/locality-layer semantic mismatch (confirmed), source-access/version discrepancies (confirmed and recorded). **Plausible high-likelihood risks unless checked:** geometry/CRS/data-rights mistakes, scope/integration pressure and unsupported benefit wording. **Plausible medium-likelihood risks:** driver/parser mismatch, local-model quality failure, prompt injection and stale-result bugs; actual implementation tests may raise or lower these judgements. **Open questions:** site permission, utility/soil conditions, professional demand and pilot economics. **Organiser clarification required:** advance work/AI assistance, exact deadline and submission/repository requirements. **Awaiting execution:** CPU/GPU parity/speed, optimiser decision quality, real local-agent usefulness, offline replay and physical/site validation.

No current absence of a test is labelled a demonstrated product defect. High consequence still requires a gate when probability is unknown. The ranked register above provides the mitigation and supporting sources; BUILD owns actual blockers and status.

## 13. Prioritised action roadmap

This is a recommendation overlay on BUILD, not a claim that tasks are complete. Each item gives action, reason, dependency, suggested owner, output and specification impact. Priority does not authorise side effects.

### P0 — critical before claiming an integrated Friday product

- **P0.1 Confirm decision and organiser boundary.** Agree user/site target/time/horizon and obtain rules/D through an authorised sender. Why: otherwise “success” and eligibility are ambiguous. Dependency: team/organiser decisions. Owner: Ben coordinates, all agree. Output: sourced decisions in existing D01/D05/D07. Spec impact: clarify defaults; no invented permission[1].
- **P0.2 Accept interfaces and geometry frame.** Close metric units, true/grid north, revisions, tree-profile semantics and writer ownership. Dependency: existing B01 draft. Owner: Ben + Arnav + Alex. Output: acknowledged contract/version and tests. Spec impact: CONTRACTS/NUMERICS precision, not a new architecture[68][110][113].
- **P0.3 Complete the numerical vertical slice.** B02→B04→B05 with actual output/stale failure path. Why: every later claim depends on it. Dependency: accepted B01. Owner: Arnav evaluator, Ben jobs, Alex UI. Output: reproducible G1 trace. Spec impact: none unless tests expose an actual defect.
- **P0.4 Accept or reject the real source bundle.** Audit a bounded primary/fallback site and rights. Dependency: SiteBundle, not the optimiser. Owner: Arnav + Alex. Output: source manifest, control-point proof, gaps and site decision. Spec impact: B03/SOURCES only until an actual chosen source changes shared semantics[91][99][118].
- **P0.5 Prove model/tool compatibility early.** Test the prepared model branch on the available authorised hardware. Dependency: B01 schema and device access. Owner: Ben. Output: exact runtime/tool-call receipt plus CPU/manual fallback. Spec impact: D06/B09 accepted candidate only after test[47][50][53].

### P1 — high-value competitive and scientific improvements

- **P1.1 Feasible search, not merely maximum coverage.** Add exact tiny cases, final-layout validation and winter truth. Dependency: B04/B07 semantics. Owner: Arnav, Ben plumbing as assigned. Output: B06/V06 evidence and honest optimality labels. Spec impact: clarify theorem/OR rules in NUMERICS/VALIDATION[77][78][81].
- **P1.2 Demonstrate a meaningful uncertainty branch.** Find a real or labelled synthetic ranking reversal and a stable control. Dependency: B07, then B10 for adaptation. Owner: Arnav + Ben. Output: current-result trace and survey-priority explanation. Spec impact: clarify sensitivity, not unsupported formal VOI[64][74][124].
- **P1.3 Freeze/run same-tools evaluation.** Use the twelve-case suite and all trials; independent scoring. Dependency: working manual/fixed and agent paths. Owner: all, scorer separate from agent implementer. Output: B11 failure-aware counts and measured latency. Spec impact: VALIDATION additions[60][62][63].
- **P1.4 Prove only useful GPU acceleration.** Measure exact workload and model coexistence. Dependency: accepted CPU reference and target device. Owner: Ben + Arnav. Output: equal-output timing/memory comparison. Spec impact: runtime manifest, no mandatory Warp/OptiX rewrite[42][45][46].
- **P1.5 Make the decision legible and rehearse failure.** Show source/assumption/change/constraint/evidence, not only a heatmap. Dependency: G1/G2/G3 as applicable. Owner: Alex, Arnav claims, Ben runtime. Output: repeatable live sequence and labelled recovery. Spec impact: V10–V12/runbook[1].

### P2 — research and maintained-product extensions

- **P2.1 Site-calibrated radiation/comfort.** Dependency: accepted geometry/weather and SOLWEIG/UMEP comparison. Owner: Arnav with qualified domain review. Output: matched-model errors then observed validation. Spec impact: new typed quantity, never overwrite shade semantics[69][83][84].
- **P2.2 Survey-priority/VOI research benchmark.** Dependency: meaningful scenario reversals; formal VOI additionally needs probabilities, observation model and utility. Owner: Ben + Arnav. Output: held-out decision-quality study. Spec impact: explicit new investigation/tool semantics[64][80].
- **P2.3 One deeper service tied to a real pilot.** Choose surveyed overheating/building, engineered tree-pit drainage, or lifecycle inventory. Dependency: user + obtainable inputs and professional validation path. Owner: nominated module owner, not all three in parallel. Output: module contract, conditional model and independent validation. Spec impact: separate optional output namespace[131][133][136].
- **P2.4 Evidence-governed profile catalogue.** Dependency: source rights, measured dimensions, UK suitability and maintenance evidence. Owner: Arnav/professional; Alex import QA. Output: versioned profiles with domain/provenance/gap flags. Spec impact: profile schema change with consumer review[124][126][128].
- **P2.5 Pilot adoption and maintenance economics.** Dependency: permission to contact and working evidence pack. Owner: Ben with team. Output: actual user feedback, ownership/support/update plan and tested comparison workflow; no predicted income. Spec impact: roadmap only until a pilot requirement is accepted[143][144].

## 14. Documentation amendment recommendations

**Research publication only:** these changes are proposals for affected owners, not silently applied implementation instructions. Preserve the recent source-applicability assessment on main. Do not maintain a second task dashboard or erase earlier provenance.

| Existing document | Strength to preserve | Necessary clarification / missing evidence | Optional change | Avoid |
|---|---|---|---|---|
| **README.md** | Clear project identity and entry point; no existing-app claim. | Link this dossier as research; maintain tested versus planned status and current setup truth. | One concise evidence-bearing product statement after team decision. | Promotional novelty, environmental numbers or install claims unsupported by execution. |
| **docs/README.md** | Living-doc authority and separated engineering/eligibility tracks. | Add research link and keep SPEC/CONTRACTS/NUMERICS/BUILD authority explicit. | Reading order for three lanes. | Replacing active specs with this large dossier. |
| **SPEC.md** | Reusable site product; deterministic truth; one runtime agent; real vertical slices. | Exact permitted quantity claims, conditional versus observed outputs, competitor-aware positioning and evidence-gated optional services. | Survey-priority investigation once tested. | Expanding the core into a multi-agent/all-service platform or declaring a new scope without agreement. |
| **CONTRACTS.md** | Immutable revisions, jobs, comparison identity and safe tool boundaries. | True/grid-north frame; acquisition/rights/profile versions; clarify any weighted score and optional module unavailable-state. Apply only with all producer/consumer impacts. | Distinct weather/scenario/module manifests when needed. | Parallel schema definitions, model-computed numbers, adding every future field now. |
| **NUMERICS.md** | Analytic opaque reference, explicit units and overlap/constraint semantics. | Submodularity theorem assumptions; winter OR truth; existing shade; fixed-crossing versus optional chord attenuation; horizon, rotation and scenario semantics. | CPU/GPU/reference comparison protocol and radiation formula when inputs exist. | Silently replacing the existing fixed-crossing B07 contract or promising global optimality/cooling from shade. |
| **BUILD.md** | Single status home, B01–B12 dependencies and named review gates. | Record accepted decisions, source rejection/acceptance, first failed gate and actual receipts; attach this recommendation overlay rather than duplicate tasks. | Select a P2 module only after pilot evidence. | Marking research, documents or worker completion as application-task completion. |
| **VALIDATION.md** | Phase-specific acceptance, stale/failure tests and real local-agent requirement. | Frozen twelve-case suite, exact optimiser checks, north-frame/control-point tests, same-tools/repetition policy and independent scoring. | Larger benchmark/observations after a defined claim. | Inflating test coverage with unexecuted cases or equating simulator agreement with field validity. |
| **SOURCES.md** | Existing numbered sources and applicability/rights assessments. | Add a clearly separate dossier link if desired; reconcile exact versions/rights before implementation. Existing numbers must retain meaning. | Selected new primary sources that change an actual specification. | Renumbering historic citations to match this independent register or duplicating the entire bibliography. |
| **AGENTS.md** | Scoped ownership, evidence, approval and untrusted-data safeguards. | No material safeguard defect found in this research. Reference the accepted task/spec version in handoffs. | A narrow source/contract lesson only if it prevents a demonstrated recurring failure. | Broad agent-policy/config changes or new authority over teammates. |
| **references/RESEARCH_HANDOFF.md** | Historical evidence, earlier design and provenance. | Add a supersession pointer only if necessary; retain snapshot meaning. | None required. | Rewriting history to make later research appear earlier. |
| **references/AGENTIC_FEATURE_REVIEW.md** | Inspectable tools/state and separated planning agent versus development assistants. | Cross-reference actual new competitors, task suite and small/large model results when measured. | Survey-priority path. | Treating agent-loop design as proof of useful agency. |
| **DGX-readiness branch/docs** | Concrete prior device/model preparation. | Verify its exact checkpoint/parser/image against model-card requirements and actual device. Keep branch/runtime state separate. | A tested alternative model branch. | Claiming research published here deploys it or mixing unrelated readiness code into this documentation commit. |

### Practical tree-profile and site-shortlisting procedure

Use a professional-facing shortlist, not automatic species selection: (1) identify site function, protected/veteran habitats, actual rooting/soil/drainage constraints and maintenance capacity; (2) choose suitable species/stock options using the Urban Tree Manual and rights-cleared specialist guidance; (3) attach measured or evidence-domain-limited dimensions and leaf-state assumptions; (4) evaluate establishment and future scenarios; (5) reject geometric winners that fail biological/site/maintenance criteria; (6) have the responsible arboricultural/estate professional review before planting. Keep “unknown” distinct from “suitable”. Full TDAG coefficient/profile content was not audited and cannot be redistributed under assumed commercial rights[125][126][147].

For the initial scene audit, use a **proposed 200 m × 200 m analysis crop** centred on the known Weston locator `(434002,387395)` in EPSG:27700, plus a separately justified shadow-casting context margin. This is a provisional computational crop, not a site boundary, use target or planting permission. The initial target should be a named path/play area chosen from actual lawful geometry and user purpose. Determine context from obstacle heights, low sun and convergence; the crop size alone is not a sufficient physical boundary[118][121][122].

Compare alternatives without inventing survey facts: Weston has the strongest inspected locator/heritage/park evidence but significant existing-canopy and consent issues; Manor Fields has verified park identity and a plausible operational site lead but needs an actual sub-area/receiver and LiDAR audit; Peace Gardens has official place identity but a more complex central public-realm context and no matching name in the queried parks layer. Proposed preparation effort is moderate for the first two and higher for the third, an engineering judgement pending the crop/asset inspection. **Primary: Weston for the geometry/decision pilot; fallback: a bounded Manor Fields sub-area if Weston rights, heritage constraints or the target make it unsuitable.** Neither has demonstrated solar benefit or plantability from this research[95][96][97].

## Sources

This register contains **170 source records**, mixing distinct works with supporting documentation, code versions and public-data endpoints. It is not 170 papers. Entries retain ledger IDs, so gaps are intentional. Priorities identify the reading path; official documentation and code are retained where they change an implementation or rights decision.

### [1] Hack for Impact: Sheffield
- **Author/publisher; year/version:** NVIDIA; 2026.
- **Type / venue:** Official event page; NVIDIA.
[1] https://events.nvidia.com/Hack-for-Impact-Sheffield — Hack for Impact: Sheffield
- **Contribution / method:** Defines date, local-model/Spark brief, team size and three judging criteria. Event requirements and timeline inspection.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Event requirements and timeline inspection..
- **Limitations:** Does not state advance-code/assistant permission, detailed submission deadline or mandatory GPU physics.
- **Use / priority / reader:** Eligibility and pitch gate — **Essential**; All.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [2] PhD student wins NVIDIA hackathon prize and government recognition for NHS tool | Faculty of Engineering
- **Author/publisher; year/version:** UCL Faculty of Engineering; 2026.
- **Type / venue:** Institutional news; UCL Faculty of Engineering.
[2] https://www.ucl.ac.uk/engineering/news/2026/jun/phd-student-wins-nvidia-hackathon-prize-and-government-recognition-nhs-tool-3 — PhD student wins NVIDIA hackathon prize and government recognition for NHS tool | Faculty of Engineering
- **Contribution / method:** Corroborates a student hackathon win and NHS-tool recognition. Institutional event account.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Institutional event account..
- **Limitations:** Not a benchmark or independent clinical evaluation; not Sheffield rules.
- **Use / priority / reader:** Prior-event precedent — **Useful**; Ben; Alex.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [3] UCL Computer Science students recognised in national and international competitions | Faculty of Engineering
- **Author/publisher; year/version:** UCL Faculty of Engineering; 2026.
- **Type / venue:** Institutional news; UCL Faculty of Engineering.
[3] https://www.ucl.ac.uk/engineering/news/2026/sep/ucl-computer-science-students-recognised-national-and-international-competitions — UCL Computer Science students recognised in national and international competitions | Faculty of Engineering
- **Contribution / method:** Places student competition outcomes in institutional context. Named competition/outcome account.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Named competition/outcome account..
- **Limitations:** Do not infer judging rationale or current eligibility.
- **Use / priority / reader:** Precedent cross-check — **Useful**; Ben.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [5] Let your agent run the physics · infrared.city
- **Author/publisher; year/version:** Infrared City; Undated; cutoff snapshot.
- **Type / venue:** Vendor product documentation; Infrared City.
[5] https://infrared.city/solutions-agents — Let your agent run the physics · infrared.city
- **Contribution / method:** Direct competitor offers agent-facing microclimate investigations. SDK/agent workflow description.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; SDK/agent workflow description..
- **Limitations:** Vendor capability/performance statements; no runtime benchmark or open-engine proof.
- **Use / priority / reader:** Novelty boundary and integration alternative — **Essential**; All.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [6] New backing for open-source AI builders, data centre design challenge and robotics partnership - GOV.UK
- **Author/publisher; year/version:** UK Department for Science, Innovation and Technology; 2026.
- **Type / venue:** Government announcement; UK Department for Science, Innovation and Technology.
[6] https://www.gov.uk/government/news/new-backing-for-open-source-ai-builders-data-centre-design-challenge-and-robotics-partnership — New backing for open-source AI builders, data centre design challenge and robotics partnership - GOV.UK
- **Contribution / method:** Names Codeborough, WaitWise, Stella and NeMo-Ray among London winners. Official outcome announcement.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Official outcome announcement..
- **Limitations:** No unpublished scores, source-code identity match or causation of wins.
- **Use / priority / reader:** Winner identity and cautious precedent — **Essential**; All.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [7] Climate Simulation API: Python and TypeScript SDK · infrared.city
- **Author/publisher; year/version:** Infrared City; Undated; cutoff snapshot.
- **Type / venue:** Vendor API documentation; Infrared City.
[7] https://infrared.city/products-api — Climate Simulation API: Python and TypeScript SDK · infrared.city
- **Contribution / method:** Python/TypeScript integration surface for climate simulation. API/SDK workflow documentation.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; API/SDK workflow documentation..
- **Limitations:** No independent latency, licence grant for engine or offline reproduction.
- **Use / priority / reader:** Build-versus-integrate comparison — **Essential**; Ben.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [8] Infrared Core: Urban Climate Simulation Engine · infrared.city
- **Author/publisher; year/version:** Infrared City; Undated; cutoff snapshot.
- **Type / venue:** Vendor engine documentation; Infrared City.
[8] https://infrared.city/products-engine — Infrared Core: Urban Climate Simulation Engine · infrared.city
- **Contribution / method:** Describes underlying urban climate simulation offering. Vendor architecture/capability account.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Vendor architecture/capability account..
- **Limitations:** Self-hosting/product claims not independently deployed.
- **Use / priority / reader:** Scientific/product scope comparison — **Useful**; Arnav; Ben.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [9] Pricing: 900 free tokens, from €240/year · infrared.city
- **Author/publisher; year/version:** Infrared City; 2026 snapshot.
- **Type / venue:** Vendor pricing page; Infrared City.
[9] https://infrared.city/pricing — Pricing: 900 free tokens, from €240/year · infrared.city
- **Contribution / method:** Documents available commercial access/pricing snapshot. Pricing and plan inspection.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Pricing and plan inspection..
- **Limitations:** Not spend approval; terms/entitlements may change.
- **Use / priority / reader:** Commercial alternative context — **Useful**; Ben.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [10] Generative Agentic AI and Explainable Digital Twins for Climate-Neutral Cities | GENeCITY | Project | Fact Sheet | HORIZON | CORDIS | European Commission
- **Author/publisher; year/version:** European Commission CORDIS; 2026.
- **Type / venue:** Grant fact sheet; European Commission CORDIS.
[10] https://cordis.europa.eu/project/id/101270173 — Generative Agentic AI and Explainable Digital Twins for Climate-Neutral Cities | GENeCITY | Project | Fact Sheet | HORIZON | CORDIS | European Commission
- **Contribution / method:** GENeCITY generative/agentic digital-twin programme and June start. Funded-project objectives and dates.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Funded-project objectives and dates..
- **Limitations:** Programme, not a completed validated product.
- **Use / priority / reader:** Related research scope without false competitor claims — **Useful**; All.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [11] README.md — Infrared-city/infrared-skills
- **Author/publisher; year/version:** Infrared City maintainers; Pinned pre-cutoff commit; fff92e3cdb1464a834036b0ab324bab6add17118.
- **Type / venue:** Repository README; Infrared City maintainers.
[11] https://github.com/Infrared-city/infrared-skills/blob/fff92e3cdb1464a834036b0ab324bab6add17118/README.md — README.md — Infrared-city/infrared-skills
- **Contribution / method:** Public agent integration repository rather than only marketing. Pinned source inspection.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Pinned source inspection..
- **Limitations:** Public adapter does not open-source proprietary physics.
- **Use / priority / reader:** Competitor implementation grounding — **Essential**; Ben.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [12] README.md — khayamumair/waitwise
- **Author/publisher; year/version:** WaitWise maintainers; Pinned pre-cutoff commit; 17cdfd92f5c8485481c268de2366501f1fb21d76.
- **Type / venue:** Repository README; WaitWise maintainers.
[12] https://github.com/khayamumair/waitwise/blob/17cdfd92f5c8485481c268de2366501f1fb21d76/README.md — README.md — khayamumair/waitwise
- **Contribution / method:** Public operations/triage workflow and architecture. Pinned README/source inspection; event metadata checked separately.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Pinned README/source inspection; event metadata checked separately..
- **Limitations:** Not independently run; current pinned code not automatically the judged version.
- **Use / priority / reader:** Hackathon workflow comparison — **Useful**; Ben; Alex.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [13] waitwise-backend/agents/triage.py — khayamumair/waitwise
- **Author/publisher; year/version:** WaitWise maintainers; Pinned pre-cutoff commit; 17cdfd92f5c8485481c268de2366501f1fb21d76.
- **Type / venue:** Implementation source; WaitWise maintainers.
[13] https://github.com/khayamumair/waitwise/blob/17cdfd92f5c8485481c268de2366501f1fb21d76/waitwise-backend/agents/triage.py — waitwise-backend/agents/triage.py — khayamumair/waitwise
- **Contribution / method:** Actual triage-agent integration path. Source-level inspection.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Source-level inspection..
- **Limitations:** No measured reliability or event-day runtime reproduction.
- **Use / priority / reader:** Compare agent architecture with implementation — **Useful**; Ben.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [14] README.md — Bl4ckd09/Stella
- **Author/publisher; year/version:** Bl4ckd09/Stella maintainers; Pinned pre-cutoff commit; 63192b8c2c6439f8bddaf50407ce466393316b20.
- **Type / venue:** Repository README; Bl4ckd09/Stella maintainers.
[14] https://github.com/Bl4ckd09/Stella/blob/63192b8c2c6439f8bddaf50407ce466393316b20/README.md — README.md — Bl4ckd09/Stella
- **Contribution / method:** Demonstrates that a similar-name discovered repository is not verified as the NVIDIA-winning Stella. README plus repository creation/event chronology.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; README plus repository creation/event chronology..
- **Limitations:** Winner identity unverified; do not attribute its dependencies/test claims to the NVIDIA entry.
- **Use / priority / reader:** Prevent false precedent attribution — **Essential**; Ben.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [15] plugins/infrared/skills/use-infrared/SKILL.md
- **Author/publisher; year/version:** Infrared City maintainers; Commit fff92e3cdb1464a834036b0ab324bab6add17118; fff92e3cdb1464a834036b0ab324bab6add17118.
- **Type / venue:** Agent integration skill source; Infrared City maintainers.
[15] https://github.com/Infrared-city/infrared-skills/blob/fff92e3cdb1464a834036b0ab324bab6add17118/plugins/infrared/skills/use-infrared/SKILL.md — plugins/infrared/skills/use-infrared/SKILL.md
- **Contribution / method:** Agent-callable climate operations and workflow exposed in code. Pinned SKILL.md and related implementation reading.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Pinned SKILL.md and related implementation reading..
- **Limitations:** No physics source, benchmark or self-hosted-engine licence implied.
- **Use / priority / reader:** Most consequential novelty correction — **Essential**; All.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [16] plugins/infrared/skills/use-infrared/references/interpretation/thermal-results.md
- **Author/publisher; year/version:** Infrared City maintainers; Same pinned skill commit; fff92e3cdb1464a834036b0ab324bab6add17118.
- **Type / venue:** Interpretation documentation; Infrared City maintainers.
[16] https://github.com/Infrared-city/infrared-skills/blob/fff92e3cdb1464a834036b0ab324bab6add17118/plugins/infrared/skills/use-infrared/references/interpretation/thermal-results.md — plugins/infrared/skills/use-infrared/references/interpretation/thermal-results.md
- **Contribution / method:** Documented interpretation boundary for thermal outputs. Source-level reference reading.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Source-level reference reading..
- **Limitations:** Vendor model assumptions still need independent validation.
- **Use / priority / reader:** Result-semantics comparison — **Useful**; Arnav; Ben.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [17] cookbook/notebooks/01_design_variants.ipynb
- **Author/publisher; year/version:** Infrared City maintainers; Same pinned skill commit; fff92e3cdb1464a834036b0ab324bab6add17118.
- **Type / venue:** Example notebook; Infrared City maintainers.
[17] https://github.com/Infrared-city/infrared-skills/blob/fff92e3cdb1464a834036b0ab324bab6add17118/cookbook/notebooks/01_design_variants.ipynb — cookbook/notebooks/01_design_variants.ipynb
- **Contribution / method:** Concrete tree/design-variant scenario workflow. Notebook source inspection.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Notebook source inspection..
- **Limitations:** Notebook not executed; example does not validate our site/model.
- **Use / priority / reader:** Compare adaptive variant feature — **Essential**; Ben; Arnav.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [18] pedroandreou/Codeborough README
- **Author/publisher; year/version:** Codeborough maintainers; Pinned pre-cutoff commit; 7c186cd8742b8bceb34478b4800cf18d8706f2a9.
- **Type / venue:** Repository README; Codeborough maintainers.
[18] https://github.com/pedroandreou/Codeborough/blob/7c186cd8742b8bceb34478b4800cf18d8706f2a9/README.md — pedroandreou/Codeborough README
- **Contribution / method:** Voice-first civic concierge with local and explicitly optional external components. README and event-end commit metadata.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; README and event-end commit metadata..
- **Limitations:** Do not call all components offline or infer judged-version metrics.
- **Use / priority / reader:** Clear civic decision and dependency boundary precedent — **Useful**; Ben; Alex.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [20] Locating trees to mitigate outdoor radiant load of humans in urban areas using a metaheuristic hill-climbing algorithm – introducing TreePlanter v1.0
- **Author/publisher; year/version:** Nils Wallenberg; Fredrik Lindberg; David Rayner; Published 2022-02-07; TreePlanter v1.0.
- **Type / venue:** Peer-reviewed model description; Geoscientific Model Development 15, 1107–1128.
[20] https://gmd.copernicus.org/articles/15/1107/2022 — TreePlanter paper
- **DOI:** 10.5194/gmd-15-1107-2022
- **Contribution / method:** Direct prior art; fuller radiation reruns can alter search rankings. Cached tree-shadow/radiant-load information; overlap-aware local search; SOLWEIG reassessment.
- **Access and reading depth:** Full HTML paper retrieved; Preprocessing, greedy/hill-climbing algorithms, evaluation, rerun comparisons, discussion and availability read.
- **Limitations:** Specific Gothenburg experiment; heterogeneous profiles and planning feasibility are not established here.
- **Use / priority / reader:** Strong comparator and independent reevaluation pattern. — **Essential**; Arnav; Ben; Alex.
- **Implementation:** https://doi.org/10.5281/zenodo.4616761
- **Rights:** Paper CC BY 4.0; archived-code license not inspected

### [21] UMEP TreePlanter tutorial
- **Author/publisher; year/version:** UMEP maintainers; Cutoff snapshot.
- **Type / venue:** Tutorial; UMEP maintainers.
[21] https://umep-docs.readthedocs.io/projects/tutorial/en/latest/Tutorials/IntroductionToTreePlanter.html — UMEP TreePlanter tutorial
- **Contribution / method:** TreePlanter preprocessing and use path. Tutorial inspection.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Tutorial inspection..
- **Limitations:** Not an installation/run receipt.
- **Use / priority / reader:** Reuse versus rebuild and data requirements — **Essential**; Arnav.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [22] UMEP processing implementation
- **Author/publisher; year/version:** UMEP maintainers; Pinned pre-cutoff commit; a7798db1698c29fa5ba667e082e7ad564c20e8e8.
- **Type / venue:** Algorithm source; UMEP maintainers.
[22] https://github.com/UMEP-dev/UMEP-processing/blob/a7798db1698c29fa5ba667e082e7ad564c20e8e8/postprocessor/treeplanter_algorithm.py — UMEP processing implementation
- **Contribution / method:** Actual TreePlanter processing implementation. Pinned Python algorithm inspection.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Pinned Python algorithm inspection..
- **Limitations:** Source familiarity is not numerical/runtime reproduction.
- **Use / priority / reader:** Existing optimiser/thermal reference baseline — **Essential**; Arnav.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [23] Freiburg research README
- **Author/publisher; year/version:** Schrodi et al.; Freiburg maintainers; Pinned pre-cutoff commit; a997b89c250c86656a70deef0f54ca07fca4cedd.
- **Type / venue:** Research repository README; Schrodi et al.; Freiburg maintainers.
[23] https://github.com/lmb-freiburg/tree-planting/blob/a997b89c250c86656a70deef0f54ca07fca4cedd/README.md — Freiburg research README
- **Contribution / method:** Actual implementation associated with climate-sensitive tree-placement preprint. README inspection paired with paper.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; README inspection paired with paper..
- **Limitations:** Do not conflate with TreeShadeMapper.
- **Use / priority / reader:** Surrogate/search reuse candidate — **Useful**; Arnav; Ben.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [24] Freiburg optimisation implementation
- **Author/publisher; year/version:** Freiburg tree-planting maintainers; Pinned pre-cutoff commit; a997b89c250c86656a70deef0f54ca07fca4cedd.
- **Type / venue:** Optimisation source; Freiburg tree-planting maintainers.
[24] https://github.com/lmb-freiburg/tree-planting/blob/a997b89c250c86656a70deef0f54ca07fca4cedd/optimize.py — Freiburg optimisation implementation
- **Contribution / method:** Actual search implementation behind the reported surrogate approach. Pinned optimize.py inspection.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Pinned optimize.py inspection..
- **Limitations:** Not executed or benchmarked here.
- **Use / priority / reader:** Algorithmic comparator and implementation leverage — **Useful**; Arnav.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [25] Cornell Tree Folio project
- **Author/publisher; year/version:** Cornell AAP Design Across Scales Lab; 2023 project; cutoff snapshot.
- **Type / venue:** Institutional project page; Cornell AAP Design Across Scales Lab.
[25] https://labs.aap.cornell.edu/daslab/projects/treefolio — Cornell Tree Folio project
- **Contribution / method:** Tree Folio canopy digital twin and shade communication. Project description inspection.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Project description inspection..
- **Limitations:** Institutional description does not validate independent metrics or optimiser.
- **Use / priority / reader:** Product/display precedent — **Useful**; Alex.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [26] Tree Folio dashboard
- **Author/publisher; year/version:** Tree Folio project; Undated; cutoff snapshot.
- **Type / venue:** Interactive application landing page; Tree Folio project.
[26] https://www.treefolio.org — Tree Folio dashboard
- **Contribution / method:** Public dashboard existence. Minimal readable landing text; interactive app not exercised.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Minimal readable landing text; interactive app not exercised..
- **Limitations:** No substantive dashboard capability benchmark.
- **Use / priority / reader:** Optional UX lead, not central scientific proof — **Optional**; Alex.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [27] ShadePlan README
- **Author/publisher; year/version:** ShadePlan maintainers; Pinned pre-cutoff commit; ccb08c0cef2dcc5cae88cda550e9924b0e773a66.
- **Type / venue:** Repository README; ShadePlan maintainers.
[27] https://github.com/gitrlawton/urban-cooling/blob/ccb08c0cef2dcc5cae88cda550e9924b0e773a66/README.md — ShadePlan README
- **Contribution / method:** Urban-cooling/tree intervention agent workflow overlap. README paired with actual tools.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; README paired with actual tools..
- **Limitations:** Marketing-like README is not physics validation.
- **Use / priority / reader:** Competitor/small-system baseline — **Essential**; Ben; Arnav.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [28] ShadePlan agent registration
- **Author/publisher; year/version:** ShadePlan maintainers; Pinned pre-cutoff commit; ccb08c0cef2dcc5cae88cda550e9924b0e773a66.
- **Type / venue:** Agent registration source; ShadePlan maintainers.
[28] https://github.com/gitrlawton/urban-cooling/blob/ccb08c0cef2dcc5cae88cda550e9924b0e773a66/backend/agents/urban_cooling_analyst.py — ShadePlan agent registration
- **Contribution / method:** Google ADK agent with named geospatial/shade tools. Actual registration source inspection.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Actual registration source inspection..
- **Limitations:** Not evidence the agent reliably chooses tools.
- **Use / priority / reader:** Compare explicit tool surfaces — **Useful**; Ben.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [29] ShadePlan shade computation
- **Author/publisher; year/version:** ShadePlan maintainers; Pinned pre-cutoff commit; ccb08c0cef2dcc5cae88cda550e9924b0e773a66.
- **Type / venue:** Shade calculation source; ShadePlan maintainers.
[29] https://github.com/gitrlawton/urban-cooling/blob/ccb08c0cef2dcc5cae88cda550e9924b0e773a66/backend/tools/shade_simulation.py — ShadePlan shade computation
- **Contribution / method:** Degree-grid/centre-path heuristic with capped increments. Actual simulate_shade_coverage implementation inspected.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Actual simulate_shade_coverage implementation inspected..
- **Limitations:** Not a measured crown/mesh radiative model; no runtime benchmark.
- **Use / priority / reader:** Avoid mistaking simple heuristics for validated physics — **Essential**; Arnav; Ben.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [30] NeMo-Ray README
- **Author/publisher; year/version:** NeMo-Ray maintainers; Pinned pre-cutoff commit; 6b3dfdc06ffe9b846eca864fb87257151ed0f337.
- **Type / venue:** Repository README; NeMo-Ray maintainers.
[30] https://github.com/Harrishayy/NeMo-Ray/blob/6b3dfdc06ffe9b846eca864fb87257151ed0f337/README.md — NeMo-Ray README
- **Contribution / method:** Applied medical agent workflow precedent. README/source inspection and official winner corroboration.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; README/source inspection and official winner corroboration..
- **Limitations:** No clinical validity/regulatory/accuracy claim.
- **Use / priority / reader:** Demonstration coherence only — **Useful**; Ben; Alex.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [31] NeMo-Ray agent loop
- **Author/publisher; year/version:** NeMo-Ray maintainers; Pinned pre-cutoff commit; 6b3dfdc06ffe9b846eca864fb87257151ed0f337.
- **Type / venue:** Agent-loop source; NeMo-Ray maintainers.
[31] https://github.com/Harrishayy/NeMo-Ray/blob/6b3dfdc06ffe9b846eca864fb87257151ed0f337/agent/nemoray_modelling/agent.py — NeMo-Ray agent loop
- **Contribution / method:** Actual agent control implementation. Source-level inspection.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Source-level inspection..
- **Limitations:** No independent clinical/workflow runtime test.
- **Use / priority / reader:** Compare tool loop and fallback patterns — **Useful**; Ben.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [32] NeMo-Ray tools
- **Author/publisher; year/version:** NeMo-Ray maintainers; Pinned pre-cutoff commit; 6b3dfdc06ffe9b846eca864fb87257151ed0f337.
- **Type / venue:** Tool source; NeMo-Ray maintainers.
[32] https://github.com/Harrishayy/NeMo-Ray/blob/6b3dfdc06ffe9b846eca864fb87257151ed0f337/agent/nemoray_modelling/tools.py — NeMo-Ray tools
- **Contribution / method:** Concrete domain-tool surface. Source-level inspection.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Source-level inspection..
- **Limitations:** Medical findings and safety do not transfer to planning.
- **Use / priority / reader:** Implementation pattern only — **Useful**; Ben.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [33] UrbanTreeAgent README
- **Author/publisher; year/version:** UrbanTreeAgent maintainers; Pinned pre-cutoff commit; 97575309be274b563063e809623cbee7d42e2d86.
- **Type / venue:** Repository README; UrbanTreeAgent maintainers.
[33] https://github.com/MerryBai/UrbanTreeAgent/blob/97575309be274b563063e809623cbee7d42e2d86/README.md — UrbanTreeAgent README
- **Contribution / method:** Image/tree-analysis implementation inspired by a five-component architecture. README paired with source.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; README paired with source..
- **Limitations:** Not independent validation of underlying research or autonomous planning.
- **Use / priority / reader:** Inventory/agent architecture alternative — **Useful**; Ben.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [34] UrbanTreeAgent planner
- **Author/publisher; year/version:** UrbanTreeAgent maintainers; Pinned pre-cutoff commit; 97575309be274b563063e809623cbee7d42e2d86.
- **Type / venue:** Planner source; UrbanTreeAgent maintainers.
[34] https://github.com/MerryBai/UrbanTreeAgent/blob/97575309be274b563063e809623cbee7d42e2d86/urban_tree_agent/components/planner.py — UrbanTreeAgent planner
- **Contribution / method:** Fixed ordered capability sequence and fallback parameters. Actual Planner.plan implementation.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Actual Planner.plan implementation..
- **Limitations:** Planner naming does not establish model-driven adaptive reasoning.
- **Use / priority / reader:** Agent versus deterministic baseline lesson — **Essential**; Ben.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [35] UrbanTreeAgent pipeline
- **Author/publisher; year/version:** UrbanTreeAgent maintainers; Pinned pre-cutoff commit; 97575309be274b563063e809623cbee7d42e2d86.
- **Type / venue:** Pipeline source; UrbanTreeAgent maintainers.
[35] https://github.com/MerryBai/UrbanTreeAgent/blob/97575309be274b563063e809623cbee7d42e2d86/urban_tree_agent/services/pipeline.py — UrbanTreeAgent pipeline
- **Contribution / method:** Component orchestration for image/tree analysis. Source-level pipeline inspection.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Source-level pipeline inspection..
- **Limitations:** No runtime or scientific accuracy validation here.
- **Use / priority / reader:** Boundary/reuse comparison — **Useful**; Ben.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [36] TreeShadeMapper README
- **Author/publisher; year/version:** Kunihiko Fujiwara; repository cites Ito, Ignatius and Biljecki; 2024 research; pinned source; 5b612c55dc4df7141a6b832f2f20603cc693f951.
- **Type / venue:** Research implementation README; Kunihiko Fujiwara; repository cites Ito, Ignatius and Biljecki.
[36] https://github.com/kunifujiwara/TreeShadeMapper/blob/5b612c55dc4df7141a6b832f2f20603cc693f951/README.md — TreeShadeMapper README
- **Contribution / method:** Panorama segmentation/transmission/sky-view/irradiance workflow. README/method/citation/licence inspection.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; README/method/citation/licence inspection..
- **Limitations:** No Sheffield imagery run; stated CC BY-SA 4.0 code terms need reuse review.
- **Use / priority / reader:** Measurement/reference alternative, separate from Freiburg optimisation — **Useful**; Arnav; Alex.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [37] Forma microclimate feature description
- **Author/publisher; year/version:** Jesper Staahl / Autodesk Forma; 2023-05-08.
- **Type / venue:** Vendor technical article; Jesper Staahl / Autodesk Forma.
[37] https://blogs.autodesk.com/forma/2023/05/08/updated-microclimate-analysis-allows-intuitive-insights-perceived-temperature — Forma microclimate feature description
- **Contribution / method:** Microclimate/perceived-temperature design analysis. Vendor feature account.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Vendor feature account..
- **Limitations:** No independent validation, local-execution proof or runtime measurement.
- **Use / priority / reader:** Commercial competitor context — **Useful**; All.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [38] Forma tool overview
- **Author/publisher; year/version:** Autodesk Forma Team; 2026-08-28.
- **Type / venue:** Vendor tool overview; Autodesk Forma Team.
[38] https://blogs.autodesk.com/forma/2026/08/28/forma-site-design-tools-overview — Forma tool overview
- **Contribution / method:** Design/analysis functions as of pre-cutoff article. Vendor documentation inspection.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Vendor documentation inspection..
- **Limitations:** Not an independently exercised product.
- **Use / priority / reader:** Build-versus-buy and scope comparison — **Useful**; Ben; Alex.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [39] Snaptrude site-analysis agents, vendor article
- **Author/publisher; year/version:** Snaptrude; 2026; updated 2026-06-22.
- **Type / venue:** Vendor article; Snaptrude.
[39] https://www.snaptrude.com/blog/ai-site-analysis-agents-architecture — Snaptrude site-analysis agents, vendor article
- **Contribution / method:** AI-assisted site-analysis workflow proposition. Vendor article reading.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Vendor article reading..
- **Limitations:** No verified autonomous performance or physics implementation.
- **Use / priority / reader:** Adjacent competition, not validated equivalent — **Useful**; All.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [40] i-Tree Design description
- **Author/publisher; year/version:** i-Tree programme; Undated; cutoff snapshot.
- **Type / venue:** Official calculator page; i-Tree programme.
[40] https://design.itreetools.org/treecalculator/calc_map/map_index.cfm — i-Tree Design description
- **Contribution / method:** Browser-based tree-benefit decision tool. Calculator documentation/page inspection.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; Calculator documentation/page inspection..
- **Limitations:** Calculator not executed; location/method assumptions matter.
- **Use / priority / reader:** Existing product substitute — **Useful**; All.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [41] i-Tree Design/Planting FAQ and model limitations
- **Author/publisher; year/version:** i-Tree programme; Undated; cutoff snapshot.
- **Type / venue:** Official FAQ; i-Tree programme.
[41] https://www.itreetools.org/faqs_home/i-tree_design_planting — i-Tree Design/Planting FAQ and model limitations
- **Contribution / method:** Design/Planting model boundaries and applicability. FAQ reading.
- **Access and reading depth:** Primary public page/source inspected; see read-depth limitations; FAQ reading..
- **Limitations:** Do not infer UK transfer, local offline operation or site-specific validity.
- **Use / priority / reader:** Interpretation and geography gates — **Useful**; Arnav; Ben.
- **Rights:** No general reuse grant inferred; verify exact content/software/data licence before adoption

### [42] DGX Spark Hardware Overview, DGX OS, Release Notes and Known Issues
- **Author/publisher; year/version:** NVIDIA; Hardware page updated 2026-11-04; October 2026 release section.
- **Type / venue:** Official hardware and operating-system documentation; NVIDIA Docs.
[42] https://docs.nvidia.com/dgx/dgx-spark/hardware.html — DGX Spark Hardware Overview, DGX OS, Release Notes and Known Issues
- **Contribution / method:** Establishes platform characteristics and device-inspection requirements. Vendor specifications and release documentation
- **Access and reading depth:** Public text retrieved; Hardware specifications, software version table, OS description and memory-accounting issue.
- **Limitations:** Published stack is not proof of the assigned event device; related pages are maintained live.
- **Use / priority / reader:** ARM64 packaging, memory accounting and B09 preflight — **Essential**; Ben and Arnav.
- **Rights:** Proprietary documentation; reuse terms not audited

### [43] CUDA Toolkit 13.1 Release Notes and Minor Version Compatibility
- **Author/publisher; year/version:** NVIDIA; CUDA 13.1.0 archive; compatibility page updated 2026-11-04.
- **Type / venue:** Versioned official documentation; NVIDIA Docs.
[43] https://docs.nvidia.com/cuda/archive/13.1.0/cuda-toolkit-release-notes/index.html — CUDA Toolkit 13.1 Release Notes and Minor Version Compatibility
- **Contribution / method:** Separates toolkit driver version from minor-compatibility floor. Vendor compatibility specification
- **Access and reading depth:** Public text retrieved; Driver tables and feature/PTX compatibility caveats.
- **Limitations:** Does not qualify a particular container's JIT kernels on GB10.
- **Use / priority / reader:** Reject simplistic driver checks — **Essential**; Ben and Arnav.
- **Rights:** Proprietary documentation

### [44] Warp 1.9.1 installation, changelog and mesh ray-query implementation
- **Author/publisher; year/version:** NVIDIA and Warp contributors; v1.9.1, 2025-10-01.
- **Type / venue:** Original repository implementation and versioned documentation; GitHub; NVIDIA Warp documentation.
[44] https://nvidia.github.io/warp/v1.9/installation.html — Warp 1.9.1 installation, changelog and mesh ray-query implementation
- **Contribution / method:** Documents AArch64/CPU paths and identifies software BVH traversal in the inspected version. Source-code and packaging inspection
- **Access and reading depth:** Public tagged source and documentation retrieved; Installation requirements, dated changelog and mesh_query_ray traversal body.
- **Limitations:** No installation or execution; conclusions do not cover every later Warp backend.
- **Use / priority / reader:** Optional accelerated solver behind CPU reference — **High**; Arnav.
- **Implementation:** https://github.com/NVIDIA/warp/tree/v1.9.1
- **Rights:** Apache-2.0, confirmed in source header

### [45] CuPy 14.0.0 Installation and Release Notes
- **Author/publisher; year/version:** CuPy developers; v14.0.0, 2026-02-18.
- **Type / venue:** Versioned documentation and original release; CuPy documentation; GitHub.
[45] https://docs.cupy.dev/en/v14.0.0/install.html — CuPy 14.0.0 Installation and Release Notes
- **Contribution / method:** A concrete CUDA-array packaging option. Documentation and release inspection
- **Access and reading depth:** Public text retrieved; Requirements, AArch64 wheel table and release changes.
- **Limitations:** Documented wheels are not application or GB10 execution proof; no spatial engine supplied.
- **Use / priority / reader:** Consider only where existing array operations justify it — **Medium**; Arnav.
- **Implementation:** https://github.com/cupy/cupy/releases/tag/v14.0.0
- **Rights:** Unknown; licence file not inspected

### [46] NVIDIA OptiX Downloads and Legacy Release Summaries
- **Author/publisher; year/version:** NVIDIA; 9.0.0, February 2025; 9.1.0, December 2025.
- **Type / venue:** Official SDK release summaries; NVIDIA Developer.
[46] https://developer.nvidia.com/designworks/optix/downloads/legacy — NVIDIA OptiX Downloads and Legacy Release Summaries
- **Contribution / method:** Distinguishes an explicit RT API from ordinary CUDA ray traversal. Release requirement comparison
- **Access and reading depth:** Public summaries retrieved; detailed 9.0 PDF redirected to login; Platform, driver, RT-core and licence-access summaries; not full SDK notes.
- **Limitations:** Exact GB10 qualification and full SDK terms remain uninspected.
- **Use / priority / reader:** Defer unless RT acceleration is a measured project requirement — **High**; Arnav and Ben.
- **Implementation:** https://developer.nvidia.com/designworks/optix/download
- **Rights:** NVIDIA SDK agreement; not an open-source licence

### [47] NVIDIA-Nemotron-3-Nano-30B-A3B-BF16 pinned model card
- **Author/publisher; year/version:** NVIDIA; Released 2025-12-15; revision bf77c3174f68ad409e1c2aa60daeb46e32d1c606, history dated 2026-08-24.
- **Type / venue:** Pinned original model card; Hugging Face.
[47] https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16/blob/bf77c3174f68ad409e1c2aa60daeb46e32d1c606/README.md — NVIDIA-Nemotron-3-Nano-30B-A3B-BF16 pinned model card
- **Contribution / method:** Supports the proposed deployment candidate. Model-card and revision-history audit
- **Access and reading depth:** Pinned README and commit history retrieved; Architecture, context, vLLM/parser recipe, thinking controls and inference hardware.
- **Limitations:** No weight verification, device execution or project benchmark.
- **Use / priority / reader:** B09 candidate qualification — **Essential**; Ben.
- **Implementation:** https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16/tree/bf77c3174f68ad409e1c2aa60daeb46e32d1c606
- **Rights:** NVIDIA Nemotron Open Model License

### [48] Nemotron 3 Nano: Open, Efficient Mixture-of-Experts Hybrid Mamba-Transformer Model for Agentic Reasoning
- **Author/publisher; year/version:** NVIDIA research team; arXiv v1, 2025-12-23.
- **Type / venue:** Full technical report; arXiv.
[48] https://arxiv.org/html/2512.20848v1 — Nemotron 3 Nano: Open, Efficient Mixture-of-Experts Hybrid Mamba-Transformer Model for Agentic Reasoning
- **DOI:** 10.48550/arXiv.2512.20848
- **Contribution / method:** Explains hybrid memory structure and active-parameter terminology. Architecture description and vendor benchmark evaluation
- **Access and reading depth:** Full HTML retrieved; Architecture table, active/total parameters, training/evaluation sections and limitations of hardware transfer.
- **Limitations:** No Sheffield task evaluation; no Spark result located in the report.
- **Use / priority / reader:** Memory model and model-selection hypotheses — **High**; Ben and Arnav.
- **Implementation:** https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16
- **Rights:** Paper licence not independently resolved

### [49] NVIDIA-Nemotron-Nano-9B-v2 Model Card and History
- **Author/publisher; year/version:** NVIDIA; Released 2025-08-18; inspected history through 6533e8d, 2026-03-05.
- **Type / venue:** Original model card and revision history; Hugging Face.
[49] https://huggingface.co/nvidia/NVIDIA-Nemotron-Nano-9B-v2 — NVIDIA-Nemotron-Nano-9B-v2 Model Card and History
- **Contribution / method:** Smaller candidate with distinct parser/cache requirements. Card and history inspection
- **Access and reading depth:** Live card/history retrieved; attempted pinned raw card inaccessible; Licence, architecture, deployment, tool parser and cache-dtype instructions.
- **Limitations:** Exact fallback snapshot and Spark tool performance unverified.
- **Use / priority / reader:** Alternative profile, especially if already available — **High**; Ben.
- **Implementation:** https://huggingface.co/nvidia/NVIDIA-Nemotron-Nano-9B-v2/commits/main
- **Rights:** NVIDIA Open Model License Agreement

### [50] NVIDIA-Nemotron-3-Nano-4B-BF16 Model Card and History
- **Author/publisher; year/version:** NVIDIA; Released 2026-03-16; history lists dfaf35d on 2026-03-20.
- **Type / venue:** Original model card; Hugging Face.
[50] https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16 — NVIDIA-Nemotron-3-Nano-4B-BF16 Model Card and History
- **Contribution / method:** A much smaller candidate requiring a different runtime profile. Model-card and history audit
- **Access and reading depth:** Live card/history retrieved; pinned-card fetch failed; Compression lineage, parameter count, context, parser and vLLM requirements.
- **Limitations:** No exact downloaded snapshot or application measurements.
- **Use / priority / reader:** Qualify before assuming 30B is necessary — **High**; Ben.
- **Implementation:** https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16/commits/main
- **Rights:** NVIDIA Nemotron Open Model License

### [51] NVIDIA Nemotron Open Model License
- **Author/publisher; year/version:** NVIDIA; Last modified 2025-12-15.
- **Type / venue:** Primary licence text; NVIDIA.
[51] https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-nemotron-open-model-license — NVIDIA Nemotron Open Model License
- **Contribution / method:** Clarifies that public availability does not erase licence conditions. Direct terms inspection
- **Access and reading depth:** Full terms retrieved; Grant, redistribution, notices, trademarks and warranty terms.
- **Limitations:** Does not govern every Nemotron checkpoint; not legal advice.
- **Use / priority / reader:** Keep exact licence and notices with transferred model artifacts — **Essential**; Ben and Alex.
- **Rights:** This document defines the model licence

### [52] NVIDIA vLLM Release 25.12 and 25.12.post1-py3 Catalogue Entry
- **Author/publisher; year/version:** NVIDIA; 25.12; release-note page updated 2026-10-30; post1 tag visible.
- **Type / venue:** Official release notes and container catalogue; NVIDIA Docs; NGC.
[52] https://docs.nvidia.com/deeplearning/frameworks/vllm-release-notes/rel-25-12.html — NVIDIA vLLM Release 25.12 and 25.12.post1-py3 Catalogue Entry
- **Contribution / method:** Exposes base/post1 distinction and real platform failure modes. Release-note and catalogue comparison
- **Access and reading depth:** Public text retrieved; manifest/config metadata not exposed; Contents, driver guidance, unified-memory and FP8 known issues.
- **Limitations:** Supplied post1 digest and embedded version were not independently verified.
- **Use / priority / reader:** Profile audit and co-resident-memory testing — **Essential**; Ben.
- **Implementation:** https://catalog.ngc.nvidia.com/orgs/nvidia/containers/vllm?version=25.12.post1-py3
- **Rights:** Container-specific terms not fully inspected

### [53] vLLM 0.12.0 Tool Calling
- **Author/publisher; year/version:** vLLM contributors; Documentation v0.12.0.
- **Type / venue:** Versioned runtime documentation; vLLM.
[53] https://docs.vllm.ai/en/v0.12.0/features/tool_calling — vLLM 0.12.0 Tool Calling
- **Contribution / method:** Separates structural validity from semantic correctness and automatic tool selection. API behavior documentation
- **Access and reading depth:** Public full page retrieved; Named, required and automatic calls; parser/template requirements; initial schema compilation.
- **Limitations:** No guarantee of application correctness or every parser combination.
- **Use / priority / reader:** Strict dispatcher and two-stage protocol/domain testing — **Essential**; Ben.
- **Implementation:** https://github.com/vllm-project/vllm/tree/v0.12.0
- **Rights:** Licence file not inspected in this review

### [54] llama.cpp b8268 Function Calling and NVIDIA Local-Inference Announcement
- **Author/publisher; year/version:** ggml-org contributors; Annamalai Chockalingam; b8268 release 2026-03-11; NVIDIA article 2026-01-05.
- **Type / venue:** Tagged original documentation and dated vendor article; GitHub; NVIDIA Technical Blog.
[54] https://raw.githubusercontent.com/ggml-org/llama.cpp/b8268/docs/function-calling.md — llama.cpp b8268 Function Calling and NVIDIA Local-Inference Announcement
- **Contribution / method:** Alternative runtime with explicit template-dependent tool handling. Original runtime documentation
- **Access and reading depth:** Tagged README/function-calling document retrieved; Native/generic format handling, Jinja, quantisation and backend overview.
- **Limitations:** Pinned Spark benchmark file was absent; exact Nemotron tuple not qualified.
- **Use / priority / reader:** Alternative only after equivalent tool tests — **Medium**; Ben.
- **Implementation:** https://github.com/ggml-org/llama.cpp/releases/tag/b8268
- **Rights:** MIT, identified in tagged README

### [55] NVIDIA-Nemotron-Nano-9B-v2-DGX-Spark NIM Catalogue
- **Author/publisher; year/version:** NVIDIA; Collection lists 1.0.0-variant modified 2025-10-14.
- **Type / venue:** Official container catalogue; NGC.
[55] https://catalog.ngc.nvidia.com/orgs/nim/teams/nvidia/containers/nvidia-nemotron-nano-9b-v2-dgx-spark — NVIDIA-Nemotron-Nano-9B-v2-DGX-Spark NIM Catalogue
- **Contribution / method:** Confirms a Spark-specific NIM route exists. Catalogue inspection
- **Access and reading depth:** Public metadata; container access gated; Product identity, access notice and collection date.
- **Limitations:** No entitlement, image, parser, profile or performance verification.
- **Use / priority / reader:** Reuse only if organiser supplies authorised access — **Medium**; Ben.
- **Implementation:** https://catalog.ngc.nvidia.com/orgs/nvidia/-/collections/dgx-spark/-/artifacts
- **Rights:** NIM access and software terms require separate verification

### [56] ReAct: Synergizing Reasoning and Acting in Language Models
- **Author/publisher; year/version:** Shunyu Yao; Jeffrey Zhao; Dian Yu; Nan Du; Izhak Shafran; Karthik Narasimhan; Yuan Cao; v1 2022-10-06; inspected v3 2023-03-10.
- **Type / venue:** Full research paper; ICLR 2023.
[56] https://arxiv.org/html/2210.03629v3 — ReAct: Synergizing Reasoning and Acting in Language Models
- **DOI:** 10.48550/arXiv.2210.03629
- **Contribution / method:** Supports observation-dependent investigation as an architectural hypothesis. Prompting and ablations across QA and interactive environments
- **Access and reading depth:** Full HTML retrieved; Method, action spaces, baselines, failure analysis and risk discussion.
- **Limitations:** No same-tools tree-planning/manual comparison; restricted experimental action spaces.
- **Use / priority / reader:** Narrow action-observation loop — **High**; Ben.
- **Implementation:** https://react-lm.github.io/
- **Rights:** Not independently resolved

### [57] ReWOO: Decoupling Reasoning from Observations for Efficient Augmented Language Models
- **Author/publisher; year/version:** Binfeng Xu; Zhiyuan Peng; Bowen Lei; Subhabrata Mukherjee; Yuchen Liu; Dongkuan Xu; v1, 2023-05-23.
- **Type / venue:** Full research paper; arXiv.
[57] https://arxiv.org/html/2305.18323v1 — ReWOO: Decoupling Reasoning from Observations for Efficient Augmented Language Models
- **DOI:** 10.48550/arXiv.2305.18323
- **Contribution / method:** Motivates deterministic execution of known dependencies. Modular planning/execution and NLP benchmark comparisons
- **Access and reading depth:** Full HTML retrieved; Plan-work-solve method, experiments and observation-dependence limitation.
- **Limitations:** Foreseeable plans struggle when environment observations determine later actions.
- **Use / priority / reader:** Hybrid controller rather than unconditional long model-generated plans — **Medium**; Ben.
- **Implementation:** https://github.com/billxbf/ReWOO
- **Rights:** Paper CC BY 4.0; repository licence not audited

### [58] LangChain and LangGraph Agent Frameworks Reach v1.0 Milestones
- **Author/publisher; year/version:** Sydney Runkle and the LangChain OSS team; 2025-10-22; supplemental live persistence/interrupt documentation.
- **Type / venue:** Official release announcement and framework documentation; LangChain.
[58] https://www.langchain.com/blog/langchain-langgraph-1dot0 — LangChain and LangGraph Agent Frameworks Reach v1.0 Milestones
- **Contribution / method:** A framework option for persistent control flow. Release and API documentation
- **Access and reading depth:** Public full announcement and documentation retrieved; Durable state, human interruption, deterministic/agentic composition and replay semantics.
- **Limitations:** Current interrupt APIs are not all v1.0 APIs; application authority remains external.
- **Use / priority / reader:** Optional orchestration, with idempotent backend jobs — **Medium**; Ben.
- **Implementation:** https://github.com/langchain-ai/langgraph
- **Rights:** Not independently licence-file audited

### [59] NeMo Agent Toolkit 1.3.1: ReAct Agent and Workflow Evaluation
- **Author/publisher; year/version:** NVIDIA and contributors; v1.3.1, 2025-11-07.
- **Type / venue:** Tagged original repository documentation; GitHub; NVIDIA Docs.
[59] https://raw.githubusercontent.com/NVIDIA/NeMo-Agent-Toolkit/v1.3.1/docs/source/workflows/about/react-agent.md — NeMo Agent Toolkit 1.3.1: ReAct Agent and Workflow Evaluation
- **Contribution / method:** Identifies reusable components and defaults requiring an explicit override. Tagged implementation-documentation audit
- **Access and reading depth:** Tagged README, changelog, agent and evaluation documents retrieved; Configuration defaults, retry/normalisation/history behavior and evaluator extension.
- **Limitations:** Not a claim about newest NAT; no ARM64 installation or domain integration tested.
- **Use / priority / reader:** Optional profiling/evaluation adapter; avoid unnecessary replatforming — **High**; Ben.
- **Implementation:** https://github.com/NVIDIA/NeMo-Agent-Toolkit/tree/v1.3.1
- **Rights:** Apache-2.0

### [60] AI Agents That Matter
- **Author/publisher; year/version:** Sayash Kapoor; Benedikt Stroebl; Zachary S. Siegel; Nitya Nadgir; Arvind Narayanan; v1, 2024-07-01.
- **Type / venue:** Full research paper; arXiv.
[60] https://arxiv.org/html/2407.01502v1 — AI Agents That Matter
- **DOI:** 10.48550/arXiv.2407.01502
- **Contribution / method:** Primary basis for fair cost/quality comparison and avoiding agent theatre. Benchmark audits, comparative experiments and cost-accuracy analysis
- **Access and reading depth:** Full HTML retrieved; Cost-controlled evaluation, holdouts, benchmark shortcuts and reproducibility statement.
- **Limitations:** Does not provide a ready-made spatial-planning benchmark.
- **Use / priority / reader:** B11 benchmark design — **Essential**; All three developers.
- **Implementation:** https://github.com/benediktstroebl/agent-evals
- **Rights:** Reproduction code MIT according to paper; paper licence not resolved

### [61] tau-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains
- **Author/publisher; year/version:** Shunyu Yao; Noah Shinn; Pedram Razavi; Karthik Narasimhan; v1, 2024-06-17.
- **Type / venue:** Full research paper; arXiv.
[61] https://arxiv.org/html/2406.12045v1 — tau-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains
- **DOI:** 10.48550/arXiv.2406.12045
- **Contribution / method:** Repeated reliability and policy-compliance evaluation. API environments, simulated users, annotated goal states and repeated trials
- **Access and reading depth:** Full HTML retrieved; Task construction, state checking, pass^k, methods and failure analysis.
- **Limitations:** Final-state reward can miss policy violations; simulated users differ from actual managers.
- **Use / priority / reader:** Check both final state and approval/action history — **Essential**; Ben and Alex.
- **Implementation:** https://github.com/sierra-research/tau-bench
- **Rights:** Paper CC BY 4.0; code licence not audited

### [62] AgentDojo: A Dynamic Environment to Evaluate Attacks and Defenses for LLM Agents
- **Author/publisher; year/version:** Edoardo Debenedetti; Jie Zhang; Mislav Balunović; Luca Beurer-Kellner; Marc Fischer; Florian Tramèr; v1, 2024-06-19.
- **Type / venue:** Full research paper; arXiv.
[62] https://arxiv.org/html/2406.13352v1 — AgentDojo: A Dynamic Environment to Evaluate Attacks and Defenses for LLM Agents
- **DOI:** 10.48550/arXiv.2406.13352
- **Contribution / method:** Grounds adversarial tests in legitimate task utility as well as attack failure. Executable tool environments with deterministic outcome checks
- **Access and reading depth:** Full HTML retrieved; Environment/state checks, attack surfaces, utility-security results and tool-isolation limitations.
- **Limitations:** Benchmark attack distribution is not application security certification.
- **Use / priority / reader:** Imported-text injection and overblocking tests — **Essential**; Ben and Alex.
- **Implementation:** https://github.com/ethz-spylab/agentdojo
- **Rights:** Not independently resolved

### [63] Ignored, Not Refused: What Low Prompt-Injection Success Rates Hide in Small Tool-Using Agents
- **Author/publisher; year/version:** Farhan Zarif; Kazi Shahid Ahmed Galib; Synthia Akter Promi; Shabnam Sharmin Tarin; Ariyan Hossain; Sadif Ahmed; Farig Yousuf Sadeque; v1, 2026-10-16.
- **Type / venue:** Full research preprint; arXiv.
[63] https://arxiv.org/html/2610.23254v1 — Ignored, Not Refused: What Low Prompt-Injection Success Rates Hide in Small Tool-Using Agents
- **DOI:** 10.48550/arXiv.2610.23254
- **Contribution / method:** Shows why failed attacks must be separated from successful useful defense. Trajectory audit of small agents with a human-checked LLM judge
- **Access and reading depth:** Full HTML and version metadata retrieved; Study design, outcome matrix, prompt/precision sensitivity and limitations.
- **Limitations:** Static synthetic attacks; one judge; heterogeneous interfaces; no sampling-variance measurement.
- **Use / priority / reader:** Joint safe/useful outcomes for smaller model selection — **High**; Ben and Alex.
- **Rights:** Not independently resolved

### [64] Value of Information: Sensitivity Analysis and Research Design in Bayesian Evidence Synthesis
- **Author/publisher; year/version:** Christopher Jackson; Anne Presanis; Stefano Conti; Daniela De Angelis; arXiv v1 submitted 2017-03-27; PDF dated 2017-03-28; later journal reference 2019.
- **Type / venue:** Full methodological paper; arXiv version; Journal of the American Statistical Association.
[64] https://arxiv.org/pdf/1703.08994 — Value of Information: Sensitivity Analysis and Research Design in Bayesian Evidence Synthesis
- **DOI:** 10.1080/01621459.2018.1562932
- **Contribution / method:** Distinguishes decision value from raw output sensitivity. Bayesian decision analysis and expected-loss reduction
- **Access and reading depth:** Full 31-page PDF text retrieved; Decision/loss formulation, EVPI/EVPPI/EVSI definitions and computational approach.
- **Limitations:** Requires probabilistic assumptions absent from the current project; health example is not tree validation.
- **Use / priority / reader:** Use scenario robustness now; reserve formal VOI terminology — **High**; Arnav and Ben.
- **Rights:** Not independently resolved

### [65] Serve LLMs with vLLM on One Device — Intermediate
- **Author/publisher; year/version:** NVIDIA; Undated live Markdown retrieved during review.
- **Type / venue:** Official operational playbook; NVIDIA Build.
[65] https://build.nvidia.com/spark/vllm/intermediate.md — Serve LLMs with vLLM on One Device — Intermediate
- **Contribution / method:** Operational guidance and evidence of live recipe drift. Vendor instructions
- **Access and reading depth:** Public full Markdown retrieved; Network/SSH, Sync, Docker-group warning and memory/model table.
- **Limitations:** 64 GB row and current model choices lack independently established historical publication dates.
- **Use / priority / reader:** Reference only after assigned-device verification — **Medium**; Ben.
- **Rights:** Not inspected

### [66] NeMo Guardrails v0.16.0 README and Changelog
- **Author/publisher; year/version:** NVIDIA and contributors; v0.16.0, 2025-08-29.
- **Type / venue:** Tagged original repository documentation; GitHub.
[66] https://raw.githubusercontent.com/NVIDIA-NeMo/Guardrails/v0.16.0/README.md — NeMo Guardrails v0.16.0 README and Changelog
- **Contribution / method:** Explains programmable input/dialog/retrieval/execution/output controls. Framework documentation inspection
- **Access and reading depth:** Tagged README and changelog retrieved; Rail types, configuration behavior and release limitations.
- **Limitations:** Inspected release labels itself beta; configured rails still require testing and backend authority.
- **Use / priority / reader:** Optional framework; deterministic contract checks remain mandatory — **Medium**; Ben.
- **Implementation:** https://github.com/NVIDIA-NeMo/Guardrails/tree/v0.16.0
- **Rights:** Apache-2.0

### [67] Solar Position Algorithm for Solar Radiation Applications (Revised)
- **Author/publisher; year/version:** Ibrahim Reda; Afshin Andreas; Revised January 2008; NREL/TP-560-34302.
- **Type / venue:** Technical report; National Renewable Energy Laboratory.
[67] https://www.nlr.gov/docs/fy08osti/34302.pdf — Solar Position Algorithm for Solar Radiation Applications (Revised)
- **DOI:** 10.2172/15003974
- **Contribution / method:** Authoritative solar-position conventions and a published reference example. Astronomical solar-position calculation with topocentric and refraction treatment.
- **Access and reading depth:** Full 40-page PDF retrieved; initial SPA website failed; later PDF searches timed out; Report conventions, time-scale introduction and procedure overview inspected; not every astronomical table independently checked.
- **Limitations:** Algorithm uncertainty is not shadow-boundary accuracy or site-input accuracy.
- **Use / priority / reader:** Solar-direction contract and reference verification. — **Essential**; Arnav.
- **Rights:** Unknown; report access does not establish SPA source-code licensing

### [68] pvlib 0.13.1 solar-position interfaces and release provenance
- **Author/publisher; year/version:** pvlib python Developers; 0.13.1; released 2025-09-24; publishing commit 6b9476b90892bd05726b237d9098f7536568a43a.
- **Type / venue:** Versioned documentation and package record; pvlib / PyPI.
[68] https://pvlib-python.readthedocs.io/en/v0.13.1/reference/generated/pvlib.solarposition.get_solarposition.html — pvlib 0.13.1 solar-position interfaces and release provenance
- **Contribution / method:** Timezone behavior, geographic signs, method selection and apparent/geometric angle distinction. Python wrapper with documented NREL SPA implementations.
- **Access and reading depth:** Versioned API pages and PyPI release record retrieved; get_solarposition and spa_python parameters/returns; release date, license and provenance inspected.
- **Limitations:** No installation or platform test; release documentation is not runtime compatibility evidence.
- **Use / priority / reader:** Pin the astronomy dependency and explicit returned columns. — **Essential**; Arnav; Ben.
- **Implementation:** https://github.com/pvlib/pvlib-python/tree/6b9476b90892bd05726b237d9098f7536568a43a
- **Rights:** BSD-3-Clause according to version-specific PyPI record

### [69] SOLWEIG 1.0 – Modelling spatial variations of 3D radiant fluxes and mean radiant temperature in complex urban settings
- **Author/publisher; year/version:** Fredrik Lindberg; Björn Holmer; Sofia Thorsson; Published online 2008-06-04; SOLWEIG 1.0.
- **Type / venue:** Peer-reviewed model paper; International Journal of Biometeorology 52, 697–713.
[69] https://link.springer.com/article/10.1007/s00484-008-0162-7 — SOLWEIG 1.0 – Modelling spatial variations of 3D radiant fluxes and mean radiant temperature in complex urban settings
- **DOI:** 10.1007/s00484-008-0162-7
- **Contribution / method:** Directional radiation-to-MRT pathway and historical model limitations. 2.5-D geometry; six-direction shortwave/longwave calculations; comparison with Göteborg measurements.
- **Access and reading depth:** Publisher abstract; author-uploaded full paper publicly retrieved; Radiation equations, geometry, evaluation and model-performance discussion inspected.
- **Limitations:** Original version did not yet include the later vegetation scheme; limited validation settings.
- **Use / priority / reader:** Define the boundary between shade and a future comfort model. — **Essential**; Arnav.
- **Implementation:** https://github.com/UMEP-dev/UMEP
- **Rights:** Paper copyright retained; current UMEP code has a separate GPL license

### [70] Urban Multi-scale Environmental Predictor (UMEP): An integrated tool for city-based climate services
- **Author/publisher; year/version:** Fredrik Lindberg; C. S. B. Grimmond; Andrew Gabey; Bei Huang; Christoph W. Kent; Ting Sun; Natalie E. Theeuwes; Leena Järvi; Helen C. Ward; I. Capel-Timms; Yuanyong Chang; Per Jonsson; Niklas Krave; Dongwei Liu; D. Meyer; K. Frans G. Olofson; Jianguo Tan; Dag Wästberg; Lingbo Xue; Zhe Zhang; January 2018 journal issue.
- **Type / venue:** Peer-reviewed software/model ecosystem paper; Environmental Modelling & Software 99, 70–87.
[70] https://researchportal.helsinki.fi/en/publications/urban-multi-scale-environmental-predictor-umep-an-integrated-tool — Urban Multi-scale Environmental Predictor (UMEP): An integrated tool for city-based climate services
- **DOI:** 10.1016/j.envsoft.2017.09.020
- **Contribution / method:** Foundational provenance for the UMEP ecosystem. Integrated GIS climate-service framework; detailed methods not reviewed.
- **Access and reading depth:** Institutional metadata retrieved; publisher 403; Reading PDF blocked by Anubis; Helsinki PDF 403; Metadata and indexed abstract only; full text remains a gap.
- **Limitations:** Does not establish current package behavior or compatibility.
- **Use / priority / reader:** Prior-art citation and future model-reuse investigation. — **High**; Arnav; Alex.
- **Implementation:** https://github.com/UMEP-dev/UMEP
- **Rights:** Institutional record identifies paper CC BY-NC-ND; software separately licensed

### [71] Climate-sensitive Urban Planning through Optimization of Tree Placements
- **Author/publisher; year/version:** Simon Schrodi; Ferdinand Briegel; Max Argus; Andreas Christen; Thomas Brox; arXiv:2310.05691v1; 2023-10-09.
- **Type / venue:** Research preprint; arXiv.
[71] https://arxiv.org/pdf/2310.05691v1 — Climate-sensitive Urban Planning through Optimization of Tree Placements
- **DOI:** 10.48550/arXiv.2310.05691
- **Contribution / method:** Surrogate-assisted placement and aggregation prior art. Learned MRT/SVF models and iterated local search.
- **Access and reading depth:** Full 16-page versioned PDF retrieved; Methods, convergence assumptions, experiments, final evaluator, limitations and input appendix inspected.
- **Limitations:** Single-city, uniform-profile assumptions; final assessment remains model-based; feasibility omissions.
- **Use / priority / reader:** Future upgrade reference, not an event-day dependency. — **High**; Arnav; Ben.
- **Implementation:** https://github.com/lmb-freiburg/tree-planting
- **Rights:** Paper license not verified; repository separately MIT

### [72] Official repository for Climate-sensitive Urban Planning Through Optimization of Tree Placements
- **Author/publisher; year/version:** lmb-freiburg; Unpinned main branch; commit history retrieval failed.
- **Type / venue:** Original public research software; GitHub.
[72] https://github.com/lmb-freiburg/tree-planting — Official repository for Climate-sensitive Urban Planning Through Optimization of Tree Placements
- **Contribution / method:** Reveals practical reproduction dependencies distinct from the paper. Research training and optimisation scripts.
- **Access and reading depth:** README, file listing and selected optimize.py text retrieved; Setup/data statements, training workflow and device assumption inspected; no execution.
- **Limitations:** Data-sharing permission unresolved in README; no verified weights, environment or Spark support.
- **Use / priority / reader:** Inspect as research reference before considering reuse. — **Medium**; Ben; Arnav.
- **Implementation:** https://github.com/lmb-freiburg/tree-planting/blob/main/optimize.py
- **Rights:** MIT shown on project page

### [73] Modification of Human-Biometeorologically Significant Radiant Flux Densities by Shading as Local Method to Mitigate Heat Stress in Summer within Urban Street Canyons
- **Author/publisher; year/version:** Hyunjung Lee; Jutta Holst; Helmut Mayer; 2013-06-26.
- **Type / venue:** Peer-reviewed field research; Advances in Meteorology, article 312572.
[73] https://onlinelibrary.wiley.com/doi/10.1155/2013/312572 — Modification of Human-Biometeorologically Significant Radiant Flux Densities by Shading as Local Method to Mitigate Heat Stress in Summer within Urban Street Canyons
- **DOI:** 10.1155/2013/312572
- **Contribution / method:** Measured distinction between air temperature, radiant load and PET. Freiburg building/tree-shading campaigns with directional radiation measurements.
- **Access and reading depth:** Full HTML paper retrieved; Measurement design, radiation mechanisms, results and conclusions inspected.
- **Limitations:** Particular street geometry and summer weather; no transferable Sheffield coefficient.
- **Use / priority / reader:** Mechanism explanation and future radiation-validation design. — **High**; Arnav; Alex.
- **Rights:** Open access; exact license version not verified

### [74] Transmissivity of solar radiation through crowns of single urban trees—application for outdoor thermal comfort modelling
- **Author/publisher; year/version:** Janina Konarska; Fredrik Lindberg; Annika Larsson; Sofia Thorsson; Björn Holmer; Published online 19 September 2013; journal volume 117, 363–376, 2014.
- **Type / venue:** Peer-reviewed measurement and modelling paper; Theoretical and Applied Climatology.
[74] https://link.springer.com/article/10.1007/s00704-013-1000-3 — Transmissivity of solar radiation through crowns of single urban trees—application for outdoor thermal comfort modelling
- **DOI:** 10.1007/s00704-013-1000-3
- **Contribution / method:** Direct evidence that leaf-off crowns retain substantial obstruction Paired radiation measurements for five trees over nine clear days; SOLWEIG comparison
- **Access and reading depth:** Author-deposited full text fetched through ResearchGate; Experimental description, transmission results, modelling limitations and conclusions inspected.
- **Limitations:** Small sample, selected trees and conditions; not Sheffield or universal species coefficients
- **Use / priority / reader:** Seasonal sensitivity design and field-validation protocol — **Essential**; Arnav.
- **Rights:** Copyrighted author deposit; no reusable software licence established

### [75] Impact of shading on evapotranspiration and water stress of urban trees
- **Author/publisher; year/version:** Laura Tams; Eva Nora Paton; Björn Kluge; 2023-05-23.
- **Type / venue:** Peer-reviewed modelling study; Ecohydrology 16, e2556.
[75] https://onlinelibrary.wiley.com/doi/10.1002/eco.2556 — Impact of shading on evapotranspiration and water stress of urban trees
- **DOI:** 10.1002/eco.2556
- **Contribution / method:** Water availability changes the timing of actual evaporative cooling. Urban tree water model with Penman–Monteith and a soil-water bucket.
- **Access and reading depth:** Full HTML paper retrieved; Shading model, water-supply scenarios, parameterisation and temporal results inspected.
- **Limitations:** Specified Berlin/Potsdam forcing and tree/soil assumptions; not a Sheffield calibration.
- **Use / priority / reader:** Separate geometric shade from water-dependent cooling claims. — **High**; Arnav; Alex.
- **Rights:** Open access; exact license version not verified

### [76] Aerodynamic effects of trees on pollutant concentration in street canyons
- **Author/publisher; year/version:** Riccardo Buccolieri; Christof Gromke; Silvana Di Sabatino; Bodo Ruck; 2009; journal issue 2009-09-15.
- **Type / venue:** Peer-reviewed wind-tunnel/CFD research; Science of the Total Environment 407, 5247–5256.
[76] https://publikationen.bibliothek.kit.edu/1000032014 — Aerodynamic effects of trees on pollutant concentration in street canyons
- **DOI:** 10.1016/j.scitotenv.2009.06.016
- **Contribution / method:** Evidence that tree aerodynamic obstruction can reduce canyon air exchange. Wind-tunnel flow/tracer measurements with numerical comparison, as described in abstract.
- **Access and reading depth:** Institutional abstract retrieved; publisher full-text request returned 403; Abstract-only evidence; indexed publisher excerpts also found.
- **Limitations:** Full methods not reviewed; configuration-dependent and unsuitable for numeric transfer.
- **Use / priority / reader:** Keep ventilation/pollution outside the shade claim. — **Medium**; Alex; Arnav.
- **Rights:** Unknown

### [77] An analysis of approximations for maximizing submodular set functions—I
- **Author/publisher; year/version:** G. L. Nemhauser; L. A. Wolsey; M. L. Fisher; December 1978.
- **Type / venue:** Foundational optimisation paper; Mathematical Programming 14, 265–294.
[77] https://link.springer.com/article/10.1007/BF01588971 — An analysis of approximations for maximizing submodular set functions—I
- **DOI:** 10.1007/BF01588971
- **Contribution / method:** Conditional cardinality-greedy approximation theorem. Worst-case analysis of submodular maximisation heuristics.
- **Access and reading depth:** Publisher abstract retrieved; attempted public PDF mirror returned 404; Abstract-only; original full proof not inspected.
- **Limitations:** Does not cover arbitrary budget/conflict/winter constraints.
- **Use / priority / reader:** Precisely bounded guarantee for a simplified reference case. — **High**; Arnav.
- **Rights:** Unknown

### [78] A note on maximizing a submodular set function subject to a knapsack constraint
- **Author/publisher; year/version:** Maxim Sviridenko; January 2004.
- **Type / venue:** Foundational optimisation paper; Operations Research Letters 32, 41–43.
[78] https://www.sciencedirect.com/science/article/abs/pii/S0167637703000622 — A note on maximizing a submodular set function subject to a knapsack constraint
- **DOI:** 10.1016/S0167-6377(03)00062-2
- **Contribution / method:** Knapsack-specific approximation result distinct from cardinality greedy. Submodular maximisation algorithm; later full paper S14 supplies accessible algorithm discussion.
- **Access and reading depth:** Indexed publisher abstract/introduction available; direct retrieval 403; Abstract-only; full algorithm/proof not reviewed.
- **Limitations:** No basis for claiming the project's generic greedy implementation inherits its theorem.
- **Use / priority / reader:** Historical theorem provenance with explicit access limitation. — **Medium**; Arnav.
- **Rights:** Unknown

### [79] Practical Budgeted Submodular Maximization
- **Author/publisher; year/version:** Moran Feldman; Zeev Nutov; Elad Shoham; arXiv:2007.04937v2; 2021-02-09.
- **Type / venue:** Versioned optimisation research paper; arXiv.
[79] https://arxiv.org/pdf/2007.04937v2 — Practical Budgeted Submodular Maximization
- **DOI:** 10.48550/arXiv.2007.04937
- **Contribution / method:** Distinguishes density greedy, singleton comparison and enumerated initial choices. Approximation analysis under a single knapsack constraint.
- **Access and reading depth:** Full 31-page v2 PDF retrieved; Definitions, Algorithms 1–2, theorem statements and selected proof passages inspected.
- **Limitations:** Does not cover the combined project constraints; complexity depends on the exact algorithm variant.
- **Use / priority / reader:** Design a competent deterministic comparator without unsupported bounds. — **High**; Arnav.
- **Rights:** Not verified for v2

### [80] Robust Submodular Observation Selection
- **Author/publisher; year/version:** Andreas Krause; H. Brendan McMahan; Carlos Guestrin; Anupam Gupta; Published December 2008.
- **Type / venue:** Peer-reviewed optimisation research; Journal of Machine Learning Research 9, 2761–2801.
[80] https://jmlr.org/papers/volume9/krause08b/krause08b.pdf — Robust Submodular Observation Selection
- **Contribution / method:** Explains failure of ordinary greedy guarantees for worst-case objectives. Submodular saturation and bicriterion approximation.
- **Access and reading depth:** Full 41-page PDF retrieved; Robust formulation, counterexample, hardness, SATURATE theorem, resource expansion and selected proof passages inspected.
- **Limitations:** Its theoretical resource expansion cannot satisfy an unchanged hard project budget.
- **Use / priority / reader:** Treat robustness as an explicit constrained policy. — **High**; Arnav.
- **Rights:** Unknown

### [81] CP-SAT Solver
- **Author/publisher; year/version:** Google OR-Tools; Documentation last updated 2024-08-28 UTC.
- **Type / venue:** Official solver documentation; Google for Developers.
[81] https://developers.google.com/optimization/cp/cp_solver — CP-SAT Solver
- **Contribution / method:** Supports an exact encoded-model oracle and honest termination reporting. Integer constraint programming/SAT-based optimisation.
- **Access and reading depth:** Full documentation retrieved; v9.14 release page also inspected; Integer coefficient requirements, solver calls and status meanings read.
- **Limitations:** No package installed; no Spark or project-workload performance verified.
- **Use / priority / reader:** Opaque finite-coverage oracle after comparison with enumeration. — **Essential**; Arnav; Ben.
- **Implementation:** https://github.com/google/or-tools/releases/tag/v9.14
- **Rights:** Documentation CC BY 4.0; samples Apache 2.0; package license should be checked at selected version

### [82] r.sun — GRASS GIS 8.4 manual
- **Author/publisher; year/version:** Jaroslav Hofierka; Marcel Suri; Thomas Huld; GRASS Development Team; 8.4.3dev manual; source-change date 2025-05-06; commit 59db85624e4fd204e389e27e1ddc28028dd3edfc.
- **Type / venue:** Version-specific GIS model documentation; GRASS GIS.
[82] https://grass.osgeo.org/grass84/manuals/r.sun.html — r.sun — GRASS GIS 8.4 manual
- **Contribution / method:** Credible raster/horizon alternative and an independent terrain reference. Raster solar radiation with terrain/horizon visibility.
- **Access and reading depth:** Full manual retrieved; Inputs, modes, horizon reuse, units, timing, resolution and source metadata inspected.
- **Limitations:** Not a ready raised-crown model; coordinate/time conventions require conversion.
- **Use / priority / reader:** Cross-check terrain visibility and document non-RT options. — **High**; Arnav.
- **Implementation:** https://github.com/OSGeo/grass/tree/59db85624e4fd204e389e27e1ddc28028dd3edfc/raster/r.sun
- **Rights:** GNU GPL >=2 according to manual

### [83] UMEP source tree and raster shadowing functions
- **Author/publisher; year/version:** UMEP-dev; Unpinned master branch.
- **Type / venue:** Original public software source; GitHub.
[83] https://github.com/UMEP-dev/UMEP — UMEP source tree and raster shadowing functions
- **Contribution / method:** Concrete raster-array shadow approach distinct from mesh intersection. Directional shifts, height adjustment and raster maxima.
- **Access and reading depth:** README, license label, file listing and shadowingfunctions.py retrieved; Global raster-shadow loop and vegetation-function interface inspected.
- **Limitations:** Current source lacks a verified historical pin here; QGIS/UI dependencies are visible.
- **Use / priority / reader:** Algorithm reference and potential independent comparison after version selection. — **Medium**; Arnav; Ben.
- **Implementation:** https://github.com/UMEP-dev/UMEP/blob/master/Utilities/shadowingfunctions.py
- **Rights:** GPL-3.0 shown on project page

### [84] Deriving the operational procedure for the Universal Thermal Climate Index (UTCI), with original electronic supplement
- **Author/publisher; year/version:** Peter Bröde; Dusan Fiala; Krzysztof Błażejczyk; Ingvar Holmér; Gerd Jendritzky; Bernhard Kampmann; Birger Tinz; George Havenith; Online 2011-05-31; May 2012 journal issue.
- **Type / venue:** Peer-reviewed physiological-index paper and supplement; International Journal of Biometeorology 56, 481–494.
[84] https://link.springer.com/article/10.1007/s00484-011-0454-1 — Deriving the operational procedure for the Universal Thermal Climate Index (UTCI), with original electronic supplement
- **DOI:** 10.1007/s00484-011-0454-1
- **Contribution / method:** Separates physiological equivalent temperature from geometric shade and MRT. Thermoregulation/reference-environment model with polynomial approximation.
- **Access and reading depth:** Main article abstract-only; original 50-page ESM 1–3 PDF retrieved; Main abstract plus supplement definitions, polynomial input conventions/ranges and coefficient section inspected.
- **Limitations:** Main full text inaccessible; polynomial is not a radiation or airflow solver.
- **Use / priority / reader:** Requirements for a later, separately validated UTCI module. — **High**; Arnav.
- **Rights:** Unknown

### [85] Urban greening to cool towns and cities: A systematic review of the empirical evidence
- **Author/publisher; year/version:** Diana E. Bowler; Lisette Buyung-Ali; Teri M. Knight; Andrew S. Pullin; 2010-09-15 journal issue.
- **Type / venue:** Systematic evidence review; Landscape and Urban Planning 97, 147–155.
[85] https://doi.org/10.1016/j.landurbplan.2010.05.006 — Urban greening to cool towns and cities: A systematic review of the empirical evidence
- **DOI:** 10.1016/j.landurbplan.2010.05.006
- **Contribution / method:** Relevant review highlighting limits of transferring observational greening evidence into design prescriptions. Systematic review and meta-analysis, as described in indexed publisher content.
- **Access and reading depth:** Publisher-indexed abstract/introduction/excerpts; direct document retrieval returned 403; Partial indexed evidence only; full review unavailable.
- **Limitations:** Full inclusion criteria and synthesis not independently inspected; no effect size adopted.
- **Use / priority / reader:** Background evidence-quality caution, not project calibration. — **Medium**; Alex.
- **Rights:** Unknown

### [86] Disentangling the relative importance of tree-cast shadows and transpiration in mitigating urban extreme heat
- **Author/publisher; year/version:** Kyeongjoo Park; Jong-Jin Baik; Published 2026-09-04; accepted 2026-08-25; early accepted-article presentation.
- **Type / venue:** Peer-reviewed accepted research article; Scientific Reports.
[86] https://www.nature.com/articles/s41598-026-68979-5 — Disentangling the relative importance of tree-cast shadows and transpiration in mitigating urban extreme heat
- **DOI:** 10.1038/s41598-026-68979-5
- **Contribution / method:** Recent explicit separation of shadow and transpiration mechanisms for canyon air temperature. WRF/urban canopy simulations and factor separation, according to abstract.
- **Access and reading depth:** Publisher abstract and publication information retrieved through PDF-route redirect; full methods unavailable; Abstract-only evidence.
- **Limitations:** Early version can be replaced automatically; no full-method assessment or numeric transfer.
- **Use / priority / reader:** Supports retaining separate mechanism claims. — **Medium**; Alex; Arnav.
- **Rights:** CC BY 4.0 stated on publisher page

### [87] Community Forestry Trees and Planting Areas
- **Author/publisher; year/version:** Sheffield City Council; Publisher record updated 2025-11-27.
- **Type / venue:** Dataset publisher metadata; data.gov.uk.
[87] https://www.data.gov.uk/dataset/49513e78-5dea-4141-a09b-97fd83af525d/community-forestry-trees-and-planting-areas — Community Forestry Trees and Planting Areas
- **Contribution / method:** Establishes planting-record semantics, approximate positions and survival/date limitations Administrative planting records
- **Access and reading depth:** Public metadata; linked service responses inaccessible; Full publisher description and resource links.
- **Limitations:** Not an inventory of surviving trees
- **Use / priority / reader:** Historical context and follow-up verification — **High**; Alex; Arnav.
- **Implementation:** https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/Community_Forestry_Trees/FeatureServer/14
- **Rights:** OGL stated in publisher record; service terms not inspected

### [88] Street Trees
- **Author/publisher; year/version:** Sheffield City Council; Publisher record updated 2026-01-07.
- **Type / venue:** Dataset publisher metadata; data.gov.uk.
[88] https://www.data.gov.uk/dataset/957a85f3-d56b-4aed-9f29-5f8fe1363e57/street-trees — Street Trees
- **Contribution / method:** Street-tree location source and current publisher licence statement Council spatial records
- **Access and reading depth:** Public metadata; service/item inspection failed; Full metadata and resource links.
- **Limitations:** Attributes, completeness, capture dates and crown measurements unverified
- **Use / priority / reader:** Candidate existing-tree cross-check — **High**; Alex.
- **Implementation:** https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/INSPIRE/FeatureServer/14
- **Rights:** OGL on publisher record; discrepancy with supplied INSPIRE caution unresolved

### [89] Sheffield Parks and Countryside Sites
- **Author/publisher; year/version:** Sheffield City Council; Metadata updated 2024-05-21; service links dated 2020-03-03.
- **Type / venue:** Dataset publisher metadata; data.gov.uk.
[89] https://www.data.gov.uk/dataset/90b1db1f-18e1-4e9d-bb52-a4d1c198f6f2/sheffield-parks-and-countryside-sites — Sheffield Parks and Countryside Sites
- **Contribution / method:** Distinguishes service responsibility from ownership Council polygons, some aligned to OS MasterMap
- **Access and reading depth:** Metadata readable; feature response exceeded tool size limit; Description, rights statement and exact resource link.
- **Limitations:** Approximate outlines and mixed ownership/management relationships
- **Use / priority / reader:** Site discovery, subject to rights review — **High**; Alex; Ben.
- **Implementation:** https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/INSPIRE/FeatureServer/12
- **Rights:** Publisher states PSMA licence terms; public redistribution not cleared

### [90] School Localities
- **Author/publisher; year/version:** Sheffield City Council; 2025-01-08.
- **Type / venue:** Dataset publisher metadata; data.gov.uk.
[90] https://www.data.gov.uk/dataset/8f7b83db-35a7-4b33-87bb-d0de851bcdce/school-localities — School Localities
- **Contribution / method:** Prevents administrative locality polygons being mistaken for grounds Seven administrative boundaries
- **Access and reading depth:** Metadata readable; JSON endpoint returned no exposed attributes; Full short description and links.
- **Limitations:** No school parcel or playground geometry
- **Use / priority / reader:** Administrative context only — **High**; Alex.
- **Implementation:** https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/OpenData1/FeatureServer/7
- **Rights:** OGL on publisher record

### [91] LIDAR Composite Digital Terrain Model — 1m
- **Author/publisher; year/version:** Environment Agency; 2022 composite; metadata created 2023-03-09, updated 2025-08-01.
- **Type / venue:** Publisher dataset metadata; Defra / data.gov.uk.
[91] https://ckan.publishing.service.gov.uk/dataset/lidar-composite-digital-terrain-model-dtm-1m — LIDAR Composite Digital Terrain Model — 1m
- **Contribution / method:** Terrain source, spatial resolution, datum and composite-age limits Filtered survey returns, merged/resampled composite
- **Access and reading depth:** Full catalogue description readable; Defra application dynamically rendered; Description, lineage and resource listings.
- **Limitations:** No selected tile or pixel metadata inspected
- **Use / priority / reader:** Terrain and proposed-tree ground attachment — **Critical**; Arnav.
- **Implementation:** https://environment.data.gov.uk/survey
- **Rights:** OGL identified in Defra indexed publisher metadata; CKAN mirror says No Licence Provided

### [92] LIDAR Composite Digital Surface Model — 1m
- **Author/publisher; year/version:** Environment Agency; 2022 composite; metadata updated 2025-08-01.
- **Type / venue:** Publisher dataset metadata; data.gov.uk publisher catalogue.
[92] https://ckan.publishing.service.gov.uk/dataset/lidar-composite-digital-surface-model-dsm-1m — LIDAR Composite Digital Surface Model — 1m
- **Contribution / method:** Last/only-return surface semantics and non-semantic objects Composite of time-stamped and National LiDAR Programme surveys
- **Access and reading depth:** Full catalogue description readable; technical DOCX not retrieved; Description, lineage, dates and resource links.
- **Limitations:** Includes vehicles and vegetation; no local raster inspected
- **Use / priority / reader:** Reviewed static-obstruction reconstruction — **Critical**; Arnav.
- **Implementation:** https://environment.data.gov.uk/dataset/9ba4d5ac-d596-445a-9056-dae3ddec0178
- **Rights:** Mirror licence missing; supplied OGL assertion requires exact product/asset confirmation

### [93] EA LIDAR Composite Catalogues: first-return DSM, last-return DSM and DTM indices
- **Author/publisher; year/version:** Environment Agency; 2022 composite indices; inspected DTM/LZ schema edit date 2024-04-25.
- **Type / venue:** Publisher API schemas; ArcGIS REST Services Directory.
[93] https://services-eu1.arcgis.com/KB6uNVj5ZcJr7jUP/ArcGIS/rest/services/LIDAR_Composite_Catalogues/FeatureServer — EA LIDAR Composite Catalogues: first-return DSM, last-return DSM and DTM indices
- **Contribution / method:** Exact acquisition-provenance fields and return-type distinction Survey-footprint index polygons
- **Access and reading depth:** Layer HTML schemas readable; spatial query responses inaccessible; Layers 0, 1 and 2 descriptions, fields, CRS and query capabilities.
- **Limitations:** Not elevation pixels; mutable, non-versioned service
- **Use / priority / reader:** Resolve survey dates over complete study/context extent — **Critical**; Arnav; Alex.
- **Implementation:** https://services-eu1.arcgis.com/KB6uNVj5ZcJr7jUP/ArcGIS/rest/services/LIDAR_Composite_Catalogues/FeatureServer/1
- **Rights:** Environment Agency copyright displayed; exact index reuse terms not separately resolved

### [94] Weston Park
- **Author/publisher; year/version:** Sheffield City Council; Undated live visitor page.
- **Type / venue:** Official site information; Sheffield City Council.
[94] https://www.sheffield.gov.uk/parks-sport-recreation/parks-gardens/weston-park — Weston Park
- **Contribution / method:** Public-use and bounded-site rationale Council visitor information
- **Access and reading depth:** Public HTML; Visitor facilities, opening, location and heritage sections.
- **Limitations:** No occupancy measurements, survey geometry or planting consent
- **Use / priority / reader:** Primary study-area investigation — **High**; Alex.
- **Rights:** Webpage copyright; no geometry licence established

### [95] Weston Park — National Heritage List entry 1001340
- **Author/publisher; year/version:** Historic England; Registered 1995-12-12; description January 2000, updated October 2004.
- **Type / venue:** Official heritage register; National Heritage List for England.
[95] https://historicengland.org.uk/listing/the-list/list-entry/1001340 — Weston Park — National Heritage List entry 1001340
- **Contribution / method:** Grade II landscape and historical layout constraints Heritage registration and descriptive assessment
- **Access and reading depth:** Public full entry; Designation, grid locator and landscape description.
- **Limitations:** Historical vegetation description is not current inventory
- **Use / priority / reader:** Heritage review and reference locator — **High**; Alex; Arnav.
- **Rights:** Entry/map reuse requires applicable Historic England terms; map not cleared here

### [96] Manor Fields Park
- **Author/publisher; year/version:** The Green Estate CIC; Undated live operator page.
- **Type / venue:** Original operator site information; Green Estate.
[96] https://greenestate.org.uk/ugp-manor-fields-park — Manor Fields Park
- **Contribution / method:** Named owner/operator and drainage/ground-history obstacles Operator description
- **Access and reading depth:** Public full HTML; linked map redirect exposed place coordinates; Ownership, facilities, access and history sections.
- **Limitations:** No surveyed exclusions or planting approval
- **Use / priority / reader:** Fallback bounded playground/path study — **High**; Alex; Arnav.
- **Implementation:** https://maps.app.goo.gl/8JVvRijipapD87rk7
- **Rights:** Operator copyright; photographs not cleared

### [97] The Peace Gardens
- **Author/publisher; year/version:** Sheffield City Council; Undated live visitor page.
- **Type / venue:** Official site information; Sheffield City Council.
[97] https://www.sheffield.gov.uk/parks-sport-recreation/parks-gardens/public-spaces/peace-gardens — The Peace Gardens
- **Contribution / method:** Public use and infrastructure constraints Council visitor/history description
- **Access and reading depth:** Public full HTML; Location, history, water features, access links and management.
- **Limitations:** No underground layout, target polygons or verified numerical locator
- **Use / priority / reader:** Reserve urban shade comparison — **Medium**; Alex.
- **Implementation:** https://www.google.com/maps/dir/Current%2BLocation/peace%2Bgardens%2Bsheffield
- **Rights:** Council webpage copyright; no reusable geometry supplied

### [98] Tree works and protected trees
- **Author/publisher; year/version:** Sheffield City Council; Undated live guidance.
- **Type / venue:** Local authority regulatory guidance; Sheffield City Council.
[98] https://www.sheffield.gov.uk/planning-development/conservation-design/tree-works-protected-trees — Tree works and protected trees
- **Contribution / method:** Root-work protections and limitations of online mapping Local administrative guidance
- **Access and reading depth:** Guidance readable; interactive constraint map not readable; Main guidance and linked TPO/conservation-notice text.
- **Limitations:** No actual site order search completed
- **Use / priority / reader:** Keep protection status and professional checks explicit — **Critical**; Alex; Ben.
- **Implementation:** https://sheffieldcc.maps.arcgis.com/apps/instant/sidebar/index.html?appid=1c5ae0a20ad84a51a807bd737feaeb43
- **Rights:** Constraint-layer reuse terms unverified

### [99] Avoiding danger from underground services — HSG47
- **Author/publisher; year/version:** Health and Safety Executive; Third edition, 2014.
- **Type / venue:** Original official guidance; HSE.
[99] https://www.hse.gov.uk/pubns/priced/hsg47.pdf — Avoiding danger from underground services — HSG47
- **Contribution / method:** Distinguishes mapped records from service identification Safe-work guidance with cases and procedures
- **Access and reading depth:** Full 40-page PDF accessible; Targeted full-text reading: scope and planning/plan-limitations sections, particularly pp. 5 and 10–14.
- **Limitations:** Not a Sheffield utility survey or planting design standard
- **Use / priority / reader:** Survey requirements and provisional feasibility — **Critical**; Alex; Ben.
- **Rights:** Crown copyright 2014; publication contains third-party material

### [100] OS OpenMap — Local: Building feature definition
- **Author/publisher; year/version:** Ordnance Survey; Undated live technical documentation.
- **Type / venue:** Publisher feature specification; OS Download Products documentation.
[100] https://docs.os.uk/os-downloads/products/maps-and-imagery-portfolio/os-openmap-local/os-openmap-local-technical-specification/feature-types/building — OS OpenMap — Local: Building feature definition
- **Contribution / method:** Documents footprint generalisation Generalised mapping product
- **Access and reading depth:** Definition readable; diagram attributes not independently inspected; Building definition and overview.
- **Limitations:** No measured Sheffield building heights established
- **Use / priority / reader:** Contextual semantic cross-check — **Medium**; Arnav.
- **Rights:** OS OpenData product; exact extracted package terms not inspected

### [101] OpenStreetMap Copyright and License
- **Author/publisher; year/version:** OpenStreetMap Foundation and contributors; Undated live licence explanation.
- **Type / venue:** Original data licence guidance; OpenStreetMap.
[101] https://www.openstreetmap.org/copyright — OpenStreetMap Copyright and License
- **Contribution / method:** Separates open database reuse from hosted-service entitlement Licence explanation
- **Access and reading depth:** Public full HTML; Licence, attribution and service-policy sections.
- **Limitations:** No Sheffield OSM features or historical extract inspected
- **Use / priority / reader:** Potential rights-reviewed boundary/footprint source — **High**; Alex; Ben.
- **Rights:** ODbL; attribution and applicable database share-alike obligations

### [102] PVGIS 5 user manual and hourly radiation output documentation
- **Author/publisher; year/version:** European Commission Joint Research Centre; PVGIS 5.3 documented as production since September 2024; manual is mutable.
- **Type / venue:** Original service documentation; JRC.
[102] https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis/using-pvgis-5/pvgis-5-user-manual_en — PVGIS 5 user manual and hourly radiation output documentation
- **Contribution / method:** Radiation components, temporal semantics and version selection Satellite/reanalysis radiation products
- **Access and reading depth:** Full manual and output examples accessible; Database, hourly, TMY, timestamp and output-schema sections.
- **Limitations:** No Sheffield response inspected; examples contain older database names
- **Use / priority / reader:** Optional direct-exposure metric — **Medium**; Arnav.
- **Implementation:** https://re.jrc.ec.europa.eu/api/v5_3/seriescalc
- **Rights:** Exact returned dataset redistribution terms not audited

### [103] ERA5-Land hourly time-series data from 1950 to present
- **Author/publisher; year/version:** Copernicus Climate Change Service / ECMWF; Published 2025-06-04; inspected record update 2026-07-28.
- **Type / venue:** Publisher dataset documentation; Climate Data Store.
[103] https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries — ERA5-Land hourly time-series data from 1950 to present
- **Contribution / method:** Point-series access selects nearest model grid point Offline land reanalysis; regridded time-series subset
- **Access and reading depth:** Public metadata; no account or data retrieval; Method, grid, format and variable table.
- **Limitations:** Coarse model estimates; accumulation semantics require further validation
- **Use / priority / reader:** Optional historical weather context — **Medium**; Arnav.
- **Rights:** CC-BY licence linked by publisher; exact downloaded package not inspected

### [104] HadUK-Grid datasets
- **Author/publisher; year/version:** Met Office; Undated live dataset and format documentation; no release selected.
- **Type / venue:** Publisher dataset documentation; Met Office.
[104] https://www.metoffice.gov.uk/research/climate/maps-and-data/data/haduk-grid/datasets — HadUK-Grid datasets
- **Contribution / method:** Rainfall identifier, units and daily observation boundary Gridded land-surface climate observations
- **Access and reading depth:** Public documentation; NetCDF not retrieved; Variable definitions, periods, grid and separate format description.
- **Limitations:** Grid estimates are not planting-pit observations
- **Use / priority / reader:** Rainfall/dry-period context only — **Medium**; Arnav.
- **Implementation:** https://www.metoffice.gov.uk/research/climate/maps-and-data/data/haduk-grid/data-formats
- **Rights:** OGL stated by Met Office

### [105] Environment Agency Rainfall API reference
- **Author/publisher; year/version:** Environment Agency; Undated live reference with historical examples.
- **Type / venue:** Original API documentation; Defra Data Services Platform.
[105] https://environment.data.gov.uk/flood-monitoring/doc/rainfall — Environment Agency Rainfall API reference
- **Contribution / method:** Observation units, reporting periods, rounded positions and missing-value handling Telemetered tipping-bucket gauges
- **Access and reading depth:** Documentation and embedded schema readable; Sheffield station query failed; Measurement, station, reading, paging and archive sections.
- **Limitations:** No nearest gauge or actual reading inspected
- **Use / priority / reader:** Optional recent rainfall context — **Low**; Arnav.
- **Implementation:** https://environment.data.gov.uk/flood-monitoring/id/stations?parameter=rainfall
- **Rights:** OGL in flood-monitoring service framework; exact extract not obtained

### [106] Tree Equity Score UK — methods and data glossary
- **Author/publisher; year/version:** American Forests; Woodland Trust; Centre for Sustainable Healthcare; Launch in winter 2023; live page advertises an undated 2026 canopy update.
- **Type / venue:** Original methodology; Tree Equity Score UK.
[106] https://uk.treeequityscore.org — Tree Equity Score UK — methods and data glossary
- **Contribution / method:** Neighbourhood prioritisation context and ecological-inference limitations Canopy gap combined with six equally weighted indicators
- **Access and reading depth:** Full methods readable; download button did not expose a verified asset; Geographies, priority indicators, canopy, heat, imputation and benefit methods.
- **Limitations:** Not occupancy, air-temperature monitoring or park-level benefit validation
- **Use / priority / reader:** Contextual site-selection discussion only — **Medium**; Alex; Arnav.
- **Rights:** Download/redistribution licence unresolved; website copyright displayed

### [107] QGIS 3.40 raster extraction and GDAL processing
- **Author/publisher; year/version:** QGIS contributors; Versioned QGIS 3.40 documentation; exact documentation build date unknown.
- **Type / venue:** Original software documentation; QGIS documentation.
[107] https://docs.qgis.org/3.40/en/docs/user_manual/processing_algs/gdal/rasterextraction.html — QGIS 3.40 raster extraction and GDAL processing
- **Contribution / method:** Reusable GUI and processing operations GDAL-backed raster preparation
- **Access and reading depth:** Public detailed documentation; Extent/mask clipping parameters and GDAL linkage; GDAL warp/licence pages also inspected.
- **Limitations:** No installation, compatibility or runtime tests
- **Use / priority / reader:** Offline preprocessing and visual QA — **High**; Arnav.
- **Implementation:** https://gdal.org/en/stable/programs/gdalwarp.html
- **Rights:** QGIS publishes GPL v2 text; GDAL generally MIT with dependency-specific terms

### [108] Rasterio 1.3.11 release metadata and reprojection documentation
- **Author/publisher; year/version:** Rasterio contributors; Sean Gillies; 1.3.11 released 2024-09-04; reprojection page inspected at mutable stable URL.
- **Type / venue:** Original package metadata and documentation; PyPI / Rasterio documentation.
[108] https://pypi.org/project/rasterio/1.3.11 — Rasterio 1.3.11 release metadata and reprojection documentation
- **Contribution / method:** Array-based raster import and alignment Python interface to geospatial raster operations
- **Access and reading depth:** Public metadata/documentation; no distributions downloaded; Release date, licence, raster metadata/windows and reprojection API.
- **Limitations:** Stable documentation is not a pinned 1.3.11 manual
- **Use / priority / reader:** Reproducible preprocessing — **High**; Arnav.
- **Implementation:** https://rasterio.readthedocs.io/en/stable/topics/reproject.html
- **Rights:** BSD according to pinned package metadata

### [109] GeoPandas 0.14.4 — GeoDataFrame.to_crs
- **Author/publisher; year/version:** GeoPandas contributors; 0.14.4 released 2024-04-28.
- **Type / venue:** Original versioned API documentation; GeoPandas / PyPI.
[109] https://geopandas.org/en/v0.14.4/docs/reference/api/geopandas.GeoDataFrame.to_crs.html — GeoPandas 0.14.4 — GeoDataFrame.to_crs
- **Contribution / method:** Explicit vector reprojection Transform active geometry coordinates
- **Access and reading depth:** Public documentation and pinned package metadata; Transformation prerequisites, limitations and set_crs distinction.
- **Limitations:** No automatic source-CRS discovery or 3D survey validation
- **Use / priority / reader:** Vector preparation and export — **High**; Arnav.
- **Implementation:** https://pypi.org/project/geopandas/0.14.4/
- **Rights:** BSD 3-Clause in pinned package metadata

### [110] The Shapely User Manual 2.0.6
- **Author/publisher; year/version:** Sean Gillies; Shapely contributors; 2.0.6, 2024-08-19.
- **Type / venue:** Original versioned software manual; Shapely documentation.
[110] https://shapely.readthedocs.io/en/2.0.6/manual.html — The Shapely User Manual 2.0.6
- **Contribution / method:** Planar masks and explicit 3D limitation GEOS-based computational geometry
- **Access and reading depth:** Full manual accessible; Targeted full-text reading: planar model, operations, transforms and dimensional limitations.
- **Limitations:** Height ignored in geometric analysis
- **Use / priority / reader:** Target/exclusion topology, not ray tracing — **High**; Arnav; Ben.
- **Implementation:** https://pypi.org/project/shapely/2.0.6/
- **Rights:** Software BSD 3-Clause; GEOS LGPL 2.1; manual CC BY 3.0 US

### [111] pyproj 3.6.1 advanced examples
- **Author/publisher; year/version:** pyproj contributors; 3.6.1 released 2023-09-21.
- **Type / venue:** Original versioned software documentation; pyproj / PyPI.
[111] https://pyproj4.github.io/pyproj/3.6.1/advanced_examples.html — pyproj 3.6.1 advanced examples
- **Contribution / method:** Auditable transformation selection PROJ coordinate transformations
- **Access and reading depth:** Public versioned documentation and package metadata; TransformationGroup, missing grids, area of interest and 3D promotion.
- **Limitations:** Correct grids/CRS and local validation remain necessary
- **Use / priority / reader:** Offline coordinate pipeline — **Critical**; Arnav.
- **Implementation:** https://pypi.org/project/pyproj/3.6.1/
- **Rights:** MIT in pinned package metadata

### [112] OS Open Greenspace technical specification, product details and attribute mapping
- **Author/publisher; year/version:** Ordnance Survey; Undated live specification; product page states six-monthly updates.
- **Type / venue:** Publisher dataset schema; OS Download Products documentation.
[112] https://docs.os.uk/os-downloads/products/land-and-terrain-portfolio/os-open-greenspace/os-open-greenspace-technical-specification/attribute-mapping — OS Open Greenspace technical specification, product details and attribute mapping
- **Contribution / method:** Alternative site/access geometry with explicit identifiers Generalised large-scale mapping
- **Access and reading depth:** Detailed schema/product pages accessible; data extract not obtained; Formats, attributes, CRS, generalisation and school-field exclusions.
- **Limitations:** Likely public access, not ownership or surveyed plantability
- **Use / priority / reader:** Candidate park/play-space discovery — **High**; Alex; Arnav.
- **Implementation:** https://www.ordnancesurvey.co.uk/products/os-open-greenspace
- **Rights:** OS OpenData; exact package licence/attribution text requires confirmation

### [113] Coordinate tools and resources; OSTN15/OSGM15 transformations
- **Author/publisher; year/version:** Ordnance Survey; Transformation models introduced August 2016; guidance undated/live.
- **Type / venue:** Original geodetic guidance; Ordnance Survey.
[113] https://www.ordnancesurvey.co.uk/geodesy-positioning/coordinate-transformations/resources — Coordinate tools and resources; OSTN15/OSGM15 transformations
- **Contribution / method:** Distinguishes datum transformation from simple coordinate conversion National grid/geoid transformations
- **Access and reading depth:** Public guidance; grid archives not downloaded; Transformation accuracy, convergence, scale and model resources.
- **Limitations:** No Sheffield transformation executed
- **Use / priority / reader:** True-north and vertical-datum validation — **Critical**; Arnav.
- **Implementation:** https://www.ordnancesurvey.co.uk/geodesy-positioning/coordinate-transformations
- **Rights:** GridInQuest software BSD; exact grid-package terms not inspected

### [114] Sustainable Drainage System Regions
- **Author/publisher; year/version:** Sheffield City Council; Publisher metadata updated 2024-04-11.
- **Type / venue:** Dataset publisher metadata; data.gov.uk.
[114] https://www.data.gov.uk/dataset/7ebd8e69-ceae-41c0-ab79-163adef6b423/sustainable-drainage-system-regions — Sustainable Drainage System Regions
- **Contribution / method:** Potential drainage-conflict screening with explicit accuracy warning Council historical/current administrative information
- **Access and reading depth:** Metadata readable; service JSON exposed no readable records; Full description, licence and exact service link.
- **Limitations:** Indicative positions; no site-level match established
- **Use / priority / reader:** Contextual constraints, especially Manor Fields — **Medium**; Alex; Arnav.
- **Implementation:** https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/OpenData_FloodAndWaterManagement/MapServer/12
- **Rights:** OGL on publisher record

### [115] Sheffield Community Forestry Trees
- **Author/publisher; year/version:** Sheffield City Council; Live service inspection, 11 November 2026; records retain distinct acquisition dates.
- **Type / venue:** Primary ArcGIS REST metadata and query; Publisher service.
[115] https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/Community_Forestry_Trees/FeatureServer/14 — Sheffield Community Forestry Trees — live service metadata and bounded query
- **Contribution / method:** Verifies this council layer’s actual field names, geometry type, CRS and bounded sample semantics; no EA survey result is attributed to this council source Direct metadata and attribute inspection
- **Access and reading depth:** HTTP 200 JSON; Full schema/CRS and bounded attribute samples; no raster or site mesh.
- **Limitations:** Not full inventory, accepted geometry, plantability or rights clearance
- **Use / priority / reader:** B03 source/schema/coordinate preflight — **Essential**; Alex; Arnav.
- **Rights:** Source-specific; see section 5

### [116] Sheffield Community Forestry Tree Planting Areas
- **Author/publisher; year/version:** Sheffield City Council; Live service inspection, 11 November 2026; records retain distinct acquisition dates.
- **Type / venue:** Primary ArcGIS REST metadata and query; Publisher service.
[116] https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/Community_Forestry_Tree_Planting_Areas/FeatureServer/19 — Sheffield Community Forestry Tree Planting Areas — live service metadata and bounded query
- **Contribution / method:** Verifies this council layer’s actual field names, geometry type, CRS and bounded sample semantics; no EA survey result is attributed to this council source Direct metadata and attribute inspection
- **Access and reading depth:** HTTP 200 JSON; Full schema/CRS and bounded attribute samples; no raster or site mesh.
- **Limitations:** Not full inventory, accepted geometry, plantability or rights clearance
- **Use / priority / reader:** B03 source/schema/coordinate preflight — **Essential**; Alex; Arnav.
- **Rights:** Source-specific; see section 5

### [117] Sheffield Street Trees
- **Author/publisher; year/version:** Sheffield City Council; Live service inspection, 11 November 2026; records retain distinct acquisition dates.
- **Type / venue:** Primary ArcGIS REST metadata and query; Publisher service.
[117] https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/INSPIRE/FeatureServer/14 — Sheffield Street Trees — live service metadata and bounded query
- **Contribution / method:** Verifies this council layer’s actual field names, geometry type, CRS and bounded sample semantics; no EA survey result is attributed to this council source Direct metadata and attribute inspection
- **Access and reading depth:** HTTP 200 JSON; Full schema/CRS and bounded attribute samples; no raster or site mesh.
- **Limitations:** Not full inventory, accepted geometry, plantability or rights clearance
- **Use / priority / reader:** B03 source/schema/coordinate preflight — **Essential**; Alex; Arnav.
- **Rights:** Source-specific; see section 5

### [118] Sheffield Parks and Countryside Sites
- **Author/publisher; year/version:** Sheffield City Council; Live service inspection, 11 November 2026; records retain distinct acquisition dates.
- **Type / venue:** Primary ArcGIS REST metadata and query; Publisher service.
[118] https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/INSPIRE/FeatureServer/12 — Sheffield Parks and Countryside Sites — live service metadata and bounded query
- **Contribution / method:** Verifies this council layer’s actual field names, geometry type, CRS and bounded sample semantics; no EA survey result is attributed to this council source Direct metadata and attribute inspection
- **Access and reading depth:** HTTP 200 JSON; Full schema/CRS and bounded attribute samples; no raster or site mesh.
- **Limitations:** Not full inventory, accepted geometry, plantability or rights clearance
- **Use / priority / reader:** B03 source/schema/coordinate preflight — **Essential**; Alex; Arnav.
- **Rights:** Source-specific; see section 5

### [119] Sheffield School Localities
- **Author/publisher; year/version:** Sheffield City Council; Live service inspection, 11 November 2026; records retain distinct acquisition dates.
- **Type / venue:** Primary ArcGIS REST metadata and query; Publisher service.
[119] https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/OpenData1/FeatureServer/7 — Sheffield School Localities — live service metadata and bounded query
- **Contribution / method:** Verifies this council layer’s actual field names, geometry type, CRS and bounded sample semantics; no EA survey result is attributed to this council source Direct metadata and attribute inspection
- **Access and reading depth:** HTTP 200 JSON; Full schema/CRS and bounded attribute samples; no raster or site mesh.
- **Limitations:** Not full inventory, accepted geometry, plantability or rights clearance
- **Use / priority / reader:** B03 source/schema/coordinate preflight — **Essential**; Alex; Arnav.
- **Rights:** Source-specific; see section 5

### [120] Sheffield SuDS Regions
- **Author/publisher; year/version:** Sheffield City Council; Live service inspection, 11 November 2026; records retain distinct acquisition dates.
- **Type / venue:** Primary ArcGIS REST metadata and query; Publisher service.
[120] https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/OpenData_FloodAndWaterManagement/MapServer/12 — Sheffield SuDS Regions — live service metadata and bounded query
- **Contribution / method:** Verifies this council layer’s actual field names, geometry type, CRS and bounded sample semantics; no EA survey result is attributed to this council source Direct metadata and attribute inspection
- **Access and reading depth:** HTTP 200 JSON; Full schema/CRS and bounded attribute samples; no raster or site mesh.
- **Limitations:** Not full inventory, accepted geometry, plantability or rights clearance
- **Use / priority / reader:** B03 source/schema/coordinate preflight — **Essential**; Alex; Arnav.
- **Rights:** Source-specific; see section 5

### [121] EA DTM index
- **Author/publisher; year/version:** Environment Agency; Live service inspection, 11 November 2026; records retain distinct acquisition dates.
- **Type / venue:** Primary ArcGIS REST metadata and query; Publisher service.
[121] https://services-eu1.arcgis.com/KB6uNVj5ZcJr7jUP/ArcGIS/rest/services/LIDAR_Composite_Catalogues/FeatureServer/2 — EA DTM index — live service metadata and bounded query
- **Contribution / method:** Verifies actual fields and CRS; EA point query identifies survey P_10706 at Weston locator Direct metadata and attribute inspection
- **Access and reading depth:** HTTP 200 JSON; Full schema/CRS and bounded attribute samples; no raster or site mesh.
- **Limitations:** Not full inventory, accepted geometry, plantability or rights clearance
- **Use / priority / reader:** B03 source/schema/coordinate preflight — **Essential**; Alex; Arnav.
- **Rights:** Source-specific; see section 5

### [122] EA DSM first-return index
- **Author/publisher; year/version:** Environment Agency; Live service inspection, 11 November 2026; records retain distinct acquisition dates.
- **Type / venue:** Primary ArcGIS REST metadata and query; Publisher service.
[122] https://services-eu1.arcgis.com/KB6uNVj5ZcJr7jUP/ArcGIS/rest/services/LIDAR_Composite_Catalogues/FeatureServer/0 — EA DSM first-return index — live service metadata and bounded query
- **Contribution / method:** Verifies actual fields and CRS; EA point query identifies survey P_10706 at Weston locator Direct metadata and attribute inspection
- **Access and reading depth:** HTTP 200 JSON; Full schema/CRS and bounded attribute samples; no raster or site mesh.
- **Limitations:** Not full inventory, accepted geometry, plantability or rights clearance
- **Use / priority / reader:** B03 source/schema/coordinate preflight — **Essential**; Alex; Arnav.
- **Rights:** Source-specific; see section 5

### [123] EA DSM last-return index
- **Author/publisher; year/version:** Environment Agency; Live service inspection, 11 November 2026; records retain distinct acquisition dates.
- **Type / venue:** Primary ArcGIS REST metadata and query; Publisher service.
[123] https://services-eu1.arcgis.com/KB6uNVj5ZcJr7jUP/ArcGIS/rest/services/LIDAR_Composite_Catalogues/FeatureServer/1 — EA DSM last-return index — live service metadata and bounded query
- **Contribution / method:** Verifies actual fields and CRS; EA point query identifies survey P_10706 at Weston locator Direct metadata and attribute inspection
- **Access and reading depth:** HTTP 200 JSON; Full schema/CRS and bounded attribute samples; no raster or site mesh.
- **Limitations:** Not full inventory, accepted geometry, plantability or rights clearance
- **Use / priority / reader:** B03 source/schema/coordinate preflight — **Essential**; Alex; Arnav.
- **Rights:** Source-specific; see section 5

### [124] Allometric relationships for urban trees in Great Britain
- **Author/publisher; year/version:** Madalena Vaz Monteiro; Kieron J. Doick; Phillip Handley; 1 September 2016; Urban Forestry & Urban Greening 19, 223–236.
- **Type / venue:** Peer-reviewed empirical paper; inspected institutional summary; Urban Forestry & Urban Greening / Forest Research.
[124] https://www.forestresearch.gov.uk/publications/allometric-relationships-for-urban-trees-in-great-britain — Allometric relationships for urban trees in Great Britain
- **DOI:** 10.1016/j.ufug.2016.07.009
- **Contribution / method:** Direct GB evidence that dimension relationships vary with species and urban location More than 2,000 trees; seven species; eight urban areas
- **Access and reading depth:** Institutional summary fetched; publisher full-text request returned 403; Summary and publisher preview only; full-paper coefficients and diagnostics not inspected.
- **Limitations:** Summary-level evidence here; dimensional allometry is not an age-growth model
- **Use / priority / reader:** Require provenance and applicability limits for crown profiles — **High**; Arnav.
- **Rights:** Forest Research webpage states OGL except otherwise indicated; article reuse licence not verified

### [125] Tree Species Selection for Green Infrastructure: A Guide for Specifiers
- **Author/publisher; year/version:** Andrew D. Hirons; Henrik Sjöman; Trees and Design Action Group; Original guide 2018; live page links tdag_speciesguidev1.4.25.pdf and supplementary database 1.2 named 2019.
- **Type / venue:** UK practice guide and companion dataset; Trees and Design Action Group.
[125] https://www.tdag.org.uk/tree-species-selection-for-green-infrastructure.html — Tree Species Selection for Green Infrastructure: A Guide for Specifiers
- **Contribution / method:** Relevant UK species-selection structure and an explicit dataset reuse restriction Research-supported guide combining species characteristics and environmental tolerances
- **Access and reading depth:** Publisher page and linked licence fetched; 45 MB guide rejected as too large; Publisher description and licence only; guide profiles and workbook not inspected.
- **Limitations:** No individual profile or parameter adopted; live revision date unresolved
- **Use / priority / reader:** Candidate reference for a reviewed species registry — **High**; Alex and Arnav.
- **Rights:** Supplementary dataset: CC BY-NC 4.0 per publisher link; guide licence not established

### [126] Urban Tree Manual: The Right Tree in the Right Place for a Resilient Future
- **Author/publisher; year/version:** Defra; Forestry Commission England; contributing organisations; Forest Research publication record: 1 October 2018.
- **Type / venue:** Primary UK government practice manual; Defra / Forestry Commission / Forest Research.
[126] https://cdn.forestresearch.gov.uk/2022/02/7111_fc_urban_tree_manual_v15.pdf — Urban Tree Manual: The Right Tree in the Right Place for a Resilient Future
- **Contribution / method:** Connects planting choices to soil, infrastructure, stock procurement and aftercare Expert guidance with references and case studies
- **Access and reading depth:** Full 33-page PDF fetched; Location, soil, selection, procurement, establishment and biodiversity sections inspected.
- **Limitations:** Not a numerical rooting-volume model or proof of site permission; referenced British Standards not inspected
- **Use / priority / reader:** Survey requirements, profile evidence and maintenance fields — **Essential**; Alex; Arnav for constraints.
- **Rights:** Publisher site states OGL v3.0 except where otherwise stated; third-party material requires separate attention

### [127] Spatial and temporal dynamics of the leaf area index (LAI) of selected tree species in urban environments
- **Author/publisher; year/version:** Astrid Moser-Reischl; Eleonora Franceschi; Mohammad A. Rahman; Julia Rodrigues-Leite; Hans Pretzsch; Stephan Pauleit; Thomas Rötzer; Available online 28 March 2025; volume 107, May 2025, article 128795.
- **Type / venue:** Peer-reviewed empirical paper; Urban Forestry & Urban Greening.
[127] https://doi.org/10.1016/j.ufug.2025.128795 — Spatial and temporal dynamics of the leaf area index (LAI) of selected tree species in urban environments
- **DOI:** 10.1016/j.ufug.2025.128795
- **Contribution / method:** Size and seasonal variation in urban-tree LAI; limitations of indirect measurements German urban-tree observations, hemispherical photography and statistical analysis
- **Access and reading depth:** research worker reports inspecting the author-deposited full text (sampling/photography/seasonal methods); parent independently verified title, authors and May 2025 publication through Crossref, but direct publisher/author-copy re-fetch was blocked. No species coefficient or quantitative result is adopted here.
- **Limitations:** German observations and method-specific bias; not a calibrated Sheffield transmission library
- **Use / priority / reader:** Separate leaf area, woody obstruction, phenology and effective transmission — **High**; Arnav.
- **Rights:** CC BY 4.0 stated in the full paper

### [128] Urban Tree Mortality: A Literature Review
- **Author/publisher; year/version:** Deborah R. Hilbert; Lara A. Roman; Andrew K. Koeser; Jess Vogt; Natalie S. van Doorn; September 2019; 45(5), 167–200.
- **Type / venue:** Peer-reviewed literature review; Arboriculture & Urban Forestry.
[128] https://www.fs.usda.gov/nrs/pubs/jrnl/2019/nrs_2019_hilbert_001.pdf — Urban Tree Mortality: A Literature Review
- **DOI:** 10.48044/jauf.2019.015
- **Contribution / method:** Shows why survival assumptions depend on cohort, site, stewardship and removal Review of 56 studies with different inventory and cohort designs
- **Access and reading depth:** Full 34-page PDF fetched; subsequent page requests intermittently failed; Introduction, life-stage and human/biophysical framework inspected; indexed conclusions checked.
- **Limitations:** Heterogeneous studies; pooled rates cannot be treated as Sheffield probabilities
- **Use / priority / reader:** Scenario losses now; locally evidenced survival and replacement cohorts later — **High**; Arnav and Alex.
- **Rights:** © 2019 International Society of Arboriculture; no open reuse licence verified

### [129] The importance of city trees for reducing net rainfall: comparing measurements and simulations
- **Author/publisher; year/version:** Vincent Smets; Charlotte Wirion; Willy Bauwens; Martin Hermy; Ben Somers; Boud Verbeiren; 23 September 2019; 23, 3865–3884.
- **Type / venue:** Peer-reviewed field and model-comparison paper; Hydrology and Earth System Sciences.
[129] https://hess.copernicus.org/articles/23/3865/2019 — The importance of city trees for reducing net rainfall: comparing measurements and simulations
- **DOI:** 10.5194/hess-23-3865-2019
- **Contribution / method:** Strong individual urban-tree evidence separating canopy interception from wider hydrology Two-year observations of two Belgian trees; comparison with Gash, Rutter and adapted WetSpa
- **Access and reading depth:** Full HTML paper fetched; Interception definitions, Gash/Rutter comparison, experiment and transfer limitations inspected.
- **Limitations:** Two solitary, exposed trees; model results cannot simply transfer to other settings
- **Use / priority / reader:** Future interception pilot and water-balance validation — **Essential for hydrology**; Arnav.
- **Rights:** Copernicus open-access article; linked model implementation licences not audited

### [130] HydroPlus Technical Manual
- **Author/publisher; year/version:** Robert Coville; Jay Heppler; i-Tree development collaborators; Updated 2 February 2023.
- **Type / venue:** Primary software technical manual; i-Tree Research Suite.
[130] https://www.itreetools.org/documents/871/HydroPlus_TechnicalManual_hXHL6TW.pdf — HydroPlus Technical Manual
- **Contribution / method:** Concrete vegetation-hydrology implementation pathway and input burden StatisticalHydro plus related models; configuration files, weather, terrain, land cover and optional calibration
- **Access and reading depth:** Full 61-page PDF fetched; Model selection, required files, parameter tables, testing and international support inspected.
- **Limitations:** US-oriented data assumptions; documentation does not establish UK calibration or project compatibility
- **Use / priority / reader:** Future isolated hydrology feasibility pilot — **High for future work**; Arnav; Ben for integration assessment.
- **Implementation:** https://www.itreetools.org/tools/hydro
- **Rights:** Manual explicitly requires an i-Tree EULA; complete redistribution and embedding rights not verified

### [131] Storm Water Management Model User’s Manual Version 5.2
- **Author/publisher; year/version:** Lewis A. Rossman; Michelle A. Simon; Revised February 2022; EPA/600/R-22/030.
- **Type / venue:** Primary software manual; US Environmental Protection Agency.
[131] https://www.epa.gov/system/files/documents/2022-04/swmm-users-manual-version-5.2.pdf — Storm Water Management Model User’s Manual Version 5.2
- **Contribution / method:** Established runoff/routing framework and explicit continuity/stability checks Rainfall-runoff simulation, infiltration, storage and hydraulic routing
- **Access and reading depth:** Full 424-page PDF fetched; Conceptual model, subcatchments, depression storage, LID layers and numerical diagnostics selectively inspected.
- **Limitations:** No species-specific crown process established by this manual; site parameters and validation still required
- **Use / priority / reader:** Engineered tree-pit and drainage research — **High for future work**; Arnav.
- **Implementation:** https://www.epa.gov/water-research/storm-water-management-model-swmm
- **Rights:** EPA describes software as open source and freely available; exact dated package legal text not inspected

### [132] National standards for sustainable drainage systems
- **Author/publisher; year/version:** Department for Environment, Food & Rural Affairs; Published 19 June 2025; page updated 30 July 2025.
- **Type / venue:** Primary national guidance; GOV.UK.
[132] https://www.gov.uk/government/publications/national-standards-for-sustainable-drainage-systems/national-standards-for-sustainable-drainage-systems-suds — National standards for sustainable drainage systems
- **Contribution / method:** England-specific decision and evidence requirements for drainage Non-statutory design, maintenance and operation standards
- **Access and reading depth:** Full HTML guidance fetched; Scope, runoff hierarchy, everyday/extreme rainfall, harvesting and maintenance requirements inspected.
- **Limitations:** Not a tree-interception coefficient source; retrofit application has stated qualifications
- **Use / priority / reader:** Frame future hydrology around an actual drainage decision — **High**; Alex and Arnav.
- **Rights:** OGL v3.0 except where otherwise stated

### [133] EnergyPlus 24.2 Engineering Reference: Shading Module
- **Author/publisher; year/version:** US Department of Energy / EnergyPlus development team; documentation mirrored by Big Ladder Software; Version 24.2; mirror page undated; pre-cutoff existence corroborated by dated LBNL 17 March 2025 release note and DOE listing.
- **Type / venue:** Version-specific primary technical documentation, mirrored; EnergyPlus documentation.
[133] https://bigladdersoftware.com/epx/docs/24-2/engineering-reference/shading-module.html — EnergyPlus 24.2 Engineering Reference: Shading Module
- **Contribution / method:** Shows a possible bridge from geometric shading into building simulation Surface geometry, shadow calculations and solar heat-gain accounting
- **Access and reading depth:** Full chapter fetched; Sunlit fractions, overlapping transmission, dynamic shading and solar-distribution sections inspected.
- **Limitations:** Mirror is mutable; no installed engine, package licence, platform compatibility or project coupling verified
- **Use / priority / reader:** Future building-energy pilot — **High for future work**; Arnav and Ben.
- **Rights:** Software package licence not verified in the inspected version; documentation mirror copyright is separate

### [134] Developing a Data-driven school building stock energy and indoor environmental quality modelling method
- **Author/publisher; year/version:** Y. Schwartz; D. Godoy-Shimizu; I. Korolija; J. Dong; S.M. Hong; A. Mavrogianni; D. Mumovic; Available online 1 July 2021; Energy and Buildings 249, 111249.
- **Type / venue:** Peer-reviewed modelling and validation paper; Energy and Buildings.
[134] https://discovery.ucl.ac.uk/id/eprint/10130905 — Developing a Data-driven school building stock energy and indoor environmental quality modelling method
- **DOI:** 10.1016/j.enbuild.2021.111249
- **Contribution / method:** Actual England school-archetype methodology and validation example 168 archetypes representing 9,551 primary schools; EnergyPlus 8.9; comparison with DEC data
- **Access and reading depth:** Full 16-page published PDF fetched; Archetype construction, EnergyPlus workflow, measured comparison and sample limitations inspected.
- **Limitations:** Stock averages, sample biases and assumed constructions; no tree-intervention validation
- **Use / priority / reader:** Future school-energy model design — **High**; Arnav.
- **Rights:** Paper CC BY 4.0; model-file and underlying-data reuse not verified

### [135] The impact of urban trees on overheating and energy in London dwellings
- **Author/publisher; year/version:** Tianxing Zhang; Jonathon Taylor; Oscar Brousse; Charles H. Simpson; Yaonan Zhu; Clare Heaviside; Indexed metadata: written 17 July 2026; posted 12 August 2026; revised 23 September 2026.
- **Type / venue:** Preprint; abstract-only evidence in this review; SSRN.
[135] https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7270661 — The impact of urban trees on overheating and energy in London dwellings
- **Contribution / method:** UK-specific lead on the overheating/heating trade-off Abstract describes EnergyPlus, London dwelling types, adjusted weather and seasonal shading
- **Access and reading depth:** Primary indexed abstract and metadata accessible; direct record/PDF retrieval unsuccessful; Indexed abstract only; full methods, assumptions and numerical results not audited.
- **Limitations:** Preprint and inaccessible full text; reported effect sizes not transferred
- **Use / priority / reader:** Follow-up reading for a future building module — **Medium pending full text**; Arnav.
- **Rights:** Unknown

### [136] Understanding i-Tree: 2021 Summary of Programs and Methods
- **Author/publisher; year/version:** David J. Nowak; December 2021; General Technical Report NRS-200-2021.
- **Type / venue:** Primary model-methods report; USDA Forest Service, Northern Research Station.
[136] https://research.fs.usda.gov/download/treesearch/63636.pdf — Understanding i-Tree: 2021 Summary of Programs and Methods
- **DOI:** 10.2737/NRS-GTR-200-2021
- **Contribution / method:** Explicit model definitions for stock, annual sequestration and decomposition Inventory-based biomass and ecosystem-service models
- **Access and reading depth:** Full 107-page PDF fetched; Carbon methods and limitations, hydrology inputs and program descriptions selectively inspected.
- **Limitations:** Model conventions and transferred equations; not site observations or a licence to assume local coefficients
- **Use / priority / reader:** Carbon model contract and comparison reference — **Essential for future carbon work**; Arnav.
- **Implementation:** https://www.itreetools.org/support/resources-overview/i-tree-manuals-workbooks
- **Rights:** US government report; i-Tree software has separate EULA terms

### [137] A life cycle carbon dioxide inventory of the Million Trees Los Angeles program
- **Author/publisher; year/version:** E. Gregory McPherson; Alissa Kendall; Published online 2 July 2014; 19, 1653–1665.
- **Type / venue:** Peer-reviewed lifecycle study; The International Journal of Life Cycle Assessment.
[137] https://research.fs.usda.gov/download/treesearch/46311.pdf — A life cycle carbon dioxide inventory of the Million Trees Los Angeles program
- **DOI:** 10.1007/s11367-014-0772-8
- **Contribution / method:** Demonstrates why tree carbon requires production, maintenance, mortality and disposal accounting Surveys, interviews, field data and 40-year simulation
- **Access and reading depth:** Full 13-page paper fetched; System boundary, population/growth assumptions, activity inventory and energy dependencies inspected.
- **Limitations:** Los Angeles climate and operations; supplementary inventory not fully inspected; not UK coefficients
- **Use / priority / reader:** Future lifecycle boundary checklist — **High**; Arnav and Alex.
- **Rights:** Publisher copyright; public USDA copy does not establish an open software/data licence

### [138] Impacts of Vegetation on Urban Air Pollution
- **Author/publisher; year/version:** Air Quality Expert Group; Alastair Lewis; Sarah Julia Moller; David Carslaw; 2018 report; institutional publication record dated 27 July 2018.
- **Type / venue:** Primary commissioned UK evidence assessment; Defra / Air Quality Expert Group.
[138] https://pure.york.ac.uk/portal/en/publications/report-impacts-of-vegetation-on-urban-air-pollution — Impacts of Vegetation on Urban Air Pollution
- **Contribution / method:** UK-specific distinction between pollutant capture, ventilation and concentrations Assessment of observational, wind-tunnel and modelling evidence
- **Access and reading depth:** Official UK-AIR PDF timed out; published full report fetched from White Rose; Policy implications, dispersion, street canyons, deposition and modelling limitations inspected.
- **Limitations:** 2018 evidence base; individual scheme effects still require local assessment
- **Use / priority / reader:** Prevent removal-only objectives and unsupported air-quality claims — **Essential**; Arnav; Ben for claim validation.
- **Rights:** Crown copyright 2018; third-party cover image and repository reuse caveats apply

### [139] The Statutory Biodiversity Metric: User Guide
- **Author/publisher; year/version:** Department for Environment, Food & Rural Affairs; First published February 2024; November 2026 revision; publication/version-history pages updated 10 November 2026.
- **Type / venue:** Primary official metric manual; Defra.
[139] https://www.gov.uk/government/publications/statutory-biodiversity-metric-tools-and-guides — The Statutory Biodiversity Metric: User Guide
- **Contribution / method:** Separates statutory tree accounting from physical crown geometry and growth Habitat accounting with quality and risk adjustments
- **Access and reading depth:** Full 89-page PDF and version history fetched; calculation workbooks not inspected; Rules, tree helper, baseline/new-tree classification and condition guidance inspected.
- **Limitations:** Not a direct biodiversity census or connectivity prediction; tool and competent assessment required
- **Use / priority / reader:** Separate future ecological accounting from shade profiles — **High**; Alex and Arnav.
- **Implementation:** https://www.gov.uk/government/publications/statutory-biodiversity-metric-tools-and-guides
- **Rights:** OGL v3.0 stated in PDF

### [140] Nature Networks Evidence Handbook
- **Author/publisher; year/version:** Natural England; 6 March 2020; NERR081, edition 1.
- **Type / venue:** Official evidence handbook; inspected executive summary; Natural England.
[140] https://publications.naturalengland.org.uk/publication/6105140258144256 — Nature Networks Evidence Handbook
- **Contribution / method:** Network planning includes habitat quality, size, landscape permeability and people Ecological evidence synthesis and planning guidance
- **Access and reading depth:** Publisher summary fetched; 175-page PDF initially parsed, but substantive follow-up requests failed through signed redirects; Publisher executive summary only; not treated as a full-text review.
- **Limitations:** Detailed tools and thresholds not audited; practitioner-summary PDF also inaccessible
- **Use / priority / reader:** Frame future connectivity questions before selecting a graph model — **Medium**; Alex.
- **Rights:** Unknown for the specific downloaded artifact

### [141] The Green Book: UK government guidance on appraisal
- **Author/publisher; year/version:** HM Treasury; Government Finance Function; 2026 edition; updated 28 October 2026.
- **Type / venue:** Primary appraisal guidance; HM Treasury.
[141] https://www.gov.uk/government/publications/the-green-book--2/the-green-book-2026 — The Green Book: UK government guidance on appraisal
- **Contribution / method:** Cutoff-valid discounting and appraisal framework Incremental social appraisal, present values and distributional analysis
- **Access and reading depth:** Full HTML and 86-page PDF fetched; Discounting, distribution, costs, uncertainty and environmental valuation selectively inspected; rate checked in both formats.
- **Limitations:** No tree prices or validated benefit quantities supplied
- **Use / priority / reader:** Versioned future appraisal policy — **Essential for economics**; Alex and Arnav.
- **Rights:** OGL except where otherwise stated

### [142] Enabling a Natural Capital Approach guidance
- **Author/publisher; year/version:** Department for Environment, Food & Rural Affairs; Originally 22 January 2020; inspected revision updated 15 October 2026.
- **Type / venue:** Primary natural-capital appraisal guidance; Defra.
[142] https://www.gov.uk/government/publications/enabling-a-natural-capital-approach-enca-guidance/enabling-a-natural-capital-approach-guidance — Enabling a Natural Capital Approach guidance
- **Contribution / method:** Connects physical changes to welfare valuation without requiring every effect to be monetised Impact pathways, proportionate appraisal and valuation assurance
- **Access and reading depth:** Full accessible HTML guidance fetched; Value transfer, timing, uncertainty, biodiversity and double-counting sections inspected.
- **Limitations:** Contains discounting language predating the later October Green Book update; databook values not audited
- **Use / priority / reader:** Future valuation design and double-counting register — **Essential**; Alex and Arnav.
- **Rights:** OGL v3.0 except where otherwise stated

### [143] 101496 — Tree Management Framework
- **Author/publisher; year/version:** Sheffield City Council; Contract notice dispatched 22 July 2025; response deadline 18 August 2025.
- **Type / venue:** Primary buyer procurement notice; YORtender / Mercell CTM.
[143] https://uk.eu-supply.com/ctm/Supplier/PublicPurchase/96153/0/0?b=YORTENDER&returnUrl=ctm/Supplier/publictenders — 101496 — Tree Management Framework
- **Contribution / method:** Actual Sheffield tree-management procurement workflow Framework procurement for maintenance, cutting and clearing services
- **Access and reading depth:** Public buyer page fetched; later Find a Tender award notice returned 403; Full short public notice inspected; tender specifications and price schedules not accessed.
- **Limitations:** No proof of demand for planning software, planting prices or awarded expenditure
- **Use / priority / reader:** Identify operational users and procurement handoffs — **High**; Alex.
- **Rights:** Specific portal reuse terms not verified

### [144] University renews commitment to Sheffield’s campus trees
- **Author/publisher; year/version:** The University of Sheffield; 1 June 2026.
- **Type / venue:** Primary institutional strategy announcement; University of Sheffield Sustainability.
[144] https://sheffield.ac.uk/sustainability/news/university-renews-commitment-sheffields-campus-trees — University renews commitment to Sheffield’s campus trees
- **Contribution / method:** Local estate workflow linking retention, inspections, diversity and canopy planning Institutional policy statement referring to an estate tree assessment
- **Access and reading depth:** Full announcement fetched; linked Drive strategy text inaccessible; Entire short announcement inspected; underlying strategy not read.
- **Limitations:** Reported inventory was not independently checked; no customer interview or software procurement commitment
- **Use / priority / reader:** Ground an estate-manager design hypothesis — **High**; Alex.
- **Rights:** University copyright; reuse rights not established

### [145] Residential Archetypes Dataset Methodology
- **Author/publisher; year/version:** Kamma Climate; commissioned by the Climate Change Committee; CCC publication page dated 21 May 2025.
- **Type / venue:** Commissioned methodology and dataset description; Climate Change Committee.
[145] https://www.theccc.org.uk/publication/residential-archetypes-dataset-methodology-kamma-climate — Residential Archetypes Dataset Methodology
- **Contribution / method:** Concrete UK housing-stock archetype resource EPC data, housing surveys, imputation, clustering and recalibration
- **Access and reading depth:** Full 41-page methodology and publisher page fetched; dataset file not inspected; Normalisation, archetype construction, source restrictions and energy calculations inspected.
- **Limitations:** Includes modelled attributes and restricted underlying survey sources; not window-resolved EnergyPlus geometry
- **Use / priority / reader:** Future stock-level scenario selection — **Medium**; Arnav and Alex.
- **Rights:** Dataset redistribution and commercial reuse terms not established in this review

### [146] Hove Beach Park Tree Watering
- **Author/publisher; year/version:** Brighton and Hove City Council; Inspected public procurement mirror first published 11 June 2026; reference BHCC-016035.
- **Type / venue:** Public authority procurement record; Sell2Wales / GwerthwchiGymru.
[146] https://www.gwerthwchigymru.llyw.cymru/search/show/search_view.aspx?ID=JUN625841&catID= — Hove Beach Park Tree Watering
- **Contribution / method:** Evidence that establishment watering is separately procured Below-threshold contract record; OCID ocds-h6vhtk-06b162
- **Access and reading depth:** Primary public procurement mirror fetched; Scope, buyer, supplier and estimated contract dates inspected.
- **Limitations:** Inspected record lacks a usable value, tree count and watering specification; aggregator prices not adopted
- **Use / priority / reader:** Include aftercare ownership and cost inputs — **Medium**; Alex.
- **Rights:** Specific mirror reuse terms not verified

### [147] i-Tree Eco v6.0 User’s Manual
- **Author/publisher; year/version:** i-Tree development team; 22 September 2021, v6.0.
- **Type / venue:** Primary software user manual; i-Tree.
[147] https://www.itreetools.org/documents/275/EcoV6_UsersManual.2021.09.22.pdf — i-Tree Eco v6.0 User’s Manual
- **Contribution / method:** Establishes the documented remote-processing workflow and absence of default annual costs Inventory submission, server modelling and report retrieval
- **Access and reading depth:** Full 103-page PDF fetched; Server processing, result retrieval, annual costs, local benefit prices and EULA references inspected.
- **Limitations:** Historical manual does not establish every current capability; complete EULA retrieval unsuccessful
- **Use / priority / reader:** Comparator or future external assessment, not assumed offline integration — **High**; Ben and Alex.
- **Implementation:** https://www.itreetools.org/support/resources-overview/i-tree-manuals-workbooks
- **Rights:** Separate EULA required; full embedding, modification and redistribution rights unresolved

### [148] HERE Raster Tile API: DEM style
- **Author/publisher; year/version:** HERE; Undated/versioned documentation snapshot, 11 November 2026.
- **Type / venue:** Official documentation; HERE.
[148] https://docs.here.com/map-rendering/docs/styles-raster-tile-api — HERE Raster Tile API: DEM style
- **Contribution / method:** DEM RGB encoding, orthometric-height semantics and neighbour edges. API docs, no credentialed tile request.
- **Access and reading depth:** API docs, no credentialed tile request.; API docs, no credentialed tile request..
- **Limitations:** No Sheffield resolution/accuracy or rights test.
- **Use / priority / reader:** Possible terrain route; not immediate preference — **Useful**; Alex.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [149] HERE Raster Tile API copyright requirements
- **Author/publisher; year/version:** HERE; Undated/versioned documentation snapshot, 11 November 2026.
- **Type / venue:** Official documentation; HERE.
[149] https://docs.here.com/map-rendering/docs/required-copyright-notice — HERE Raster Tile API copyright requirements
- **Contribution / method:** Attribution varies by style, area and provider. Copyright documentation.
- **Access and reading depth:** Copyright documentation.; Copyright documentation..
- **Limitations:** Not a blanket data export licence.
- **Use / priority / reader:** Rights gate — **Useful**; Alex; Ben.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [150] Blosm documentation
- **Author/publisher; year/version:** Blosm maintainers; Undated/versioned documentation snapshot, 11 November 2026.
- **Type / venue:** Official documentation; Blosm maintainers.
[150] https://github.com/vvoovv/blosm/wiki/Documentation — Blosm documentation
- **Contribution / method:** GPL addon; OSM/building/floor import and ~30 m terrain. Actual wiki with terms warnings.
- **Access and reading depth:** Actual wiki with terms warnings.; Actual wiki with terms warnings..
- **Limitations:** Underlying data rights remain separate; no installation.
- **Use / priority / reader:** Optional scene assembly — **Useful**; Alex.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [151] GIS Copilot: Towards an Autonomous GIS Agent for Spatial Analysis
- **Author/publisher; year/version:** Temitope Akinboyewa; Zhenlong Li; Huan Ning; M. Naser Lessani; 2024 preprint; checked record version history.
- **Type / venue:** Research record; Temitope Akinboyewa; Zhenlong Li; Huan Ning; M. Naser Lessani.
[151] https://arxiv.org/abs/2411.03205 — GIS Copilot: Towards an Autonomous GIS Agent for Spatial Analysis
- **Contribution / method:** GIS agent integrating LLMs with QGIS, differentiated task complexity. Primary abstract/metadata.
- **Access and reading depth:** Primary abstract/metadata.; Primary abstract/metadata..
- **Limitations:** Full HTML unavailable here; no source runtime reproduction.
- **Use / priority / reader:** Agent architecture and task evaluation precedent — **Essential**; Ben.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [152] NIST AI Risk Management Framework
- **Author/publisher; year/version:** NIST; Undated/versioned documentation snapshot, 11 November 2026.
- **Type / venue:** Official documentation; NIST.
[152] https://www.nist.gov/itl/ai-risk-management-framework — NIST AI Risk Management Framework
- **Contribution / method:** AI risk-management framing. Official framework landing documentation.
- **Access and reading depth:** Official framework landing documentation.; Official framework landing documentation..
- **Limitations:** Not a turnkey security guarantee.
- **Use / priority / reader:** Risk ownership and documentation — **Essential**; Ben.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [153] OWASP LLM01 Prompt Injection
- **Author/publisher; year/version:** OWASP GenAI Security Project; LLM01:2025.
- **Type / venue:** Official documentation; OWASP GenAI Security Project.
[153] https://genai.owasp.org/llmrisk/llm01-prompt-injection — OWASP LLM01 Prompt Injection
- **Contribution / method:** Prompt-injection threat definition and mitigation framing. LLM01:2025 official guidance.
- **Access and reading depth:** LLM01:2025 official guidance.; LLM01:2025 official guidance..
- **Limitations:** Checklist does not prove robust runtime.
- **Use / priority / reader:** Untrusted metadata/least privilege tests — **Essential**; Ben.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [154] Berkeley Function Calling Leaderboard
- **Author/publisher; year/version:** Berkeley/Gorilla project; Undated/versioned documentation snapshot, 11 November 2026.
- **Type / venue:** Official documentation; Berkeley/Gorilla project.
[154] https://gorilla.cs.berkeley.edu/leaderboard.html — Berkeley Function Calling Leaderboard
- **Contribution / method:** Function-calling evaluation landscape. Official leaderboard/method links, current snapshot.
- **Access and reading depth:** Official leaderboard/method links, current snapshot.; Official leaderboard/method links, current snapshot..
- **Limitations:** No leaderboard scores adopted; not a spatial decision benchmark.
- **Use / priority / reader:** Schema/call-quality evaluation patterns — **Useful**; Ben.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [155] ENVI-met science overview
- **Author/publisher; year/version:** ENVI-met; Undated/versioned documentation snapshot, 11 November 2026.
- **Type / venue:** Official documentation; ENVI-met.
[155] https://envi-met.info/doku.php?id=root:start — ENVI-met science overview
- **Contribution / method:** Coupled surface/plant/air microclimate model scope. Official model wiki.
- **Access and reading depth:** Official model wiki.; Official model wiki..
- **Limitations:** No installation, commercial licence audit or case validation.
- **Use / priority / reader:** Reference alternative, not critical dependency — **Useful**; Arnav.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [156] Ladybug Tools
- **Author/publisher; year/version:** Ladybug Tools; Undated/versioned documentation snapshot, 11 November 2026.
- **Type / venue:** Official documentation; Ladybug Tools.
[156] https://www.ladybug.tools — Ladybug Tools
- **Contribution / method:** Environmental design/radiation tool ecosystem. Official project overview.
- **Access and reading depth:** Official project overview.; Official project overview..
- **Limitations:** Exact subpackage/version/licence requires adoption audit.
- **Use / priority / reader:** Existing tooling before reinventing solver — **Useful**; Arnav; Alex.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [157] NVIDIA PhysicsNeMo documentation
- **Author/publisher; year/version:** NVIDIA; Undated/versioned documentation snapshot, 11 November 2026.
- **Type / venue:** Official documentation; NVIDIA.
[157] https://docs.nvidia.com/physicsnemo/latest — NVIDIA PhysicsNeMo documentation
- **Contribution / method:** Physics-ML framework. Official documentation index.
- **Access and reading depth:** Official documentation index.; Official documentation index..
- **Limitations:** No trained surrogate or performance evidence in project.
- **Use / priority / reader:** Future reference-validated surrogate only — **Useful**; Arnav; Ben.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [158] TensorRT-LLM documentation
- **Author/publisher; year/version:** NVIDIA; Undated/versioned documentation snapshot, 11 November 2026.
- **Type / venue:** Official documentation; NVIDIA.
[158] https://nvidia.github.io/TensorRT-LLM — TensorRT-LLM documentation
- **Contribution / method:** Optimised inference framework. Official documentation.
- **Access and reading depth:** Official documentation.; Official documentation..
- **Limitations:** No project target-device support/benchmark established.
- **Use / priority / reader:** Later measured serving optimisation — **Useful**; Ben.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [159] RAPIDS installation guide
- **Author/publisher; year/version:** NVIDIA/RAPIDS maintainers; Undated/versioned documentation snapshot, 11 November 2026.
- **Type / venue:** Official documentation; NVIDIA/RAPIDS maintainers.
[159] https://docs.rapids.ai/install — RAPIDS installation guide
- **Contribution / method:** GPU data-science installation/platform matrix. Official installation documentation.
- **Access and reading depth:** Official installation documentation.; Official installation documentation..
- **Limitations:** No installed Arm geospatial workload established.
- **Use / priority / reader:** Optional only if actual bottleneck — **Useful**; Ben.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [160] NVIDIA Omniverse documentation
- **Author/publisher; year/version:** NVIDIA; Undated/versioned documentation snapshot, 11 November 2026.
- **Type / venue:** Official documentation; NVIDIA.
[160] https://docs.omniverse.nvidia.com — NVIDIA Omniverse documentation
- **Contribution / method:** 3D collaboration/simulation platform documentation. Official product documentation index.
- **Access and reading depth:** Official product documentation index.; Official product documentation index..
- **Limitations:** Not a validated twin or required viewer.
- **Use / priority / reader:** Later interoperability if justified — **Useful**; Alex; Ben.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [161] DGX Spark release notes
- **Author/publisher; year/version:** NVIDIA; October 2026 release; live cutoff table.
- **Type / venue:** Official documentation; NVIDIA.
[161] https://docs.nvidia.com/dgx/dgx-spark/release-notes.html — DGX Spark release notes
- **Contribution / method:** Exact published OS/driver/platform component baseline. Official release table.
- **Access and reading depth:** Official release table.; Official release table..
- **Limitations:** Actual event unit may differ; no update permission inferred.
- **Use / priority / reader:** Device/runtime comparison gate — **Essential**; Ben.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [162] Get Information about Schools downloads
- **Author/publisher; year/version:** Department for Education; Undated/versioned documentation snapshot, 11 November 2026.
- **Type / venue:** Official documentation; Department for Education.
[162] https://get-information-schools.service.gov.uk/Downloads — Get Information about Schools downloads
- **Contribution / method:** School-establishment download identity route. Official downloads page.
- **Access and reading depth:** Official downloads page.; Official downloads page..
- **Limitations:** Identity is not site boundary/ownership/plantability.
- **Use / priority / reader:** Correct school data starting point — **Useful**; Alex.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [163] GOV.UK API catalogue: Ordnance Survey Maps API
- **Author/publisher; year/version:** GOV.UK API Catalogue / Ordnance Survey; Undated/versioned documentation snapshot, 11 November 2026.
- **Type / venue:** Official documentation; GOV.UK API Catalogue / Ordnance Survey.
[163] https://www.api.gov.uk/os/os-maps-api — GOV.UK API catalogue: Ordnance Survey Maps API
- **Contribution / method:** OS Maps raster WMTS/ZXY discovery and licence link. Official catalogue metadata.
- **Access and reading depth:** Official catalogue metadata.; Official catalogue metadata..
- **Limitations:** Catalogue is not separate data or licence grant.
- **Use / priority / reader:** Context map integration candidate — **Useful**; Alex.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [164] OS Data Hub
- **Author/publisher; year/version:** Ordnance Survey; Undated/versioned documentation snapshot, 11 November 2026.
- **Type / venue:** Official documentation; Ordnance Survey.
[164] https://www.ordnancesurvey.co.uk/developers — OS Data Hub
- **Contribution / method:** Data Hub APIs/downloads and distinct plan categories. Official developer overview.
- **Access and reading depth:** Official developer overview.; Official developer overview..
- **Limitations:** No account/terms entitlement granted; separate named Data Science Hub not established.
- **Use / priority / reader:** Exact product/plan rights discovery — **Useful**; Alex.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [165] Copernicus DEM documentation
- **Author/publisher; year/version:** Copernicus Data Space Ecosystem; Undated/versioned documentation snapshot, 11 November 2026.
- **Type / venue:** Official documentation; Copernicus Data Space Ecosystem.
[165] https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM — Copernicus DEM documentation
- **Contribution / method:** DSM instances EEA-10/GLO-30/GLO-90; surface semantics. Official collection metadata.
- **Access and reading depth:** Official collection metadata.; Official collection metadata..
- **Limitations:** Coarse for detailed tree geometry; product licence/vertical reference still matters.
- **Use / priority / reader:** Regional context/fallback, not fine scene — **Useful**; Alex; Arnav.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [166] Open3D raycasting scene tutorial
- **Author/publisher; year/version:** Open3D contributors; Undated/versioned documentation snapshot, 11 November 2026.
- **Type / venue:** Official documentation; Open3D contributors.
[166] https://www.open3d.org/docs/release/tutorial/geometry/ray_casting.html — Open3D raycasting scene tutorial
- **Contribution / method:** Mesh raycasting tutorial/reference API. Official 0.19 documentation.
- **Access and reading depth:** Official 0.19 documentation.; Official 0.19 documentation..
- **Limitations:** No project install or equality test.
- **Use / priority / reader:** CPU/mesh reference option — **Useful**; Arnav.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [167] GDAL documentation
- **Author/publisher; year/version:** GDAL/OSGeo contributors; Undated/versioned documentation snapshot, 11 November 2026.
- **Type / venue:** Official documentation; GDAL/OSGeo contributors.
[167] https://gdal.org/en/stable — GDAL documentation
- **Contribution / method:** Raster/vector transforms and drivers. Official documentation.
- **Access and reading depth:** Official documentation.; Official documentation..
- **Limitations:** Binary/environment compatibility still requires smoke.
- **Use / priority / reader:** Core ingestion leverage — **Useful**; Alex; Arnav.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [168] OGC 3D Tiles specification
- **Author/publisher; year/version:** Open Geospatial Consortium; Undated/versioned documentation snapshot, 11 November 2026.
- **Type / venue:** Official documentation; Open Geospatial Consortium.
[168] https://www.ogc.org/standard/3dtiles — OGC 3D Tiles specification
- **Contribution / method:** 3D Tiles hierarchical geospatial streaming standard. Official standard overview.
- **Access and reading depth:** Official standard overview.; Official standard overview..
- **Limitations:** Format is not an asset source or data licence.
- **Use / priority / reader:** Optional large-scene interchange — **Useful**; Alex.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [169] LLM-Find: An Autonomous GIS Agent Framework
- **Author/publisher; year/version:** Huan Ning; Zhenlong Li; Temitope Akinboyewa; M. Naser Lessani; 2024-07-13 v1.
- **Type / venue:** Research record; Huan Ning; Zhenlong Li; Temitope Akinboyewa; M. Naser Lessani.
[169] https://arxiv.org/abs/2407.21024v1 — LLM-Find: An Autonomous GIS Agent Framework
- **Contribution / method:** Agent-selected geospatial sources using source handbooks. Primary v1 abstract/metadata.
- **Access and reading depth:** Primary v1 abstract/metadata.; Primary v1 abstract/metadata..
- **Limitations:** Do not transfer claimed retrieval success to this project.
- **Use / priority / reader:** Data-source provenance/tool documentation pattern — **Useful**; Ben; Alex.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [170] A fast and elitist multiobjective genetic algorithm: NSGA-II
- **Author/publisher; year/version:** Kalyanmoy Deb; Amrit Pratap; S. Agarwal; T. Meyarivan; 2002; IEEE TEC 6(2), 182–197; DOI 10.1109/4235.996017.
- **Type / venue:** Research record; Kalyanmoy Deb; Amrit Pratap; S. Agarwal; T. Meyarivan.
[170] https://doi.org/10.1109/4235.996017 — A fast and elitist multiobjective genetic algorithm: NSGA-II
- **Contribution / method:** NSGA-II nondominated sorting baseline. Institutional bibliographic metadata; full paper not retrieved.
- **Access and reading depth:** Institutional bibliographic metadata; full paper not retrieved.; Institutional bibliographic metadata; full paper not retrieved..
- **Limitations:** No guarantee/implementation performance claimed.
- **Use / priority / reader:** Optional multiobjective research alternative — **Useful**; Arnav.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [171] Optimization of conditional value-at-risk
- **Author/publisher; year/version:** R. Tyrrell Rockafellar; Stanislav Uryasev; 2000; Journal of Risk 2(3), 21–41; DOI 10.21314/JOR.2000.038.
- **Type / venue:** Research record; R. Tyrrell Rockafellar; Stanislav Uryasev.
[171] https://doi.org/10.21314/jor.2000.038 — Optimization of conditional value-at-risk
- **Contribution / method:** CVaR loss-tail optimisation framing. Publisher abstract/metadata.
- **Access and reading depth:** Publisher abstract/metadata.; Publisher abstract/metadata..
- **Limitations:** Full-text method not inspected; probability/loss assumptions required.
- **Use / priority / reader:** Prevent misuse of risk terminology — **Useful**; Arnav.
- **Rights:** Exact package/data/content licence remains a separate adoption gate

### [172] Maps SDK — Microsoft Garage (experiment complete)
- **Author/publisher; year/version:** Microsoft Garage; Undated/versioned documentation snapshot, 11 November 2026.
- **Type / venue:** Official documentation; Microsoft Garage.
[172] https://www.microsoft.com/en-us/garage/profiles/maps-sdk — Maps SDK — Microsoft Garage (experiment complete)
- **Contribution / method:** Bing 3D world/terrain into Unity; experiment complete. Primary page recovered with extractor.
- **Access and reading depth:** Primary page recovered with extractor.; Primary page recovered with extractor..
- **Limitations:** Direct HTML blocked; no export rights/support proof.
- **Use / priority / reader:** Do not rely on unsupported extraction route — **Useful**; Alex.
- **Rights:** Exact package/data/content licence remains a separate adoption gate


## Final independent conclusions

1. **Strongest argument for continuing:** there is a real, visible decision with measurable geometry, constraints and counterfactuals; the team already has a coherent integration spine, and a local investigator can expose a consequential uncertainty rather than merely narrate a map. The useful core survives even if the agent is later reduced to an optional interface[20][64][71].
2. **Strongest argument against continuing:** substantial prior art and Infrared City's public agent workflow erase the broad novelty claim, while rights/geometry/runtime integration could consume the remaining effort without delivering a better decision than a fixed workflow. No customer, accepted site or measured agent advantage is yet established[15][20][71].
3. **Most consequential discovery beyond the original concept:** agent-driven microclimate scenario generation is already publicly implemented; differentiation should shift to **local, auditable, survey-aware decision quality**, not “AI + trees”. Source/schema age also directly changes the decision: the school-locality and historic-planting layers are not planting opportunities[15][116][119].
4. **Best technical architecture:** typed immutable site/scenario/result contracts; a CPU analytic numerical reference; lawful metric geometry; deterministic feasible search and independent validation; optional proven GPU batching; one precisely configured local model behind a narrow dispatcher; a UI that reveals stale/missing evidence. Keep modules separate and numerical truth outside the LLM[45][47][77].
5. **Strongest agentic feature:** an adaptive counterfactual/sensitivity investigator that identifies which permitted change or uncertain input could reverse a layout choice and proposes the next useful survey, citing real current results. Call it formal VOI only when the probability/observation/utility model exists[56][64].
6. **Five biggest risks:** (i) inaccurate or uncleared real-site geometry/plantability; (ii) unsupported environmental or optimisation claims; (iii) model/driver/parser failure and shared-memory contention; (iv) no measurable value over the same-tools fixed/manual workflow; (v) late integration and unconfirmed competition rules. Each has an explicit owner/gate above[1][47][99].
7. **Ten highest-value team actions:** agree user/target; confirm rules/deadline; accept contract/frame; audit primary/fallback scene; deliver baseline→one-tree→UI; prove tiny search/constraint cases; demonstrate one uncertainty reversal plus stable control; prove exact local model/tool path; run the frozen same-tools suite; freeze and rehearse the traceable live/failure demo. Keep ownership and receipts in B01–B12, not a parallel checklist.
8. **Final recommendation: MODIFY, then continue.** Keep the project and full modular ambition; modify its novelty claim, evidence contract and validation priorities. Do not pivot merely because competitors exist, and do not continue merely because time has already been spent. Pivot only if another concept has a demonstrably better user/data/evidence path while the essential Tree Planner gates fail.
