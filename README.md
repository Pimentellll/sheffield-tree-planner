# CANOPY Sheffield · tree-planning workbench

An urban tree-planning project for NVIDIA Hack for Impact Sheffield, 13 November 2026.

The intended system combines deterministic shade analysis and constrained tree-placement search with a local planning agent that investigates alternatives and explains computed evidence. Sheffield is the first case study; existing trees, winter sunlight, costs and uncertainty remain explicit.

## Status

**Local 0.2.0 backend candidate; the integrated product is not yet accepted.** Ben approved isolated own-lane implementation under BUILD decision D18. Shared producer/consumer acceptance, teammate merges, real-site rights, scientific sign-off and Spark access remain separate gates.

This **separately authorised local M2 integration copy** also connects Alex's existing UI to actual synthetic computation. [Frontend instructions](frontend/README.md) run the built UI and API on one loopback origin and replay positive/zero/stale/source-failure/recovery/mobile checks. It is not a new push, a change to Alex's branch, or evidence that the shared product/contract is accepted. The private frontend's npm version is inherited component metadata; the Python project remains the canonical product/runtime version.

- The package now contains strict domain schemas, immutable SQLite persistence, a local API, bounded jobs/current-selection/cache validation, and a host-scoped domain-tool agent adapter. Generated domain types and actual HTTP API types derive from backend authority.
- The trusted **synthetic one-tree reference runtime** executes Arnav's pinned numerical source, not fabricated metrics. Its real HTTP demo covers positive shade, valid zero gain, revision staleness, failure and recovery. Feasibility remains `not_evaluated`; this is not Sheffield, a general SiteBundle importer or constrained search.
- The search consumer seam has controlled callback tests only. Real candidate/mask/search and independent feasibility producers, shared Alex/Arnav UI acceptance, full model-planner acceptance and actual Spark/device execution remain outstanding. The local UI proof does not close those gates. A local model's malformed or repeated actions fail closed rather than being presented as success.
- [BUILD.md](docs/BUILD.md) is the canonical exact-revision evidence/gate record. Earlier [validation (#35)](https://github.com/Pimentellll/sheffield-tree-planner/pull/35) and [job-control (#42)](https://github.com/Pimentellll/sheffield-tree-planner/pull/42) drafts are historical prototypes, not proof that this candidate is merged or accepted.

## Run the local backend candidate

Install the package using the isolated-environment commands below. Then:

```text
python -m tree_planner.api --version
python -m tree_planner.api --workspace ./canopy-workspace --port 8000
```

The server binds only loopback. `GET /api/v1/health` describes the actual installed version, worker mode and registered operations. No scientific handler is registered by default: unavailable analysis fails explicitly. Local-origin protection is not authentication against other OS users or processes.

For real synthetic calculation and the immutable-source setup, use [REFERENCE_RUNTIME.md](docs/REFERENCE_RUNTIME.md). `python -m tree_planner.evaluators.demo --output <fresh-directory> --numerical-source <pinned-numerical-checkout>` owns and stops its test server/worker and records actual HTTP receipts. The external numerical checkout is an explicit verified development dependency, not silently bundled science.

Development checks after installing `.[dev]` are `python -m pytest -q`, `python scripts/generate_api_types.py --check`, and Ruff. Live-model tests require explicit opt-in environment variables and are not implied by the default suite. `generated/openapi.json` is the route-free domain catalogue; `generated/http-openapi.json` describes implemented routes, with corresponding `contracts.ts` and `http.ts`. Pydantic input/output wire schema names remain exact; TypeScript uses documented `_Input`/`_Output` aliases.

## Run the readiness diagnostic

Requires Python 3.11 or newer. The diagnostic itself uses the standard library; the 0.2.0 package also installs the local backend's pinned runtime dependencies. No model weights or credentials are needed for its `environment` command. From a source checkout, install in an isolated environment:

Windows PowerShell, with [uv](https://docs.astral.sh/uv/) installed:

```powershell
uv venv --python 3.11 .venv
uv pip install --python .venv/Scripts/python.exe .
.venv/Scripts/sheffield-readiness.exe --version
.venv/Scripts/sheffield-readiness.exe environment
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/sheffield-readiness --version
.venv/bin/sheffield-readiness environment
.venv/bin/python -m unittest discover -s tests -v
```

The receipt describes the machine running the diagnostic and explicitly does not certify Spark/GPU availability. After a real model server and SSH tunnel exist:

```text
sheffield-readiness inference --base-url http://127.0.0.1:8001/v1 --model tree-planner-local --disable-thinking
```

Use the executable inside the environment above, or activate that environment. On Spark itself, use port `8000`. `--disable-thinking` is for the selected Nemotron profile; omit it for servers that do not support that option. Only loopback endpoints are accepted; there is no hosted fallback. Nonzero exit means failure, not permission to substitute a scripted answer. This proves transport and a harmless tool-observation exchange only; B09 still needs real domain integration.

Build the distributable with `uv build`. Install the resulting wheel, rather than an editable source tree, into a fresh environment for artifact proof. `pyproject.toml` is the only package-version source; see [CHANGELOG](CHANGELOG.md). The wheel packages the readiness diagnostic and local Python backend, including the synthetic runtime helper. Deployment templates and project documentation stay in this repository. No application container image, frontend bundle, model weights or external numerical checkout is implicitly included.

Prepared CI is configured to run the suite and source lint, check generated contracts and strict TypeScript, build wheel/sdist, and clean-install outside the source tree. Its installed smoke exercises `--version`, `--help`, `environment`, the actual API, and the synthetic one-tree calculation/failure/recovery path with durable per-run input/source hashes. Hosted execution remains unrun; the workflow does not download a model, contact a DGX or deploy. A matching, separately authorised version-tag push can create a private **draft** release with checksummed assets; no tag/release has been created and that trigger is not yet exercised.

## Start developing

1. Read the [development entry point](docs/README.md). The [three-agent execution PRD](docs/AGENT_EXECUTION_PRD.md) provides issue-sized handoffs, initial agent branches and integration rules.
2. Use [BUILD.md](docs/BUILD.md) as the single task/decision home. Begin B01 (shared schemas and portable application foundation) with B03 (site/rights audit) in parallel; B02 integration follows the required B01 models.
3. Agree the producer/consumer meaning in [CONTRACTS.md](docs/CONTRACTS.md) before parallel implementation. The first integrated target is **baseline → one proposed tree → computed difference → UI**, with stale-result rejection.
4. Implement and test against the [validation criteria](docs/VALIDATION.md). Application setup/run commands follow actual implementation; the readiness commands above cover only the diagnostic.

### Working references

- [Product and architecture](docs/SPEC.md)
- [Numerical specification](docs/NUMERICS.md)
- [Sources and evidence boundaries](docs/SOURCES.md)
- [Agentic architecture, feature review and team inputs](docs/references/AGENTIC_FEATURE_REVIEW.md)
- [Historical research handoff](docs/references/RESEARCH_HANDOFF.md)
- [Coding-assistant boundaries](AGENTS.md)

## Team and collaboration

- Ben — [bbeennyy860-cyber](https://github.com/bbeennyy860-cyber), backend and integration lane.
- Arnav — [reverez](https://github.com/reverez).
- Alex — [akurkar07](https://github.com/akurkar07).

Invited collaborators must accept GitHub's invitation before their write access is active. Proposed implementation responsibilities remain in BUILD; repository access does not establish agreement to every technical default.

Use small scoped branches and isolated worktrees/clones for concurrent writers. Update the relevant docs and tests with interface changes. Open teammate-facing PRs as drafts without requesting reviewers until the agreed review gate is cleared. No CODEOWNERS auto-review requests or automated deployment is configured by this bootstrap.

Advance development is underway; retain truthful prior-work/AI/asset provenance and confirm current entry eligibility separately. Do not commit credentials, restricted site assets, model weights, private working logs or generated proof bundles. This private repository has no open-source licence assigned by this setup; visibility/licensing changes require team approval.

Canonical repository: https://github.com/Pimentellll/sheffield-tree-planner (repository ID `1454048038`). Older owner/organisation locators redirect; they do not change the shared acceptance or publication gates.

## MVP and milestones

The [feature priority and milestone plan](docs/FEATURE_PRIORITIES.md) defines the competitive P0 MVP, P1 enhancements, longer-term P2/P3 scope, and the smaller first vertical slice. Development is active; BUILD remains the single task-status home. Draft components and passing isolated tests do not complete a milestone or establish product capability acceptance.
