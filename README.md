# Sheffield Tree Planner

**Event-day coordination (13 November 2026):** [Parallel team task board, 15:00–16:00 functional freeze, Spark proof gates and presentation plan](docs/EVENT_DAY_EXECUTION_2026-11-13.md). This schedule is a coordination plan; completion requires recorded evidence. The older status section below describes the pre-integration readiness baseline and must not be read as the current status of separate development branches.

An urban tree-planning project for NVIDIA Hack for Impact Sheffield, 13 November 2026.

The intended system combines deterministic shade analysis and constrained tree-placement search with a local planning agent that investigates alternatives and explains computed evidence. Sheffield is the first case study; existing trees, winter sunlight, costs and uncertainty remain explicit.

## Status

**Application implementation has not started.** This branch adds an installable **readiness diagnostic**, a pinned inference-service candidate and a [DGX Spark access/integration runbook](docs/DGX_SPARK.md). It is not a simulator, product agent or verified Spark deployment. Protocol tests exercise a labelled synthetic HTTP fixture, not a model; hosted checks likewise do not provide GPU evidence.

## Run the readiness diagnostic

Requires Python 3.11 or newer. This diagnostic needs no runtime dependencies, model weights or credentials for its `environment` command. From a source checkout, install in an isolated environment:

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

Build the distributable with `uv build`. Install the resulting wheel, rather than an editable source tree, into a fresh environment for artifact proof. `pyproject.toml` is the only package-version source; see [CHANGELOG](CHANGELOG.md). The wheel packages the diagnostic only. Deployment templates and project documentation stay in this repository. There is no application image/package yet.

CI runs unit/protocol checks, builds wheel/sdist, clean-installs the wheel outside the source tree and runs `--version`, `--help` and `environment`. It does not download a model, contact a DGX or deploy. A matching, separately authorised version-tag push can create a private **draft** release with checksummed assets; no tag/release has been created and that trigger is not yet exercised.

## Start developing

1. Read the [development entry point](docs/README.md).
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

- Ben — [bbeennyy860-cyber](https://github.com/bbeennyy860-cyber), repository owner.
- Arnav — [reverez](https://github.com/reverez).
- Alex — [akurkar07](https://github.com/akurkar07).

Invited collaborators must accept GitHub's invitation before their write access is active. Proposed implementation responsibilities remain in BUILD; repository access does not establish agreement to every technical default.

Use small scoped branches and isolated worktrees/clones for concurrent writers. Update the relevant docs and tests with interface changes. Open teammate-facing PRs as drafts without requesting reviewers until the agreed review gate is cleared. No CODEOWNERS auto-review requests or automated deployment is configured by this bootstrap.

Advance development is planned; retain truthful prior-work/AI/asset provenance and confirm current entry eligibility separately. Do not commit credentials, restricted site assets, model weights, private working logs or generated proof bundles. This private repository has no open-source licence assigned by this setup; visibility/licensing changes require team approval.

Canonical repository: https://github.com/bbeennyy860-cyber/sheffield-tree-planner

## MVP and milestones

The [feature priority and milestone plan](docs/FEATURE_PRIORITIES.md) defines the competitive P0 MVP, P1 enhancements, longer-term P2/P3 scope, and the smaller first vertical slice. BUILD remains the single task-status home; the product capability status is still planned.
