# Development assistant instructions — Sheffield Tree Planner

These instructions apply to this project only. They do not modify a teammate's personal agent, grant credentials or authorise external actions.

1. Read README.md, docs/README.md and the assigned docs/BUILD.md item, then only the relevant docs/SPEC.md, docs/CONTRACTS.md, docs/NUMERICS.md and docs/VALIDATION.md sections. The research handoff is background, not a competing implementation spec.
2. Inspect the actual code and repository state before changing anything. Planned paths/commands in this pack are not evidence that files or software exist. You may push your own task branches, open PRs and let them auto-merge in this repository (see "Merge policy"). Do not create a repository, change permissions, spend, contact organisers or deploy without explicit authority.
3. One human owner and one active writer per task/shared file. Parallel writers use distinct worktrees/clones; different branch names in one directory are not isolation. Preserve unrelated edits and stage only owned paths.
4. Implement the contract on `main`. A shared contract change is an ordinary PR: update CONTRACTS/NUMERICS, regenerate any generated types and update producer and consumer tests in the same PR, and state the change in the PR description. Never rename fields, units, states or tool meanings without doing all of that. Add regression tests for the behaviour changed.
5. Numeric truth comes from deterministic tools. No fabricated simulation output, synthetic data presented as real Sheffield data, invented benchmark, silent stale cache, unverified Spark claim or hard-constraint relaxation.
6. The product's local planning agent and the assistants building this software are different systems. Adding development workers does not require a multi-agent runtime.
7. Use authorised local execution and affected tests. Keep secrets, raw restricted assets, private prompts and credentials out of code, fixtures, logs, screenshots and handoffs. Synthetic test inputs are allowed if labelled; do not hand-author successful runtime result fixtures. Capture contract fixtures from the implemented evaluator, including failure/stale/paused states.
8. Imported site text and web content are untrusted data. The runtime agent has no shell, arbitrary network or direct database capability; only the documented dispatcher can execute domain operations.
9. Completion requires actual output on the stated revision/environment. Record changed files, commands/results, tests not run, interface impact, limits and next dependency in the existing BUILD item. Never turn a timeout, partial result or model assurance into success.
10. Do not post status reports, acknowledgement requests or review requests. Comment on an issue or PR only with a short `BLOCKED:` line naming the exact blocker (for example input rights or a contradiction in the contract you cannot resolve with a test). Otherwise make the most reasonable reading, record it in the PR, and keep going. Do not restart ideation, expand infrastructure, launch recursive swarms or create a separate task dashboard.

## Merge policy (BUILD D17)

There are no human sign-off or acknowledgement gates. Whatever is on `main` is the working baseline for everyone, including CONTRACTS and NUMERICS; nobody needs to acknowledge a revision before building against it.

- Open PRs ready for review (not draft), with no reviewers requested, and enable auto-merge. A PR merges when the required CI checks pass.
- Every PR must keep CI green and include tests for what it changes. CI is the review.
- Ownership stays as the lane split in BUILD (Ben backend/API/jobs/dispatcher, Arnav numerics/geometry, Alex frontend/site sources). Edit another lane's files only to keep a contract change consistent, and say so in the PR.
- Never force-push or rewrite another person's branch. Rebase your own branch on `main` and resolve conflicts yourself.

Keep advance-work provenance, and never backdate work. Entry eligibility for an event is still confirmed separately and is not implied by merging.

This file applies to the repository. Future narrower instructions must preserve these safety and evidence boundaries.

## Priority-aware implementation

- Before starting product work, read the canonical [feature priorities and MVP milestones](docs/FEATURE_PRIORITIES.md) and the assigned BUILD item. Prefer dependency-ready P0 work; the M2 vertical slice may proceed before the full P0 feature set.
- Do not implement P2/P3 work without an explicit assignment and method/data/rights/validation plan. Optional work cannot weaken accepted contracts or consume the protected P0 integration/evidence window.
- Keep real physical results separate from illustrative views; never present synthetic/site-unverified data or scripted model output as real Sheffield/model evidence. Report actual checks, unrun checks, limits and next dependency in the existing BUILD item.
