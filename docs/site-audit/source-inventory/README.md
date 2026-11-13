# Sheffield recorded street-tree inventory: source, rights and output schema

**Status (13 Nov 2026):** importer, operator script and tests are drafted for [#69](https://github.com/Pimentellll/sheffield-tree-planner/issues/69) (GEO3D-01 / I1). **No real sample has been acquired yet.** The unit tests have run only in this repository's GitHub-hosted CI, on synthetic fixtures with urllib network calls blocked. Results for each revision are recorded on #69, and the #69 follow-up's tests count only once its CI has passed. Nothing has run on the DGX, and no laptop run was made. This folder may hold a reviewed sample and its manifest only after a real run and only once the rights allow it (see "Committing a sample" below). Today they do not, because every rights status is `unknown`. A council record is **not** a verified current crown, species, health state, surveyed position or planting permission. Nothing here completes the real-site gate [#30](https://github.com/Pimentellll/sheffield-tree-planner/issues/30).

## Decisions recorded for #69 (13 Nov 2026)

These were decided by the #69 owner's coordinating session under the owner's general delegation; **the owner's own confirmation is pending**. They are also written into every manifest as `recorded_decisions`. The flag `sample_envelope_applies_to_this_acquisition` is true only when the fetched `bbox_27700` is exactly the 1a envelope, and only then is the Weston Park coverage caveat added to `limitations`. They change nothing that can run today: acquisition still waits for an approved DGX window.

| Decision | Choice |
| --- | --- |
| Sample envelope | **1a:** Weston Park with surrounding streets, approximately `433700,387100,434500,387700` in EPSG:27700. The service count is recorded first. Park-interior coverage is unverified, because the layer likely holds highway trees only. |
| Rights | **2a:** all four purposes stay `unknown`. The OGL v3.0 vs INSPIRE End User Licence conflict rules out recording any as permitted. Nothing may be displayed, shared or exported until a person records the endpoint's actual terms. |
| `featurelocation` | **3a:** dropped from anything committed, including the review sample, and kept in local outputs only. A sample built with `--keep-location-text` is written as `local-only-sample-with-location-text.json`, is stamped `local_only`, and must not be committed. |

## Source (metadata inspected 13 Nov 2026; nothing bulk-downloaded)

| Item | Observed value | Where it came from |
| --- | --- | --- |
| Dataset | "Street Trees", publisher Sheffield City Council, "Location of street trees within Sheffield." | [data.gov.uk dataset page](https://www.data.gov.uk/dataset/957a85f3-d56b-4aed-9f29-5f8fe1363e57/street-trees) |
| Catalogue dates | "Updated 7 January 2026"; CKAN `metadata_modified` 2026-01-07T17:12:40 | Dataset page; [CKAN `package_show`](https://ckan.publishing.service.gov.uk/api/action/package_show?id=957a85f3-d56b-4aed-9f29-5f8fe1363e57) |
| Licence: catalogue record | UK Open Government Licence (`uk-ogl`), [OGL v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) | CKAN `license_id` / `license_title` / `license_url` |
| Licence: ArcGIS item | links the [INSPIRE End User Licence](https://www.ordnancesurvey.co.uk/documents/licensing/inspire-end-user-licence.pdf), which restricts use and redistribution | [ArcGIS item metadata](https://www.arcgis.com/sharing/rest/content/items/162d40a383fa48cbadc101ef18829bec?f=json), as cited in [Sources](../../SOURCES.md) [13]/[18]; reported by two reviewers; not re-fetched here |
| Service | ArcGIS FeatureServer layer 14, `https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/INSPIRE/FeatureServer/14` | CKAN resources (GeoJSON and ESRI REST links both point at this layer) |
| Layer | name `" Street Trees"`, `esriGeometryPoint`, no Z/M, `spatialReference` wkid/latestWkid **27700**, `objectIdField` `objectid`, `maxRecordCount` 1000, pagination supported, `copyrightText` empty | Layer `?f=pjson` |
| Fields | `objectid` (OID), `sitename` (string 40, alias "Site"), `featurelocation` (string 200, alias "Location"), `featuretypename` (string 8000, alias "Species"), `shape` (geometry) | Layer `?f=pjson` |
| Size | `{"count":36126}` for `where=1=1` | `returnCountOnly` query |
| Per-record dates | none: the layer declares no capture, planting or last-edit field | Layer field list |

Facts that shape the importer:

- **CRS:** `f=json` returns native British National Grid metres (EPSG:27700). The catalogue's `f=geojson` link returns server-reprojected WGS84 lon/lat. The importer uses `f=json` with `outSR=27700` so source geometry and CRS are preserved, and its output is deliberately not GeoJSON.
- **Missing values:** a schema probe of three records showed one without a `featurelocation` key. Missing values are kept as explicit `unknown`, never filled.
- **Address-like text:** `featurelocation` holds frontage text such as "Outside 7-9" (house-number positions). It refers to street frontages, not people, but the review sample (`review-sample.json`) drops it. `--keep-location-text` writes a separate `local-only-sample-with-location-text.json` that keeps it, for local inspection only (decision 3a).
- **Extent:** the layer's stored extent is not plausible for Sheffield. Coverage must come from the query results, not the layer extent.

## Rights (unresolved licence conflict; asset-level decision still needed)

The manifest's `rights` block uses the SiteBundle rights field names from [Contracts](../../CONTRACTS.md) and `contracts/site.py`: `source_id`, `source_reference`, `licence_reference`, `required_attribution`, the four `*_status` fields and `evidence`. The details are under `rights_detail`.

| Contract field | Recorded status | Evidence |
| --- | --- | --- |
| `local_use_status` | `unknown` | The catalogue says OGL v3.0; the ArcGIS item links the INSPIRE End User Licence; layer `copyrightText` is empty |
| `team_share_status` | `unknown` | as above |
| `public_display_status` | `unknown` | as above |
| `export_status` | `unknown` | as above |

**The two licence statements conflict.** OGL v3.0 would permit all four purposes with attribution, but the INSPIRE End User Licence restricts use and redistribution. A person must resolve which licence governs this layer before any status changes. **Unknown is not approval.**

`--acquisition-approval-ref` records only which approval authorised one download, under `acquisition_approval.reference`. It is not a rights decision and changes no status. Because the manifest is committable and this repository is public, the value must be one of the following, **never a person's name**:
- a role from a fixed list: `role:coordinator`, `role:data-owner`, `role:integrator`, `role:operator`, `role:site-lead` or `role:team-lead`. A list rather than any slug, so that a name cannot pass as a role;
- a reference to where the approval is recorded: `#<issue>`, `#<issue>#issuecomment-<id>`, or that GitHub URL.

Both `fetch` and `replay` check the exact form, and `replay` refuses a receipt without a valid one. Only allowlisted receipt keys are copied into the manifest, so an old free-text approval field in a local receipt never reaches it.

If OGL is confirmed, the attribution would be: *"Contains public sector information licensed under the Open Government Licence v3.0. Source: Sheffield City Council, Street Trees."*

## Producing the sample (approved environment only)

```bash
# Bounded EPSG:27700 envelope (metres, <= 25 km2), capped feature count. Raw bytes AND full
# outputs must live outside every git checkout/worktree, in separate directories. Reference
# the approval of this download by role or issue/comment, never by name (not a rights decision).
python scripts/prepare_tree_inventory.py fetch \
  --bbox-27700 433700,387100,434500,387700 --max-features 500 \
  --acquisition-approval-ref "#69#issuecomment-<id>" \
  --raw-dir <outside-repo>/raw-street-trees-001 --output-dir <outside-repo>/street-trees-001
# Same-source replay from the saved raw bytes (receipt and hashes re-checked) must reproduce
# inventory_sha256.
python scripts/prepare_tree_inventory.py replay \
  --raw-dir <outside-repo>/raw-street-trees-001 --output-dir <outside-repo>/street-trees-001-replay
```

**Envelope:** decision 1a above. It is a query filter only; no coordinate conversion is claimed. The desk audit's Weston Park / Manor Fields boxes are WGS84 and were not converted here, and the script rejects boxes that look like lon/lat.

**Script safeguards:**
- **Network:** HTTPS to the one fixed layer only. Redirects are refused, not followed, and each response's final URL is recorded and checked. Every site test runs with urllib calls (`urlopen`, `OpenerDirector.open`) blocked, and with socket connects to anything but loopback or a Unix socket blocked. Attempts are recorded as failures (`backend/tests/site/conftest.py`). Host names are not resolved by the guard, so a connect by host name other than `localhost` is refused. DNS lookups before a refused connect, and UDP sends, are not intercepted.
- **Service count:** a negative count is refused before any feature is fetched. Replay also refuses a receipt with an error-body or negative count, because `fetch` could not have completed one.
- **Feature cap:** with paging, pages stop at `--max-features`. A layer without paging allows only one uncapped query. In that case the service count must be an integer no larger than `--max-features`, or nothing is downloaded. The single page is also checked afterwards, so a layer that changed in between fails the acquisition.
- **Locations:** raw and output directories must be outside every git checkout or worktree, and must not be equal or nested. This is checked before any download.
- **Committable command:** the manifest's `command` is rebuilt from the parsed arguments. Paths become the fixed placeholders `<raw-dir>` and `<output-dir>`, because even a directory's final name could be a person's name. Option abbreviations are refused.
- **CRS:** queries ask for `f=json` with `outSR=27700`, never GeoJSON (which the server reprojects to WGS84). Every declared code must be an integer, and the declared codes must agree:
  - **Pages:** `latestWkid` and `wkid` must agree with each other.
  - **Layer metadata:** every code declared at the top level or under `sourceSpatialReference` must be 27700. `extent.spatialReference` describes only a stored bounding box (implausible for this layer), so it is recorded in the manifest and never decides.

  Contradictory metadata, such as 27700 with 3857, is refused rather than resolved by taking whichever code comes first. A layer that declares no code at all is recorded as `native CRS unverified`, not refused.
- **Request identity on replay:** before the fixed source is stamped on the outputs, the receipt must describe exactly the requests `fetch` would have made to the fixed layer:
  - its paging settings must be those `fetch` reads from the saved layer metadata;
  - the set of raw files must be exactly the ones `fetch` would have requested, using the same stop rule (an extra or post-stop page is refused, and so is a receipt missing a page `fetch` would still have requested);
  - every file must have been served with HTTP 200, and no response may be a service error body;
  - with paging, the pages together must hold no more than `max_features` records (`fetch` also refuses a page that holds more than it asked for);
  - the count must not be an error body or negative; without paging, it must be an integer no larger than `max_features`;
  - each file must carry the exact request URL, rebuilt with the same code, and must have been served from it;
  - without paging, the single query must hold no more than `max_features` records.
- **On failure:** the script always leaves `acquisition.json` (status, error, every request URL, final URL, retrieval time, HTTP status and SHA-256).
- **On replay:** it refuses:
  - an incomplete acquisition;
  - any file the receipt does not exactly account for;
  - non-contiguous pages;
  - any allowlisted receipt value without its expected form. That covers URLs on the fixed layer, whose query keys and values must be exactly those `fetch` sends; UTC timestamps; a finite BNG bbox; integer limits; and SHA-256 hex. Such values would reach the manifest.
- **Count provenance:** a failed count request is reported as such, not as "not requested". "Empty" means nothing was received. Records that arrive but are all rejected or conflicting are reported as "no usable records". "Matches" and "mismatch" also state how many records were kept and rejected, and how many source IDs conflicted.

**Outputs** (all written outside the repository):
- `inventory.json`
- `receipt.json`: counts, rejections, conflicts, coincident locations, schema drift and `inventory_sha256`.
- `manifest.json` contains:
  - resolved URLs, retrieval times and per-file SHA-256;
  - the receipt hash and the layer schema;
  - the rights;
  - the approval reference (a role or a reference, never a name);
  - the recorded decisions.

  Path arguments become fixed placeholders, and only allowlisted, validated receipt values are copied. **Publisher text is also copied and is not validated:** `layer_schema` (name, field names, types, aliases and lengths; `editingInfo`; `serviceItemId`) and `rights_detail.layer_copyright_text`. Review it before any commit.
- `review-sample.json`: a small sample **for review, not redistribution**. Its schema is tagged `#sample`, and each record lists any `withheld_for_sample` fields. Only `sitename` and `featuretypename` are kept; any other field is withheld.
- `local-only-sample-with-location-text.json` (only with `--keep-location-text`, written instead of `review-sample.json`): it also keeps `featurelocation` and is stamped `local_only`. Under decision 3a it is never committed.

**Committing a sample.** Copy `manifest.json` and `review-sample.json` into this folder only after review, **and only once `public_display_status` and `export_status` are both recorded as `permitted`**, because the repository is public. Under decision 2a every status is `unknown`, so nothing from a real run is committed today. Raw downloads, the full inventory and any local-only sample always stay out of git.

## Output schema (`canopy-source-tree-inventory/1`) — handoff for the viewer (Alex)

Each feature:

```json
{
  "feature_id": "sheffield-street-trees:<objectid>",
  "source_record_id": <objectid>,
  "evidence_class": "recorded_location",
  "geometry": {"kind": "point", "source_crs": "EPSG:27700", "x": <easting>, "y": <northing>,
               "x_axis": "easting", "y_axis": "northing", "unit": "metre"},
  "attributes": {"sitename": "...", "featurelocation": "...", "featuretypename": "..."},
  "unknown": ["<declared field absent, null or blank>"],
  "anomalies": ["<only when a value was present but not usable>"]
}
```

- **Selection key:** `feature_id`. It is stable **only within one recorded source snapshot**: an ArcGIS `objectid` may be renumbered by a republish or reload. The manifest records the layer's `serviceItemId`, `editingInfo` and metadata hash, and records must never be matched across snapshots by `feature_id` alone. Show `source_record_id`, `sitename` and `featuretypename` as source attributes. Label the species as "Species (as recorded by the council)", never as verified.
- **Rendering:** render as recorded locations, not measured canopies. List the `unknown` fields rather than hiding them.
- **Coordinates:** they are EPSG:27700 and are **not** converted to ENU/WGS84 here. Do not place them in the Three.js scene until a verified transform exists.

## Limitations for scene/asset integration (Ben)

- **Positions:** no verified geodesy. They are stored source coordinates with no accuracy statement. ENU/height/true-north conversion and known-point checks belong to the later verified transform work.
- **Not occluders:** no crowns, heights or leaf state; points are not baseline occluders. Mapping a point to a LiDAR crown, and exactly one baseline occluder per tree, is GEO3D Phase 2 and #30, not this slice.
- **Not merged:** records are never fused by proximity. Coincident distinct IDs are reported in the receipt; conflicting records under one ID are rejected and reported.
- **Coverage:** a bounded envelope sample is not citywide, and its `completeness_relative_to_service` field says whether the retrieved records match the service count for that query.
- **Licence:** rights remain `unknown` until the OGL vs INSPIRE conflict above is resolved.
- **Scope of the layer:** reviewers report that it likely covers council highway (street) trees only, not park, private or other trees. This is not verified here; absence from the layer is not absence of a tree.

## Known limits (from review, not fixed)

The non-paging cap and the completeness wording were addressed in the first #69 follow-up. The CRS agreement and replay request-identity checks from Ben's review of #77 are covered above. These remain:

- **Same-ID conflicts:** a same-ID copy rejected for bad geometry is not compared, so its valid twin is kept. Copies that differ only in non-string values hash as identical repeats.
- **Count status:** `fetch` stops on a count error body, and replay refuses such a receipt, so the importer's `service_error` count status is now reachable only by calling `build_inventory` directly.
- **Provenance on replay:** `replay` stamps the fixed Sheffield source only on a receipt that describes exactly `fetch`'s requests to the fixed layer. Those URLs can be recomputed from the receipt itself, so provenance still rests on the receipt's integrity, not on any server signature. A consistently hand-built receipt is not detected.
- **Real layer metadata:** where the real layer-14 metadata declares its CRS (top level, `sourceSpatialReference` or `extent.spatialReference`) has not been checked against a saved `layer.json`. The first real acquisition should confirm it.
