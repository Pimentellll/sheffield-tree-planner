# CANOPY Sheffield — Product Vision v2 (design reference)

**State:** design reference only. It is **not** implementation evidence, not a record of any computed result, and not an accepted contract. [BUILD](../../BUILD.md) and the running code remain the authority for what is implemented. Added 13 November 2026 by Arnav.

## What is here

| File | What it is |
|---|---|
| [CANOPY_Sheffield_Product_Vision_v2.html](CANOPY_Sheffield_Product_Vision_v2.html) | The design artifact: one self-contained HTML gallery of eight 1600 × 1000 artboards. Open it in a browser to view. |
| [IMPLEMENTATION_HANDOFF.md](IMPLEMENTATION_HANDOFF.md) | Arnav's brief for implementing the design in the existing React/Three.js frontend: priorities, safeguards, tests and completion criteria. |

The artifact was supplied as `CANOPY Sheffield — Product Vision v2.html` and is stored here byte-for-byte under an ASCII file name.

- **Size:** 7,285,888 bytes
- **SHA-256:** `0c26555446b0654d53bd30f1d714ccb5e0e310e5efa5952bbf2eaab1a80ece04`

## The eight artboards

The artboards are states of **one** application, not eight separate pages.

| ID | Title in the file | Application state it depicts |
|---|---|---|
| B07 | Planting Studio (flagship) | Default Studio |
| B08 | Selected tree & footprint | Studio with one proposed tree selected |
| C01 | Budget & constraints editing | Scenario being edited |
| C02 | Stale result after edit | Draft differs from the accepted scenario |
| C03 | Running evaluation | Evaluation or search job in progress |
| C04 | Completed result & provenance | Completed result with its evidence |
| C05 | Alternatives & candidate ranking | Alternative layouts from a search |
| C06 | Scenario comparison | Compare workspace |

## Read this before using any number or picture from it

Everything below was checked by unpacking the file and reading its contents on 13 November 2026. The file was not rendered in a browser for this check.

- **Every figure is a design example.** The artboards show, among others, 39 proposed trees, £74,300, 5,520 (shade), "157 / 157 candidates", percentage progress values and "7 registered tools". None of these was produced by the CANOPY backend. Do not quote them as results, and do not copy them into the application as data.
- **The scene pictures are illustrative renders.** Six distinct JPEG images are embedded, and all six were looked at. The file's own alt text calls the main one an "Illustrative 3D view of Weston Park"; they are stylised low-poly renders of a park, paths, a pond and block buildings, not surveyed or licensed Sheffield geometry, and not output of the project's site pipeline. The artboards carry "SYNTHETIC" and "illustrative" labels; keep that labelling wherever the pictures are reused.
- **The budget example on C01 contradicts itself.** The editor shows £64,000 while the pence figure on the same artboard is 7,500,000 (which is £75,000). The intended example appears to be a change from £64,000 to £75,000.
- **Some depicted capabilities may not exist in the backend.** B08 shows "Marginal shade, this tree"; C03 shows phase-by-phase and percentage progress; B07 shows a count of agent tools. Whether the current API provides each of these has to be established from the code and [CONTRACTS](../../CONTRACTS.md), not assumed from the picture. Where it does not, the application must show an honest "not computed" or "unavailable" state.

The implementation handoff lists these and further points (shadow footprint overlays, candidate-ranking meaning, environmental benefits that are not geometric shade) as a discrepancy register to resolve before building.

## Third-party content inside the file

- **Fonts:** subsets of Inter, Manrope and JetBrains Mono, downloaded from Google Fonts when the file was saved, each under the SIL Open Font License 1.1. The licence texts are in the comment at the top of the HTML file. **Keep that comment in the file if you pass it on.**
- **JavaScript:** React and React DOM production builds (MIT licence, notices retained in the file) and a small generated page runtime.
- No credentials, personal email addresses, private host names or local file paths were found in the unpacked contents.

## How it relates to other documents

- [UI_DESIGN_REFERENCE](../../UI_DESIGN_REFERENCE.md) is the earlier visual reference. Where the two differ on look and layout, this artifact is the newer visual direction.
- [SPEC](../../SPEC.md), [CONTRACTS](../../CONTRACTS.md), [NUMERICS](../../NUMERICS.md) and [VALIDATION](../../VALIDATION.md) decide what the interface is allowed to show and how. A picture in this artifact never overrides them.
- [FEATURE_PRIORITIES](../../FEATURE_PRIORITIES.md) still orders the work. The handoff ranks a working, tested Studio above visual completeness.

## Status of the implementation

Not started at the time this folder was added. Progress is reported on the implementation pull request and in BUILD, not here.
