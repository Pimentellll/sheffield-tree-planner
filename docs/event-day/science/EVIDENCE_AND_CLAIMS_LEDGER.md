# Evidence and claims ledger

**Rule:** a statement in the video, form, README or Q&A must match an **approved** row (category VR, RI or SE with its condition met). Rows in HF may be said only as plans. Rows in UP must not be said; use the safer wording.
**No CANOPY measured or computed result appears in this ledger** (the only figures are published literature values or scenario inputs). Spark-dependent rows stay conditional until the [acceptance checklist](SCIENTIFIC_ACCEPTANCE.md) row they cite is `verified`. Fill the "Spark evidence" column with run IDs, not prose.

**Categories:** **VR** verified public research · **RI** verified repository implementation (code inspected on `main` 630ee65; development tests reported in PR #52 and not re-run here) · **SE** actual Spark evidence (pending) · **HF** hypothesis / future capability · **UP** unsupported / prohibited.
**Judging:** I = Impact · T = Technical Execution · F = Feasibility.

## Sheffield, impact and residents

| ID | Proposed claim | Judging | Category | Evidence source | Confidence | In video? | Needs Spark? | Safer wording | Limitation |
|---|---|---|---|---|---|---|---|---|---|
| I-01 | Sheffield manages street trees through a multi-partner strategy, the Street Tree Partnership Strategy (2021) | I | VR | [Research §1](IMPACT_AND_FEASIBILITY_RESEARCH.md#1-the-real-problem-in-sheffield) | High | Yes | No | — | Says nothing about CANOPY's use |
| I-02 | Where a tree goes changes how much *new* shade it adds, because buildings and existing trees already shade some ground | I/T | VR + RI | Wallenberg et al. 2022; NUMERICS §4.2 (B − V) | High | Yes | No | — | Geometric shade only |
| I-03 | Tree shade can lower radiant heat exposure (a Manchester study found shading reduced globe temperatures by up to 5–7 °C) | I | VR | Armson et al. 2012 | Medium–high | Only attributed to that study, never as a CANOPY result | No | "Field studies in the UK link tree shade to lower radiant heat exposure" | Not a CANOPY output; site- and weather-specific |
| I-04 | Sheffield City Council uses, endorses or partners with CANOPY | I | UP | None | — | **No** | — | "Designed around the kind of decision Sheffield's street-tree process involves" | No contact or endorsement exists |
| I-05 | CANOPY improves residents' health or comfort | I | UP | None | — | **No** | — | "Aims to make planting trade-offs easier to compare and explain" | No outcome study |
| I-06 | Planting decisions involve trade-offs between shade, budget, winter sun, space and utilities | I | VR + RI | TDAG; NJUG Vol 4; scenario constraints | High | Yes | No | — | Utilities are survey-required, not modelled |

## Shade, cooling and the numerical model

| ID | Proposed claim | Judging | Category | Evidence source | Confidence | In video? | Needs Spark? | Safer wording | Limitation |
|---|---|---|---|---|---|---|---|---|---|
| S-01 | CANOPY computes additional direct-sun shade in m²·h, accounting for buildings and existing trees | T | RI | physics README; NUMERICS §4 | High | Yes | For on-screen numbers: N-01, N-12 | — | Direct beam only; synthetic receivers |
| S-02 | Sun positions use pvlib's SPA algorithm for the declared latitude and time | T | RI | physics README (`pvlib-spa-geometric/0.15.2`) | High | Yes | No | — | ΔT fixed at 67 s; no weather |
| S-03 | "Measured shade" | T | UP | — | — | **No** | — | "Computed shade" | Nothing is measured |
| S-04 | The shade model is validated | T/F | UP | — | — | **No** | — | "Checked against analytic test cases during development; not field-validated" | No observations |
| S-05 | A summer value describes daily or seasonal shade | T | UP | Seed time bins | — | **No** | — | "A one-hour midday sample on 1 July" (if seed unchanged) | Single time bin per case |
| S-06 | Winter sunlight loss is checked against a declared hard limit | T | RI | `jobs/comparison.py` winter check | High | Yes | N-09 | — | Leaf-off transmission 0.7 is assumed |
| S-07 | Young and mature trees are evaluated separately | T | RI | Seed cases `establishment` (yr 1) and `summer` (yr 20) | High | Yes | N-08 | "Assumed young and mature crown sizes" | Not a growth forecast |
| S-08 | The demo is a real Sheffield site | I/F | UP | — | — | **No** | — | "Synthetic test geometry placed at Sheffield's latitude" | No surveyed geometry |
| S-09 | Planting cools Sheffield by X °C, cuts energy use, stores carbon, cleans air or reduces flooding | I | UP | — | — | **No** | — | "Shade is a first step; temperature or other benefits need further validated models" | [Research §2 table](IMPACT_AND_FEASIBILITY_RESEARCH.md#2-shade-is-not-cooling-what-the-evidence-supports) |
| S-10 | Weighted utility equals shaded area | T | UP | `results.py` validator | — | **No** | — | "Priority-weighted score, shown beside the unweighted shade" | Seed weight 2 doubles it |

## Cost and optimisation

| ID | Proposed claim | Judging | Category | Evidence source | Confidence | In video? | Needs Spark? | Safer wording | Limitation |
|---|---|---|---|---|---|---|---|---|---|
| O-01 | Finds the optimal layout | T | UP | Search docstring; PHYSICAL_RUNTIME | — | **No** | — | "Finds the best evaluated layout in a finite candidate catalogue, then checks every constraint independently" | No optimality proof; 3 candidates in demo |
| O-02 | Every selected layout respects budget, tree count, spacing and winter limits | T | RI + SE | `check()`; comparison validator | High (code) | Yes, for the shown run | N-06 | — | Survey items remain unknown |
| O-03 | Costs are real prices / saves the council money / has an ROI | I | UP | Seed `cost_scope` "Assumed upfront test cost" | — | **No** | — | "Uses an assumed upfront cost per tree (£100 in the demo scenario)" | No pricing data |
| O-04 | Budgets are handled exactly in pence | T | RI | Integer `budget_pence`, `cost_pence` | High | Optional | N-04 | — | Upfront basis only |
| O-05 | Scales to city-wide planning | F | HF | Mask-reuse design in NUMERICS | Low | Only as future work | — | "The method reuses shadow masks, which is how it would scale; not yet tested at city scale" | No scale benchmark |

## Hardware, local compute and Nemotron

| ID | Proposed claim | Judging | Category | Evidence source | Confidence | In video? | Needs Spark? | Safer wording | Limitation |
|---|---|---|---|---|---|---|---|---|---|
| H-01 | The agent runs a local Nemotron model on our DGX Spark | T | SE | X-01, X-02 | Pending | **After verification only** | Yes | Partial case: "Our agent is built for local models on DGX Spark; [state what was shown]" | Exact tag from `ollama ps` |
| H-02 | Shade/physics computation is GPU-accelerated on the Spark | T | UP | Evaluator `canopy-cpu-reference` | — | **No** | — | "Inference runs locally on the Spark; the numerical engine is a CPU reference implementation" | — |
| H-03 | No data leaves the device | T/F | HF → SE | Loopback-only client and dispatcher (code) | Medium | Only as "no hosted model API is used" | X-01 | "The model and the tools both run on loopback on the Spark; no hosted model API is called" | Network isolation not audited |
| H-04 | A query takes N seconds | T | SE | X-08 | Pending | Only measured values with n and conditions | Yes | — | n = 5; one scenario |
| H-05 | Uses NIM, TensorRT-LLM, NeMo, vLLM, Warp or cuOpt | T | UP unless shown | `ollama ps`; deployed release | — | **No** unless actually used | Yes | List only technologies in the deployed release | The vLLM profile in `deploy/spark/` is untested |
| M-01 | Nemotron chooses which planning tool to call | T | SE | Protocol A-01, C1–C3 | Pending | After verification | Yes | "In our five recorded tests the model chose …" | n = 5 |
| M-02 | Nemotron passed k of 5 required tests | T | SE | Protocol §7 summary | Pending | Exact k/5 with failures | Yes | — | No reliability estimate |
| M-03 | Nemotron is better than another model | T | UP | — | — | **No** | — | Omit unless a matched P1 comparison was run | — |
| M-04 | The model's reasoning guarantees correct numbers | T | UP | — | — | **No** | — | "Numbers come from deterministic tools; the host rejects evidence IDs it did not observe" | The model's own wording can still be wrong (D5) |

## Agent behaviour and safety

| ID | Proposed claim | Judging | Category | Evidence source | Confidence | In video? | Needs Spark? | Safer wording | Limitation |
|---|---|---|---|---|---|---|---|---|---|
| G-01 | Figures shown to the user are generated from stored backend results, not by the model | T | RI | `AgentLoop._conclusion` | High | Yes | A-05 for footage | — | Model narrative is kept separately as untrusted |
| G-02 | The agent cannot change the accepted budget, approve plans or grant permission | T/F | RI | `policy.py`; `search_layouts` takes no args; pinned scope | High | Yes | A-03 | "The agent can investigate but cannot accept a scenario; humans accept" | Only for exposed tools |
| G-03 | The agent asks for clarification and says "I don't know" when appropriate | T | SE | C4, C5 | Pending | Only if C4/C5 passed; show the transcript | Yes | Report actual grade (PASS-A/B) | One prompt each |
| G-04 | Multi-agent system / autonomous planner | T | UP | One loop | — | **No** | — | "A single tool-using agent with a bounded set of planning tools" | — |
| G-05 | The agent is better than a manual workflow | I/T | UP | B11 incomplete (#31) | — | **No** | — | Omit | — |
| G-06 | Late or stale results cannot overwrite newer ones | T | RI + SE | VALIDATION V05 tests; A-06 | High (code) | Yes, if A-06 has evidence | A-06 | — | — |
| G-07 | Every result traces to inputs, versions and hashes | T/F | RI | Result `provenance`, `input_fingerprint`, `source_ids` | High | Yes | N-12 | — | Hashes check integrity, not authenticity |

## Deployment and feasibility

| ID | Proposed claim | Judging | Category | Evidence source | Confidence | In video? | Needs Spark? | Safer wording | Limitation |
|---|---|---|---|---|---|---|---|---|---|
| D-01 | Ready for council deployment | F | UP | — | — | **No** | — | "A working prototype with a staged path to a real-street pilot" | [Research §5](IMPACT_AND_FEASIBILITY_RESEARCH.md#5-staged-adoption-pathway-feasibility) |
| D-02 | Could work beyond the hackathon via a real-street pilot | F | HF | Research §5 | Medium | Yes, as a plan | No | — | Needs data rights and partners |
| D-03 | Open-source public repository | F | SE | #59 | Pending | After the URL opens anonymously | Yes | — | Licence must be stated |
| D-04 | Runs on a single local machine | F | SE | X-01 | Pending | After verification | Yes | — | Memory/latency not yet measured |

## Wording quick reference (for Alex and the form)

| Avoid | Use |
|---|---|
| measured shade | computed shade |
| optimal / optimises the city | best evaluated layout under the accepted budget |
| validated | tested against analytic cases; not field-validated |
| cools Sheffield / reduces temperature | adds direct-sun shade; temperature effects need further models |
| real Sheffield site | synthetic geometry at Sheffield's latitude |
| AI decides where to plant | the agent investigates options; a person decides |
| GPU-accelerated simulation | local model inference on DGX Spark; CPU numerical engine |
| £20,000 (from 20000) | £200.00 (20000 pence) |
