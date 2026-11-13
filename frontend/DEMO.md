# CANOPY demo runbook (frontend, STP-028)

What the live demo can truthfully show **today**, in order, with what to say and what not to claim. Every number on screen comes from a backend run that you can open in the evidence chain. Follows docs/VALIDATION.md §4 as far as the implemented system allows.

## Which backend

- **Physical runtime (recommended when Ben's `STP-arnav-logic-takeover` work is in your checkout):** real sun positions for each case, multi-tree search within budget, winter check, server-side location and scenario comparisons. From that checkout's environment: `python frontend/scripts/serve_physical.py --workspace ../canopy-physical-$(date +%H%M) --winter`. The tree moves between the three catalogue positions only. Rehearse with `npm run test:physical` (19 checks; every number is compared with the backend's stored record).
- **Reference runtime (fallback):** the one-tree, chosen-sun evaluator below. The script table that follows was written for it. With the physical runtime the numbers differ, and Search, the winter panel and the backend comparisons show real results instead of "unavailable".

## Reference-mode rehearsal

The steps and numeric examples below apply only to the reference runtime. For the primary physical demo, follow [README.md](README.md); inspect the actual stored results rather than reusing these values.

1. Fresh backend workspace each time (the browser checks assume revision 1):
   `.venv/bin/python frontend/scripts/serve_reference.py --workspace ../canopy-demo-$(date +%H%M) --numerical-source ../repo-numerical-inputs`
   (PowerShell: `.venv\Scripts\python.exe` and a new folder name.)
2. `cd frontend && CANOPY_SESSION=<that workspace>/session.json npm run dev`, open http://127.0.0.1:5173 in Chrome or Edge at 1920×1080.
3. Optional rehearsal: `CANOPY_DEV_WORKSPACE=<workspace> npm run test:browser` against a *separate* fresh workspace. It ends with a full set of screenshots in `frontend/artifacts/`.

## Script (≈4 minutes)

| # | Screen / action | Say | Do **not** say |
|---|---|---|---|
| 1 | **Sheffield sites** | "We audited two real candidates, Weston Park and Manor Fields. Neither is loaded yet: the LiDAR tiles, datum and rights checks are still open, and the app says so." | That we have analysed a Sheffield park. |
| 2 | **Planning studio**, point at the banner and SYNTHETIC tags | "Today's engine runs on an explicit synthetic test site. Everything you see is a real computation of that geometry." | That the site is Sheffield. |
| 3 | **Evaluate planting** | "The tree blocks the declared sun ray: 2 m²·h of extra shade on the target in this one-hour bin. Here is the run ID, the fingerprint, 13 bound source hashes." | Cooling, energy, CO₂, AQI or any bill saving. |
| 4 | Move the tree (drag, arrow keys or East = 20) | "The old number is struck through immediately: it describes the old position." | |
| 5 | **Accept changes & evaluate** | "New accepted revision, real recomputation: a valid zero. Zero is an honest answer, not an error." | |
| 6 | Requirements: budget £80, max trees 1, then **Discard**, then accept | "Edits are a draft until a human accepts them. Accepting creates a revision; results from earlier revisions are superseded." | That the agent can accept anything. |
| 7 | **Compare**: base rev 1 vs alternative rev 2 | "A controlled relocation: one placement moved, nothing else changed. 2 → 0, Δ −2 m²·h, from two stored runs." | That the comparison came from a server-side comparison tool (it didn't). |
| 8 | **Compare → Evidence**, expand the newest job | "Every number traces to a request, job, input fingerprint, code version and source hashes." | That a local model was involved (no inference device is recorded). |
| 9 | **Review pack** → Download | "The export copies the stored records unchanged, labels positions as ENU metres, and always lists the survey work that still has to happen." | That this is a planting proposal or permission. |

In reference mode search, server comparisons and winter cases are unavailable. The physical runtime supports these on its authored catalogue; agent narrative and a backend export handler remain unavailable.

## Recovery

| Symptom | Action |
|---|---|
| "Backend not connected" | Backend not running or wrong port. Restart `serve_reference.py` with a **new** workspace folder; reload. |
| `REVISION_CONFLICT` banner | Another accepted change (or a changed asset). The newer head is loaded and your draft is kept; accept again, or **Discard draft**. |
| Job "Failed" or deadline errors after a long session | Accepting any change renews the job deadline. Otherwise restart with a fresh workspace. |
| 3D view blank (no WebGL) | Use the East/North fields; every other panel works. |
| Tree off-screen | **Find tree** or **Reset view** (frames the target and the tree). |
| Wrong state after rehearsal | Start a new workspace; never reuse a rehearsal workspace for the live run. |
