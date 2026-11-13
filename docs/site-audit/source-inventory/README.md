# Sheffield recorded street-tree inventory: source, rights and output schema

**Status (13 Nov 2026):** importer, operator script and tests are drafted for [#69](https://github.com/Pimentellll/sheffield-tree-planner/issues/69) (GEO3D-01 / I1). **No real sample has been acquired yet**, and none of the code has been run: Arnav's execution is DGX-only, and no approved window has occurred. This folder will hold the reviewed redistributable sample and its manifest once that run happens. A council record is **not** a verified current crown, species, health state, surveyed position or planting permission. Nothing here completes the real-site gate [#30](https://github.com/Pimentellll/sheffield-tree-planner/issues/30).

## Source (metadata inspected 13 Nov 2026; nothing bulk-downloaded)

| Item | Observed value | Where it came from |
| --- | --- | --- |
| Dataset | "Street Trees", publisher Sheffield City Council, "Location of street trees within Sheffield." | [data.gov.uk dataset page](https://www.data.gov.uk/dataset/957a85f3-d56b-4aed-9f29-5f8fe1363e57/street-trees) |
| Catalogue dates | "Updated 7 January 2026"; CKAN `metadata_modified` 2026-01-07T17:12:40 | Dataset page; [CKAN `package_show`](https://ckan.publishing.service.gov.uk/api/action/package_show?id=957a85f3-d56b-4aed-9f29-5f8fe1363e57) |
| Licence stated by the publisher | UK Open Government Licence (`uk-ogl`), [OGL v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) | CKAN `license_id` / `license_title` / `license_url` |
| Service | ArcGIS FeatureServer layer 14, `https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/INSPIRE/FeatureServer/14` | CKAN resources (GeoJSON and ESRI REST links both point at this layer) |
| Layer | name `" Street Trees"`, `esriGeometryPoint`, no Z/M, `spatialReference` wkid/latestWkid **27700**, `objectIdField` `objectid`, `maxRecordCount` 1000, pagination supported, `copyrightText` empty | Layer `?f=pjson` |
| Fields | `objectid` (OID), `sitename` (string 40, alias "Site"), `featurelocation` (string 200, alias "Location"), `featuretypename` (string 8000, alias "Species"), `shape` (geometry) | Layer `?f=pjson` |
| Size | `{"count":36126}` for `where=1=1` | `returnCountOnly` query |
| Per-record dates | none: the layer declares no capture, planting or last-edit field | Layer field list |

Facts that shape the importer:

- **CRS:** `f=json` returns native British National Grid metres (EPSG:27700). The catalogue's `f=geojson` link returns server-reprojected WGS84 lon/lat. The importer uses `f=json` with `outSR=27700` so source geometry and CRS are preserved, and its output is deliberately not GeoJSON.
- **Missing values:** a schema probe of three records showed one without a `featurelocation` key. Missing values are kept as explicit `unknown`, never filled.
- **Address-like text:** `featurelocation` holds frontage text such as "Outside 7-9" (house-number positions). It refers to street frontages, not people, but the redistributable sample drops it by default (`--keep-location-text` to override after review).
- **Extent:** the layer's stored extent is not plausible for Sheffield. Coverage must come from the query results, not the layer extent.

## Rights (asset-level decision still needed)

| Purpose | Recorded status | Evidence |
| --- | --- | --- |
| Local use | `unknown` | Publisher states OGL v3.0 in catalogue metadata; layer `copyrightText` is empty |
| Team sharing | `unknown` | as above |
| Public display | `unknown` | as above |
| Export | `unknown` | as above |

OGL v3.0 would permit all four purposes with attribution, but [the council notes some of its data carries other terms](https://www.sheffield.gov.uk/your-city-council/about-council/access-to-information). A reviewer must confirm that the stated licence covers this layer before any status changes; **unknown is not approval**. Proposed attribution when approved: *"Contains public sector information licensed under the Open Government Licence v3.0. Source: Sheffield City Council, Street Trees."*

## Producing the sample (approved environment only)

```bash
# Bounded EPSG:27700 envelope (metres, <= 25 km2), capped feature count. Raw bytes AND full
# outputs must live outside the repository. Downloading is local use, so name the approval.
python scripts/prepare_tree_inventory.py fetch \
  --bbox-27700 <xmin,ymin,xmax,ymax> --max-features 500 \
  --local-use-approved-by "<who approved, and where it is recorded>" \
  --raw-dir <outside-repo>/raw-street-trees-001 --output-dir <outside-repo>/street-trees-001
# Same-source replay from the saved raw bytes (receipt and hashes re-checked) must reproduce
# inventory_sha256.
python scripts/prepare_tree_inventory.py replay \
  --raw-dir <outside-repo>/raw-street-trees-001 --output-dir <outside-repo>/street-trees-001-replay
```

**Choosing the envelope:** agree it with the site work. The desk audit's Weston Park / Manor Fields boxes are WGS84 and were not converted here, because no conversion is accepted in this slice. The script rejects boxes that look like lon/lat.

**Script safeguards:**
- **On failure:** the script always leaves `acquisition.json` (status, error, every request URL, retrieval time, HTTP status and SHA-256).
- **On replay:** it refuses an incomplete acquisition, any file the receipt does not exactly account for, and non-contiguous pages.
- **Count provenance:** a failed count request is reported as such, not as "not requested". An empty result is reported as empty.

**Outputs** (all written outside the repository):
- `inventory.json`
- `receipt.json`: counts, rejections, conflicts, coincident locations, schema drift and `inventory_sha256`.
- `manifest.json`: resolved URLs, retrieval times, per-file SHA-256, the receipt hash, the layer schema, the rights and the approval reference. Path arguments are redacted, so the manifest is safe to commit.
- `redistributable-sample.json`: its schema is tagged `#sample`, and each record lists any `withheld_for_sample` fields.

After review, copy only `manifest.json` and the small sample here. Raw downloads and the full inventory stay out of git.

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
- **Licence:** rights remain `unknown` until the asset-level licence review above.
