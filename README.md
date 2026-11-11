# Sheffield Tree Planner

An urban tree-planning project for NVIDIA Hack for Impact Sheffield, 13 November 2026.

The intended system combines deterministic shade analysis and constrained tree-placement search with a local planning agent that investigates alternatives and explains computed evidence. Sheffield is the first case study; existing trees, winter sunlight, costs and uncertainty remain explicit.

## Status

**Development specification ready; application implementation has not started.** This initial repository contains the reviewed working docs and collaboration guidance, not a running simulator, benchmark or Spark deployment. No application test suite or GitHub Actions workflow is present yet.

## Start developing

1. Read the [development entry point](docs/README.md).
2. Use [BUILD.md](docs/BUILD.md) as the single task/decision home. Begin B01 (shared schemas and portable application foundation) with B03 (site/rights audit) in parallel; B02 integration follows the required B01 models.
3. Agree the producer/consumer meaning in [CONTRACTS.md](docs/CONTRACTS.md) before parallel implementation. The first integrated target is **baseline → one proposed tree → computed difference → UI**, with stale-result rejection.
4. Implement and test against the [validation criteria](docs/VALIDATION.md). Setup/run commands will be documented after the actual paths are exercised; none are invented here.

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
