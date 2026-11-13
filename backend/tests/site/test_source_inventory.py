"""Recorded-tree source inventory (#69).

All pages here are a tiny SYNTHETIC fixture shaped like the publisher's ArcGIS ``f=json``
query responses (field names and EPSG:27700 point form as observed in the layer metadata).
Values are invented test values, not Sheffield records; the real sample is produced only
by ``scripts/prepare_tree_inventory.py fetch`` in the approved environment.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import urllib.error
import urllib.request

import pytest

from tree_planner.canonical import content_hash
from tree_planner.site.source_inventory import (
    EVIDENCE_CLASS,
    INVENTORY_SCHEMA,
    InventoryError,
    build_inventory,
    redistributable_sample,
)

SOURCE = {"source_key": "synthetic-street-trees", "layer_url": "https://example.invalid/layer"}
FIELDS = ["sitename", "featurelocation", "featuretypename"]
BNG = {"wkid": 27700, "latestWkid": 27700}


def feature(objectid, x, y, **attributes):
    return {"attributes": {"objectid": objectid, **attributes}, "geometry": {"x": x, "y": y}}


def page(features, *, more=False, sr=BNG):
    value = {"geometryType": "esriGeometryPoint", "features": features}
    if sr is not None:
        value["spatialReference"] = sr
    if more:
        value["exceededTransferLimit"] = True
    return value


SYNTHETIC_PAGES = [
    page(
        [
            feature(1, 430000.5, 380000.25, sitename="SYNTHETIC ROAD", featurelocation="Outside 1",
                    featuretypename="Synthetic species A"),
            feature(2, 430010.0, 380010.0, sitename="SYNTHETIC ROAD", featuretypename="Synthetic B"),
        ],
        more=True,
    ),
    page(
        [
            # Identical repeat of objectid 2 (pagination overlap) plus a new record.
            feature(2, 430010.0, 380010.0, sitename="SYNTHETIC ROAD", featuretypename="Synthetic B"),
            feature(3, 430020.0, 380020.0, sitename="", featurelocation=None,
                    featuretypename="Synthetic C"),
        ]
    ),
]


def build(pages=None, **kwargs):
    return build_inventory(
        SYNTHETIC_PAGES if pages is None else pages,
        source=SOURCE,
        id_field="objectid",
        attribute_fields=FIELDS,
        **kwargs,
    )


def test_observed_schema_maps_to_versioned_source_backed_records():
    built = build(service_count=3)
    inventory, receipt = built["inventory"], built["receipt"]
    assert inventory["schema"] == INVENTORY_SCHEMA and inventory["source_crs"] == "EPSG:27700"
    assert inventory["id_stability"].startswith("per-snapshot")
    assert [f["feature_id"] for f in inventory["features"]] == [
        "synthetic-street-trees:1",
        "synthetic-street-trees:2",
        "synthetic-street-trees:3",
    ]
    first = inventory["features"][0]
    assert first["source_record_id"] == 1 and first["evidence_class"] == EVIDENCE_CLASS
    assert first["geometry"] == {
        "kind": "point",
        "source_crs": "EPSG:27700",
        "x": 430000.5,
        "y": 380000.25,
        "x_axis": "easting",
        "y_axis": "northing",
        "unit": "metre",
    }
    assert first["attributes"] == {
        "sitename": "SYNTHETIC ROAD",
        "featurelocation": "Outside 1",
        "featuretypename": "Synthetic species A",
    }
    assert receipt["counts"]["completeness_relative_to_service"].startswith("matches")
    assert receipt["inventory_sha256"] == content_hash(inventory)


def test_output_is_not_mislabeled_as_rfc7946_geojson():
    inventory = build()["inventory"]
    text = json.dumps(inventory)
    assert '"FeatureCollection"' not in text and '"Point"' not in text
    assert all(f["geometry"]["kind"] == "point" for f in inventory["features"])
    assert inventory["coordinate_conversion"].startswith("none")


def test_missing_attributes_stay_unknown_and_are_never_filled():
    by_id = {f["source_record_id"]: f for f in build()["inventory"]["features"]}
    assert "featurelocation" not in by_id[2]["attributes"]
    assert by_id[2]["unknown"] == ["featurelocation"]
    assert by_id[3]["attributes"] == {"featuretypename": "Synthetic C"}
    assert by_id[3]["unknown"] == ["sitename", "featurelocation"]


def test_identical_repeats_are_kept_once_and_counted():
    counts = build()["receipt"]["counts"]
    assert counts["features_received"] == 4 and counts["features_kept"] == 3
    assert counts["identical_repeats_dropped"] == 1 and counts["conflicting_source_ids"] == 0


def test_conflicting_records_sharing_an_id_are_rejected_not_overwritten():
    pages = copy.deepcopy(SYNTHETIC_PAGES)
    pages[1]["features"][0]["attributes"]["featuretypename"] = "Different species"
    built = build(pages)
    ids = [f["source_record_id"] for f in built["inventory"]["features"]]
    assert ids == [1, 3]
    conflict = built["receipt"]["conflicts"][0]
    assert conflict["source_record_id"] == 2 and len(conflict["occurrences"]) == 2


def test_missing_ids_and_invalid_coordinates_are_rejected_with_reasons():
    pages = [
        page(
            [
                {"attributes": {"sitename": "NO ID"}, "geometry": {"x": 1.0, "y": 2.0}},
                feature("7", 1.0, 2.0),  # string id
                feature(8, None, 2.0),
                feature(9, "430000", 380000.0),
                {"attributes": {"objectid": 10}},  # no geometry
                feature(11, 430000.0, 380000.0),
            ]
        )
    ]
    built = build(pages)
    assert [f["source_record_id"] for f in built["inventory"]["features"]] == [11]
    reasons = [r["reason"] for r in built["receipt"]["rejected"]]
    assert reasons.count("missing or non-integer objectid") == 2
    assert reasons.count("missing or non-finite point") == 3


def test_non_finite_coordinates_are_rejected():
    for bad in (float("nan"), float("inf"), float("-inf"), 10**400):  # 10**400: float overflow
        built = build([page([feature(1, bad, 1.0), feature(2, 1.0, 1.0)])])
        assert [f["source_record_id"] for f in built["inventory"]["features"]] == [2]


@pytest.mark.parametrize(
    "sr",
    [
        None,
        {},
        {"wkid": "27700"},
        {"wkid": 3857},
        {"wkt": "PROJCS[...]"},
        # Ben's review of #77 (1): contradictory codes are refused, whichever comes first.
        {"wkid": 3857, "latestWkid": 27700},
        {"wkid": 27700, "latestWkid": 3857},
        {"wkid": 27700, "latestWkid": "27700"},
    ],
)
def test_unknown_or_unsupported_crs_fails_closed(sr):
    with pytest.raises(InventoryError):
        build([page([feature(1, 1.0, 1.0)], sr=sr)])


def test_pages_with_different_crs_fail_closed():
    pages = [page([feature(1, 1.0, 1.0)]), page([feature(2, 1.0, 1.0)], sr={"wkid": 4326})]
    with pytest.raises(InventoryError):
        build(pages)


def test_wgs84_source_is_labelled_wgs84_never_bng():
    built = build([page([feature(1, -1.43, 53.42)], sr={"wkid": 4326})])
    geometry = built["inventory"]["features"][0]["geometry"]
    assert geometry["source_crs"] == "EPSG:4326" and geometry["unit"] == "degree"
    assert (geometry["x"], geometry["y"]) == (-1.43, 53.42)
    assert (geometry["x_axis"], geometry["y_axis"]) == ("longitude", "latitude")


def test_non_point_layers_and_service_errors_fail_closed():
    line = page([feature(1, 1.0, 1.0)])
    line["geometryType"] = "esriGeometryPolyline"
    for pages in ([line], [{"error": {"code": 400}}], [], [{"features": "nope", **BNG}]):
        with pytest.raises(InventoryError):
            build(pages)


def test_coincident_distinct_ids_are_kept_and_reported_not_fused():
    pages = [page([feature(1, 430000.0, 380000.0), feature(2, 430000.0, 380000.0)])]
    built = build(pages)
    assert len(built["inventory"]["features"]) == 2
    group = built["receipt"]["coincident_locations"][0]
    assert group["feature_ids"] == ["synthetic-street-trees:1", "synthetic-street-trees:2"]


def test_pagination_and_count_provenance_is_reported_honestly():
    truncated = build(SYNTHETIC_PAGES[:1], service_count=3, requested_limit=2)["receipt"]
    assert truncated["counts"]["last_page_reported_more_records"] is True
    assert truncated["counts"]["completeness_relative_to_service"].startswith("incomplete")
    assert truncated["counts"]["requested_limit"] == 2
    mismatch = build(service_count=5)["receipt"]["counts"]["completeness_relative_to_service"]
    assert mismatch.startswith("mismatch")
    unknown = build()["receipt"]["counts"]["completeness_relative_to_service"]
    assert unknown == "unknown: no service count was requested"


def test_failed_count_requests_are_not_reported_as_not_requested():
    for status, text in (
        ("service_error", "unknown: the service count request returned an error"),
        ("non_integer", "unknown: the service count response had no integer count"),
    ):
        counts = build(service_count_status=status)["receipt"]["counts"]
        assert counts["completeness_relative_to_service"] == text
        assert counts["service_count_status"] == status


def test_empty_result_is_reported_as_empty_not_matching():
    counts = build([page([])], service_count=0)["receipt"]["counts"]
    assert counts["features_kept"] == 0
    assert counts["completeness_relative_to_service"].startswith("empty")


def test_completeness_never_says_empty_or_matches_when_records_were_unusable():
    """L4: records that arrive without usable IDs, or that are all rejected, are reported as
    such, never as an empty result or a match."""
    no_ids = [page([{"attributes": {"sitename": "NO ID"}, "geometry": {"x": 1.0, "y": 2.0}}] * 2)]
    counts = build(no_ids, service_count=2)["receipt"]["counts"]
    text = counts["completeness_relative_to_service"]
    assert counts["features_received"] == 2 and counts["features_kept"] == 0
    assert text.startswith("no usable records: all 2 retrieved") and "empty" not in text
    bad_points = [page([feature(1, None, 1.0), feature(2, "x", 1.0)])]
    counts = build(bad_points, service_count=2)["receipt"]["counts"]
    assert counts["distinct_source_ids_seen"] == 2  # would have matched the service count
    assert counts["completeness_relative_to_service"].startswith("no usable records")
    kept = build(service_count=3)["receipt"]["counts"]["completeness_relative_to_service"]
    assert kept == (
        "matches the service-reported count for this query "
        "(3 kept, 0 rejected, 0 conflicting source IDs)"
    )
    # A conflicting ID is named in the tally, so kept + rejected never silently falls short.
    conflict = [
        page([feature(1, 430000.0, 380000.0), feature(2, 430010.0, 380010.0, sitename="A"),
              feature(2, 430010.0, 380010.0, sitename="B"), feature(3, 430020.0, 380020.0)])
    ]
    text = build(conflict, service_count=3)["receipt"]["counts"]["completeness_relative_to_service"]
    assert text.endswith("(2 kept, 0 rejected, 1 conflicting source IDs)"), text


def test_completeness_counts_each_source_id_once():
    # One ID kept from one page and rejected (bad point) on another is still one source ID.
    pages = [page([feature(5, 430000.0, 380000.0)]), page([feature(5, None, 380000.0)])]
    counts = build(pages, service_count=1)["receipt"]["counts"]
    assert counts["features_kept"] == 1 and counts["rejected"] == 1
    assert counts["distinct_source_ids_seen"] == 1
    assert counts["completeness_relative_to_service"].startswith("matches")


def test_schema_drift_is_reported_and_its_values_are_not_imported():
    pages = [page([feature(1, 1.0, 1.0, sitename="S", undeclared_owner="x")])]
    built = build(pages)
    assert built["receipt"]["schema_drift_undeclared_attribute_counts"] == {"undeclared_owner": 1}
    assert "undeclared_owner" not in json.dumps(built["inventory"])


def test_declared_but_not_imported_fields_are_not_reported_as_drift():
    pages = [page([feature(1, 1.0, 1.0, sitename="S", lastedited=1700000000000)])]
    built = build(pages, declared_fields=["objectid", *FIELDS, "lastedited", "shape"])
    assert built["receipt"]["schema_drift_undeclared_attribute_counts"] == {}
    assert "lastedited" not in json.dumps(built["inventory"]["features"])


def test_non_string_attribute_values_are_not_coerced():
    built = build([page([feature(1, 1.0, 1.0, sitename=42)])])
    record = built["inventory"]["features"][0]
    assert "sitename" not in record["attributes"] and "sitename" in record["unknown"]
    assert record["anomalies"] == ["sitename: non-string value not used"]


def test_same_source_replay_is_byte_identical_and_input_is_not_modified():
    snapshot = copy.deepcopy(SYNTHETIC_PAGES)
    first, second = build(service_count=3), build(service_count=3)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["receipt"]["inventory_sha256"] == second["receipt"]["inventory_sha256"]
    assert SYNTHETIC_PAGES == snapshot


def test_redistributable_sample_records_what_it_removed():
    inventory = build()["inventory"]
    sample = redistributable_sample(inventory, limit=2, drop_attributes=("featurelocation",))
    assert sample["schema"] == INVENTORY_SCHEMA + "#sample"
    assert len(sample["features"]) == 2
    assert all("featurelocation" not in f["attributes"] for f in sample["features"])
    first, second = sample["features"]
    assert first["withheld_for_sample"] == ["featurelocation"]  # supplied, then withheld
    assert "withheld_for_sample" not in second  # never supplied: stays in "unknown"
    assert second["unknown"] == ["featurelocation"]
    assert sample["sample"]["attributes_removed_for_sample"] == ["featurelocation"]
    assert sample["sample"]["of_inventory_sha256"] == content_hash(inventory)
    assert inventory["features"][0]["attributes"]["featurelocation"] == "Outside 1"  # unmodified
    with pytest.raises(InventoryError):
        redistributable_sample(inventory, limit=0)


# --------------------------------------------------------------------------- operator script


# Real network access is blocked for every test in this directory by the autouse
# ``no_network`` fixture in backend/tests/site/conftest.py.


def test_the_site_network_guard_is_active():
    import socket

    assert urllib.request.urlopen.__name__ == "refuse"
    assert urllib.request.OpenerDirector.open.__name__ == "refuse"
    assert socket.socket.connect.__name__ == "guarded_connect"
    assert socket.socket.connect_ex.__name__ == "guarded_connect_ex"


def _strings(value):
    """Every string inside a parsed JSON value (so path checks don't depend on escaping)."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


def _script():
    path = Path(__file__).resolve().parents[3] / "scripts" / "prepare_tree_inventory.py"
    spec = importlib.util.spec_from_file_location("prepare_tree_inventory", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LAYER = {
    "name": " Synthetic Street Trees",
    "geometryType": "esriGeometryPoint",
    "objectIdField": "objectid",
    "maxRecordCount": 1000,
    "spatialReference": BNG,
    "copyrightText": "",
    "fields": [
        {"name": "objectid", "type": "esriFieldTypeOID", "alias": "OBJECTID"},
        {"name": "sitename", "type": "esriFieldTypeString", "alias": "Site", "length": 40},
        {"name": "featurelocation", "type": "esriFieldTypeString", "alias": "Location"},
        {"name": "featuretypename", "type": "esriFieldTypeString", "alias": "Species"},
        {"name": "shape", "type": "esriFieldTypeGeometry", "alias": "SHAPE"},
    ],
}


def _write_raw(raw_dir: Path, pages, count=None, status="complete", extra_files=(), layer=None,
               paging=None):
    """SYNTHETIC raw directory in the exact layout `fetch` writes (receipt + hashed files).

    The layer metadata states the same paging settings the receipt records (as fetch reads
    them), and each file gets the request URL fetch would have made for it, if any."""
    raw_dir.mkdir()
    count = {"count": 3} if count is None else count
    paging = len(pages) > 1 if paging is None else paging
    layer = {
        **(LAYER if layer is None else layer),
        "maxRecordCount": 2,
        "advancedQueryCapabilities": {"supportsPagination": paging},
    }
    files = []
    entries = [("layer.json", layer), ("count.json", count)]
    entries += [(f"page-{i:04d}.json", p) for i, p in enumerate(pages)]
    for name, value in [*entries, *extra_files]:
        body = json.dumps(value).encode()
        (raw_dir / name).write_bytes(body)
        files.append(
            {"file": name, "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body),
             "http_status": 200}
        )
    acquisition = {
        "layer_url": SYNTHETIC_RECEIPT["layer_url"],
        "bbox_27700": list(SYNTHETIC_RECEIPT["bbox_27700"]),
        "status": status,
        "max_features": 500,
        "page_size": 2,
        "supports_pagination": paging,
        "acquisition_approval_ref": "role:operator",
        "files": files,
    }
    # The request URLs fetch() would have made for these files (replay requires them).
    urls = _script().expected_request_urls(acquisition, "objectid", list(pages))
    for record in files:
        if record["file"] in urls:
            record["url"] = record["final_url"] = urls[record["file"]]
    (raw_dir / "acquisition.json").write_text(json.dumps(acquisition))
    return acquisition


# A small BNG box that is deliberately NOT the decision-1a envelope.
SYNTHETIC_RECEIPT = {
    "layer_url": "https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/INSPIRE/FeatureServer/14",
    "bbox_27700": (430000.0, 380000.0, 430100.0, 380100.0),
}


def test_replay_refuses_files_not_requested_from_the_fixed_layer(tmp_path):
    """Ben's review of #77 (3): before SOURCE is stamped, every raw file must carry the exact
    request URL fetch would have made to the fixed layer, served from that same URL."""
    script = _script()
    cases = {
        "missing-url": lambda a: a["files"][1].pop("url"),
        "other-bbox": lambda a: a["files"][1].update(
            url=script._count_url((430000.0, 380000.0, 430200.0, 380200.0)),
            final_url=script._count_url((430000.0, 380000.0, 430200.0, 380200.0)),
        ),
        "served-elsewhere": lambda a: a["files"][0].update(final_url=script.LAYER_URL + "/query?f=json"),
        "wrong-offset": lambda a: a["files"][3].update(
            url=a["files"][3]["url"].replace("resultOffset=2", "resultOffset=0"),
            final_url=a["files"][3]["url"].replace("resultOffset=2", "resultOffset=0"),
        ),
        "no-bbox": lambda a: a.pop("bbox_27700"),
        "paging-differs-from-layer": lambda a: a.update(page_size=3),
    }
    for label, tamper in cases.items():
        raw = tmp_path / label / "raw"
        raw.parent.mkdir()
        acquisition = _write_raw(raw, SYNTHETIC_PAGES)
        assert acquisition["files"][3]["file"] == "page-0001.json"
        tamper(acquisition)
        (raw / "acquisition.json").write_text(json.dumps(acquisition))
        with pytest.raises(SystemExit, match="replay refused"):
            script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / label / "o")])
        assert not (tmp_path / label / "o").exists(), label
    # Untampered, the same receipt replays.
    raw = tmp_path / "ok" / "raw"
    raw.parent.mkdir()
    _write_raw(raw, SYNTHETIC_PAGES)
    assert script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "ok" / "o")]) == 0


def test_replay_refuses_pages_fetch_would_never_have_requested(tmp_path):
    """Ben's review of #77 (3): the set of raw files must be exactly fetch's requests."""
    script = _script()
    first, second = SYNTHETIC_PAGES[0]["features"], SYNTHETIC_PAGES[1]["features"]
    # Non-paging receipt with an extra page-0001 (fetch makes one single query).
    raw = tmp_path / "extra" / "raw"
    raw.parent.mkdir()
    acquisition = _write_raw(raw, [page(first), page(second)], paging=False)
    assert "url" not in acquisition["files"][3]  # fetch never requested it
    with pytest.raises(SystemExit, match="replay refused: the raw files"):
        script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "extra" / "o")])
    # Paging receipt whose first page did not report more records: fetch stopped there.
    raw = tmp_path / "stopped" / "raw"
    raw.parent.mkdir()
    _write_raw(raw, [page(first), page(second)], paging=True)
    with pytest.raises(SystemExit, match="replay refused: the raw files"):
        script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "stopped" / "o")])
    # Ben's review of #77 (2), replay side: a single query over the cap is refused too.
    raw = tmp_path / "cap" / "raw"
    raw.parent.mkdir()
    acquisition = _write_raw(raw, [page(first + second)], paging=False)
    acquisition["max_features"] = 3
    (raw / "acquisition.json").write_text(json.dumps(acquisition))
    with pytest.raises(SystemExit, match="more than max_features 3"):
        script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "cap" / "o")])
    # A layer without objectIdField cannot show which ordered requests were made.
    raw = tmp_path / "noid" / "raw"
    raw.parent.mkdir()
    _write_raw(raw, SYNTHETIC_PAGES, layer={k: v for k, v in LAYER.items() if k != "objectIdField"})
    with pytest.raises(SystemExit, match="declares no objectIdField"):
        script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "noid" / "o")])
    for label in ("extra", "stopped", "cap", "noid"):
        assert not (tmp_path / label / "o").exists(), label


def test_replay_cli_builds_manifest_and_is_reproducible(tmp_path):
    script = _script()
    raw = tmp_path / "raw"
    _write_raw(raw, SYNTHETIC_PAGES)
    assert script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "a")]) == 0
    assert script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "b")]) == 0
    a = json.loads((tmp_path / "a" / "inventory.json").read_text())
    b = json.loads((tmp_path / "b" / "inventory.json").read_text())
    assert a == b
    manifest = json.loads((tmp_path / "a" / "manifest.json").read_text())
    assert manifest["inventory_sha256"] == content_hash(a)
    assert manifest["counts"]["completeness_relative_to_service"].startswith("matches")
    assert manifest["acquisition"]["service_count_status"] == "ok"
    assert len(manifest["acquisition"]["receipt_sha256"]) == 64
    assert manifest["layer_schema"]["objectIdField"] == "objectid"
    assert manifest["layer_schema"]["per_record_date_fields"] == "none declared by the layer"
    # Contract field names (CONTRACTS.md SiteBundle rights); unknown is not approval.
    rights = manifest["rights"]
    for purpose in ("local_use", "team_share", "public_display", "export"):
        assert rights[f"{purpose}_status"] == "unknown"
        assert purpose not in rights
    assert rights["licence_reference"].startswith("unresolved")
    statements = manifest["rights_detail"]["licence_statements"]
    assert ["Open Government Licence" in s["statement"] for s in statements] == [True, False]
    assert "INSPIRE End User Licence" in statements[1]["statement"]
    assert manifest["rights_detail"]["conflict"] == "unresolved"
    # The download approval is recorded apart from rights and says it is not a rights decision.
    assert manifest["acquisition_approval"]["reference"] == "role:operator"
    assert "not a rights decision" in manifest["acquisition_approval"]["scope"]
    assert not any("approv" in key for key in rights)
    # The three #69 decisions travel with every manifest (envelope 1a, rights 2a, 3a).
    decisions = manifest["recorded_decisions"]
    assert decisions["sample_envelope"].startswith("1a:")
    assert decisions["rights"].startswith("2a:") and decisions["featurelocation"].startswith("3a:")
    assert "delegation" in decisions["decided_by"]
    # This synthetic receipt's bbox is not the 1a envelope, so 1a is not claimed for it.
    assert decisions["sample_envelope_applies_to_this_acquisition"] is False
    assert not any("Park-interior coverage" in limit for limit in manifest["limitations"])
    assert "local_only" not in json.loads(
        (tmp_path / "a" / "review-sample.json").read_text()
    )["sample"]
    # Operator-local paths never reach the committable manifest (checked on parsed strings,
    # so Windows backslash escaping cannot hide a leak).
    assert not any(str(tmp_path) in s for s in _strings(manifest))
    assert "<raw-dir>" in manifest["command"] and "<output-dir>" in manifest["command"]
    # Fixed placeholders: not even a final directory name reaches the manifest.
    assert "<raw>" not in manifest["command"] and "<a>" not in manifest["command"]
    assert manifest["layer_schema"]["native_crs_check"].startswith("matches")
    sample = json.loads((tmp_path / "a" / "review-sample.json").read_text())
    assert all("featurelocation" not in f["attributes"] for f in sample["features"])
    with pytest.raises(SystemExit):  # outputs are never overwritten
        script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "a")])


def test_manifest_command_never_records_paths_in_any_spelling(tmp_path):
    script = _script()
    raw = tmp_path / "raw"
    _write_raw(raw, SYNTHETIC_PAGES)
    out = tmp_path / "eq"
    assert script.main(["replay", f"--raw-dir={raw}", f"--output-dir={out}"]) == 0
    manifest = json.loads((out / "manifest.json").read_text())
    assert not any(str(tmp_path) in s for s in _strings(manifest))
    assert manifest["command"][1:] == [
        "replay", "--raw-dir", "<raw-dir>", "--output-dir", "<output-dir>", "--sample-size", "25"
    ]
    # Prefix abbreviations are refused outright rather than recorded.
    with pytest.raises(SystemExit):
        script.main(["replay", "--raw", str(raw), "--output-dir", str(tmp_path / "abbr")])
    assert not (tmp_path / "abbr").exists()


def test_sample_keeps_only_allowlisted_attributes(tmp_path):
    script = _script()
    layer = copy.deepcopy(LAYER)
    layer["fields"].insert(3, {"name": "notes", "type": "esriFieldTypeString", "alias": "Notes"})
    pages = copy.deepcopy(SYNTHETIC_PAGES)
    pages[0]["features"][0]["attributes"]["notes"] = "synthetic free text"
    raw = tmp_path / "raw"
    _write_raw(raw, pages, layer=layer)
    script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "o")])
    sample = json.loads((tmp_path / "o" / "review-sample.json").read_text())
    for f in sample["features"]:
        assert set(f["attributes"]) <= {"sitename", "featuretypename"}
    assert sample["features"][0]["withheld_for_sample"] == ["featurelocation", "notes"]
    script.main(
        ["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "k"), "--keep-location-text"]
    )
    kept = json.loads((tmp_path / "k" / "local-only-sample-with-location-text.json").read_text())
    assert kept["features"][0]["attributes"]["featurelocation"] == "Outside 1"
    assert "notes" not in kept["features"][0]["attributes"]


@pytest.mark.parametrize(
    "declared",
    [
        {"wkid": 3857, "latestWkid": 3857},
        # Ben's review of #77 (1): contradictory native codes are refused, either order.
        {"wkid": 3857, "latestWkid": 27700},
        {"wkid": 27700, "latestWkid": 3857},
        {"wkid": "27700"},
    ],
)
def test_a_layer_whose_native_crs_is_not_bng_is_refused(tmp_path, declared):
    script = _script()
    layer = {**LAYER, "spatialReference": declared}
    raw = tmp_path / "raw"
    _write_raw(raw, SYNTHETIC_PAGES, layer=layer)
    with pytest.raises(SystemExit, match="not consistently EPSG:27700"):
        script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "o")])
    assert not (tmp_path / "o").exists()


def test_replay_reports_a_non_integer_count_honestly(tmp_path):
    """With paging, fetch continues past a count that is not an integer; replay reports it."""
    script = _script()
    raw = tmp_path / "raw"
    _write_raw(raw, SYNTHETIC_PAGES, count={"count": "3"})
    script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "out")])
    manifest = json.loads((tmp_path / "out" / "manifest.json").read_text())
    assert manifest["acquisition"]["service_count_status"] == "non_integer"
    assert manifest["counts"]["completeness_relative_to_service"].startswith("unknown")
    assert "not requested" not in manifest["counts"]["completeness_relative_to_service"]


def _rewrite_raw_file(raw: Path, acquisition: dict, name: str, value) -> None:
    """SYNTHETIC: replace one raw file and keep its receipt hash consistent."""
    body = json.dumps(value).encode()
    (raw / name).write_bytes(body)
    for record in acquisition["files"]:
        if record["file"] == name:
            record.update(sha256=hashlib.sha256(body).hexdigest(), bytes=len(body))
    (raw / "acquisition.json").write_text(json.dumps(acquisition))


def test_replay_refuses_runs_fetch_could_not_have_completed(tmp_path):
    """Ben's review of #77 (2) and (3), replay side: a receipt is accepted only if fetch could
    have produced it as a complete run."""
    script = _script()
    first, second = SYNTHETIC_PAGES[0]["features"], SYNTHETIC_PAGES[1]["features"]

    def refused(label, pages, match, tamper=None, **kwargs):
        raw = tmp_path / label / "raw"
        raw.parent.mkdir()
        acquisition = _write_raw(raw, pages, **kwargs)
        if tamper:
            tamper(raw, acquisition)
        with pytest.raises(SystemExit, match=match):
            script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / label / "o")])
        assert not (tmp_path / label / "o").exists(), label

    # Trailing page removed: page-0000 reported more records, so fetch requested page-0001.
    refused("truncated", [page(first, more=True)], "replay refused: the raw files", paging=True)
    # A file served with a non-200 status (fetch stops on any non-200 response).
    refused(
        "status-404", SYNTHETIC_PAGES, "not 200",
        tamper=lambda raw, a: (
            a["files"][2].update(http_status=404),
            (raw / "acquisition.json").write_text(json.dumps(a)),
        ),
    )
    # An error-body count (fetch stops there; no page could follow).
    refused("count-error", SYNTHETIC_PAGES, "service error body",
            count={"error": {"code": 400, "message": "synthetic"}})
    # Without paging: the count must be an integer no larger than max_features.
    refused("count-over-cap", [page(first + second)], "no larger than", paging=False,
            count={"count": 600})
    refused("count-not-int", [page(first + second)], "no larger than", paging=False,
            count={"count": "3"})
    # Non-finite maxRecordCount in the layer metadata is refused, not a traceback.
    refused(
        "inf-max-records", SYNTHETIC_PAGES, "unreadable paging settings",
        tamper=lambda raw, a: _rewrite_raw_file(
            raw, a, "layer.json",
            {**LAYER, "maxRecordCount": float("inf"),
             "advancedQueryCapabilities": {"supportsPagination": True}},
        ),
    )
    # An error body as layer metadata (fetch stops on an error body in any response).
    refused(
        "layer-error", SYNTHETIC_PAGES, "layer.json is a service error body",
        tamper=lambda raw, a: _rewrite_raw_file(
            raw, a, "layer.json",
            {**LAYER, "maxRecordCount": 2, "advancedQueryCapabilities": {"supportsPagination": True},
             "error": {"code": 500, "message": "synthetic"}},
        ),
    )
    # With paging, a page holding more records than requested (fetch refuses it).
    third = [feature(3, 430020.0, 380020.0), feature(4, 430030.0, 380030.0),
             feature(5, 430040.0, 380040.0)]
    refused("page-over-size", [page(first, more=True), page(third)], "for a request of 2",
            paging=True)


def test_a_page_without_a_features_list_is_refused_cleanly(tmp_path):
    """The identity check counts it as no records; the build then refuses it by name."""
    script = _script()
    raw = tmp_path / "raw"
    _write_raw(raw, [{"geometryType": "esriGeometryPoint", "features": 5, "spatialReference": BNG}])
    with pytest.raises(SystemExit, match="inventory refused"):
        script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "o")])
    assert not (tmp_path / "o").exists()


@pytest.mark.parametrize(
    "sr", [{"wkid": 27700}, {"wkid": 27700, "latestWkid": None}, {"latestWkid": 27700}]
)
def test_consistent_crs_declarations_are_accepted(sr):
    built = build([page([feature(1, 430000.0, 380000.0)], sr=sr)])
    assert built["inventory"]["source_crs"] == "EPSG:27700"


def test_native_crs_uses_data_declarations_and_only_records_the_extent(tmp_path):
    script = _script()
    # A stored bounding box in another CRS does not decide (it is recorded, not checked).
    extent = {"xmin": 0, "ymin": 0, "xmax": 1, "ymax": 1, "spatialReference": {"wkid": 3857}}
    raw = tmp_path / "ok" / "raw"
    raw.parent.mkdir()
    _write_raw(raw, SYNTHETIC_PAGES, layer={**LAYER, "extent": extent})
    assert script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "ok" / "o")]) == 0
    manifest = json.loads((tmp_path / "ok" / "o" / "manifest.json").read_text())
    assert manifest["layer_schema"]["extent_spatialReference"] == {"wkid": 3857}
    assert manifest["layer_schema"]["native_crs_check"].startswith("matches")
    # A storage CRS (sourceSpatialReference) that disagrees is refused.
    raw = tmp_path / "src" / "raw"
    raw.parent.mkdir()
    _write_raw(raw, SYNTHETIC_PAGES, layer={**LAYER, "sourceSpatialReference": {"wkid": 3857}})
    with pytest.raises(SystemExit, match="not consistently EPSG:27700"):
        script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "src" / "o")])
    # A layer whose only declaration is latestWkid 27700 (wkid null) is accepted.
    raw = tmp_path / "latest" / "raw"
    raw.parent.mkdir()
    _write_raw(raw, SYNTHETIC_PAGES,
               layer={**LAYER, "spatialReference": {"wkid": None, "latestWkid": 27700}})
    assert script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "latest" / "o")]) == 0


def test_fetch_refuses_a_page_larger_than_requested(tmp_path, monkeypatch):
    """With paging, a server that ignores resultRecordCount cannot push past the cap."""
    script = _script()
    layer = {**LAYER, "maxRecordCount": 2, "advancedQueryCapabilities": {"supportsPagination": True}}
    third = [feature(3, 430020.0, 380020.0), feature(4, 430030.0, 380030.0),
             feature(5, 430040.0, 380040.0)]

    def opener(request):
        url = request.full_url
        if "returnCountOnly" in url:
            value = {"count": 3}
        elif "/query" in url:
            value = page(third, more=True)
        else:
            value = layer
        return _FakeResponse(value, url)

    monkeypatch.setattr(script, "_open", opener)
    raw, out = tmp_path / "raw", tmp_path / "out"
    with pytest.raises(SystemExit, match="returned 3 features for a request of 2"):
        script.main(
            ["fetch", "--bbox-27700", "433700,387100,434500,387700", "--acquisition-approval-ref",
             "role:operator", "--raw-dir", str(raw), "--output-dir", str(out)]
        )
    assert json.loads((raw / "acquisition.json").read_text())["status"] == "failed"
    assert not out.exists()


def test_a_multi_page_fetch_replays_through_the_identity_check(tmp_path, monkeypatch):
    """fetch's own paging loop and the replay rebuild must agree page by page (not only via
    the test helper, which uses the replay builder)."""
    script = _script()
    first, second = SYNTHETIC_PAGES[0]["features"], SYNTHETIC_PAGES[1]["features"]
    layer = {**LAYER, "maxRecordCount": 2, "advancedQueryCapabilities": {"supportsPagination": True}}
    requested = []

    def opener(request):
        url = request.full_url
        requested.append(url)
        if "returnCountOnly" in url:
            value = {"count": 3}
        elif "resultOffset=0" in url:
            value = page(first, more=True)
        elif "resultOffset=2" in url:
            value = page(second)
        elif "/query" in url:
            raise AssertionError(f"unexpected page request {url}")
        else:
            value = layer
        return _FakeResponse(value, url)

    monkeypatch.setattr(script, "_open", opener)
    raw, out = tmp_path / "raw", tmp_path / "out"
    assert script.main(
        ["fetch", "--bbox-27700", "433700,387100,434500,387700", "--acquisition-approval-ref",
         "role:operator", "--raw-dir", str(raw), "--output-dir", str(out)]
    ) == 0
    files = json.loads((raw / "acquisition.json").read_text())["files"]
    assert [f["file"] for f in files] == ["layer.json", "count.json", "page-0000.json", "page-0001.json"]
    assert sum("resultOffset" in u for u in requested) == 2
    # The same raw directory replays: fetch's recorded URLs pass the identity check.
    assert script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "again")]) == 0


def test_replay_refuses_changed_bytes_without_leaving_an_output_dir(tmp_path):
    script = _script()
    raw = tmp_path / "raw"
    _write_raw(raw, SYNTHETIC_PAGES)
    # Still valid, buildable JSON with one coordinate changed: only the SHA-256 check can
    # catch it.
    changed = copy.deepcopy(SYNTHETIC_PAGES[0])
    changed["features"][0]["geometry"]["x"] += 1.0
    (raw / "page-0000.json").write_text(json.dumps(changed))
    with pytest.raises(SystemExit, match="SHA-256"):
        script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "out")])
    assert not (tmp_path / "out").exists()  # a corrected retry can reuse the same path


def test_replay_refuses_receipts_it_cannot_account_for(tmp_path):
    script = _script()
    cases = {
        "incomplete": dict(status="failed"),
        "bad-name": dict(extra_files=[("../escape.json", {})]),
    }
    for label, kwargs in cases.items():
        raw = tmp_path / label / "raw"
        raw.parent.mkdir()
        try:
            _write_raw(raw, SYNTHETIC_PAGES, **kwargs)
        except OSError:
            continue  # the platform refused to create the escaping file; nothing to replay
        with pytest.raises(SystemExit):
            script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / label / "o")])
    # A page the receipt does not list, and a gap in page numbering, are both refused.
    raw = tmp_path / "unlisted" / "raw"
    raw.parent.mkdir()
    _write_raw(raw, SYNTHETIC_PAGES)
    (raw / "page-0002.json").write_text(json.dumps(SYNTHETIC_PAGES[1]))
    with pytest.raises(SystemExit):
        script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "unlisted" / "o")])
    raw = tmp_path / "gap" / "raw"
    raw.parent.mkdir()
    acquisition = _write_raw(raw, SYNTHETIC_PAGES)
    (raw / "page-0001.json").rename(raw / "page-0003.json")
    for record in acquisition["files"]:
        if record["file"] == "page-0001.json":
            record["file"] = "page-0003.json"
    (raw / "acquisition.json").write_text(json.dumps(acquisition))
    with pytest.raises(SystemExit):
        script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "gap" / "o")])
    raw = tmp_path / "noreceipt" / "raw"
    raw.parent.mkdir()
    _write_raw(raw, SYNTHETIC_PAGES)
    (raw / "acquisition.json").unlink()
    with pytest.raises(SystemExit):
        script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "noreceipt" / "o")])


def test_requests_are_limited_to_the_fixed_publisher_layer():
    script = _script()
    assert script.check_url(script.LAYER_URL + "?f=json")
    assert script.check_url(script.LAYER_URL + "/query?where=1%3D1&f=json")
    for url in (
        "http://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/INSPIRE/FeatureServer/14",
        "https://example.com/server/rest/services/AGOL/INSPIRE/FeatureServer/14/query",
        script.LAYER_URL.replace("/14", "/15") + "/query",
        "https://user:pw@sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/INSPIRE/FeatureServer/14",
    ):
        with pytest.raises(SystemExit):
            script.check_url(url)


def test_bbox_must_be_a_bounded_bng_envelope():
    script = _script()
    import argparse

    for bad in (
        "1,2,3",
        "1,2,1,3",
        "nan,0,1,1",
        "400000,380000,410000,390000",  # 100 km2: not bounded
        "-1.50,53.37,-1.47,53.39",  # WGS84 lon/lat pasted as BNG
        "433700,387100,433705,387700",  # under the minimum extent
    ):
        with pytest.raises(argparse.ArgumentTypeError):
            script.parse_bbox(bad)
    assert script.parse_bbox("433700,387100,434500,387700") == (433700.0, 387100.0, 434500.0, 387700.0)


def test_fetch_requires_approval_and_keeps_raw_and_outputs_outside_the_repo(tmp_path):
    script = _script()
    box = "433700,387100,434500,387700"
    with pytest.raises(SystemExit):  # the download must be approved by someone, explicitly
        script.main(
            ["fetch", "--bbox-27700", box, "--raw-dir", str(tmp_path / "r"),
             "--output-dir", str(tmp_path / "o")]
        )
    inside = script.REPO / "raw-should-not-be-here"
    with pytest.raises(SystemExit, match="outside every git working tree"):
        script.main(
            ["fetch", "--bbox-27700", box, "--acquisition-approval-ref", "role:operator",
             "--raw-dir", str(inside), "--output-dir", str(tmp_path / "o")]
        )
    assert not inside.exists() and not (tmp_path / "r").exists()
    # A valid raw dir, so the refusal below can only come from the output-location guard.
    raw = tmp_path / "raw"
    _write_raw(raw, SYNTHETIC_PAGES)
    out = script.REPO / "docs" / "site-audit" / "source-inventory" / "out"
    with pytest.raises(SystemExit, match="outside every git working tree"):
        script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(out)])
    assert not out.exists()
    # Any other checkout or worktree (marked by a .git dir or file) is refused too.
    other = tmp_path / "other-checkout"
    other.mkdir()
    (other / ".git").write_text("gitdir: synthetic\n")
    with pytest.raises(SystemExit, match="outside every git working tree"):
        script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(other / "out")])
    assert not (other / "out").exists()


def test_raw_and_output_directories_must_be_disjoint_before_any_download(tmp_path):
    script = _script()
    box = "433700,387100,434500,387700"
    for raw, out in (
        (tmp_path / "same", tmp_path / "same"),
        (tmp_path / "raw", tmp_path / "raw" / "out"),
        (tmp_path / "out2" / "raw", tmp_path / "out2"),
    ):
        with pytest.raises(SystemExit, match="non-nested"):
            script.main(
                ["fetch", "--bbox-27700", box, "--acquisition-approval-ref", "role:operator",
                 "--raw-dir", str(raw), "--output-dir", str(out)]
            )
        assert not raw.exists()


def test_redirects_are_refused_not_followed():
    script = _script()
    request = urllib.request.Request(script.LAYER_URL + "?f=json")
    with pytest.raises(urllib.error.HTTPError, match="redirect refused"):
        script._RefuseRedirects().redirect_request(
            request, io.BytesIO(b""), 302, "Found", {}, "http://example.invalid/elsewhere"
        )


class _FakeResponse:
    """SYNTHETIC stand-in for an HTTP response; no network is involved."""

    def __init__(self, value, final_url):
        self._body, self.status, self._url = json.dumps(value).encode(), 200, final_url

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._body

    def geturl(self):
        return self._url


def _fake_publisher(final_url=None, count=None, requests=None):
    """Serve the SYNTHETIC layer, count and one page by request URL."""
    single_page = page(SYNTHETIC_PAGES[0]["features"] + SYNTHETIC_PAGES[1]["features"])
    count = {"count": 3} if count is None else count

    def opener(request):
        url = request.full_url
        if requests is not None:
            requests.append(url)
        if "returnCountOnly" in url:
            value = count
        elif "/query" in url:
            value = single_page
        else:
            value = LAYER
        return _FakeResponse(value, final_url or url)

    return opener


def test_fetch_records_each_final_url_and_builds_offline(tmp_path, monkeypatch):
    script = _script()
    monkeypatch.setattr(script, "_open", _fake_publisher())
    raw, out = tmp_path / "raw", tmp_path / "out"
    assert script.main(
        ["fetch", "--bbox-27700", "433700,387100,434500,387700", "--acquisition-approval-ref",
         "#69", "--raw-dir", str(raw), "--output-dir", str(out)]
    ) == 0
    acquisition = json.loads((raw / "acquisition.json").read_text())
    assert acquisition["status"] == "complete"
    assert [f["file"] for f in acquisition["files"]] == ["layer.json", "count.json", "page-0000.json"]
    assert all(f["final_url"] == f["url"] for f in acquisition["files"])
    assert all(script.check_url(f["url"]) for f in acquisition["files"])
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["counts"]["features_kept"] == 3
    assert manifest["acquisition_approval"]["reference"] == "#69"
    assert manifest["command"][manifest["command"].index("--acquisition-approval-ref") + 1] == "#69"
    # The decision-1a envelope was fetched, so the decision and its coverage caveat apply.
    assert manifest["recorded_decisions"]["sample_envelope_applies_to_this_acquisition"] is True
    assert any("Park-interior coverage" in limit for limit in manifest["limitations"])


def test_non_paging_single_query_is_refused_if_it_exceeds_the_cap(tmp_path, monkeypatch):
    """L2: the layer can change between the count and the single query; the page is checked."""
    script = _script()
    monkeypatch.setattr(script, "_open", _fake_publisher(count={"count": 2}))
    raw, out = tmp_path / "raw", tmp_path / "out"
    with pytest.raises(SystemExit, match="single query returned 4 features"):
        script.main(
            ["fetch", "--bbox-27700", "433700,387100,434500,387700", "--max-features", "2",
             "--acquisition-approval-ref", "role:operator",
             "--raw-dir", str(raw), "--output-dir", str(out)]
        )
    assert json.loads((raw / "acquisition.json").read_text())["status"] == "failed"
    assert not out.exists()


def test_fetch_refuses_a_response_from_another_url_and_keeps_the_receipt(tmp_path, monkeypatch):
    script = _script()
    monkeypatch.setattr(script, "_open", _fake_publisher("http://example.invalid/moved"))
    raw, out = tmp_path / "raw", tmp_path / "out"
    with pytest.raises(SystemExit, match="outside the fixed publisher layer"):
        script.main(
            ["fetch", "--bbox-27700", "433700,387100,434500,387700", "--acquisition-approval-ref",
             "role:operator", "--raw-dir", str(raw), "--output-dir", str(out)]
        )
    acquisition = json.loads((raw / "acquisition.json").read_text())
    assert acquisition["status"] == "failed"
    assert acquisition["files"][0]["final_url"] == "http://example.invalid/moved"
    assert not out.exists()


@pytest.mark.parametrize(
    "count,match",
    [({"count": 3}, "more than --max-features 2"), ({"count": "3"}, "not an integer")],
)
def test_non_paging_layer_honours_max_features_before_any_page(tmp_path, monkeypatch, count, match):
    """L2: a layer without paging gets one uncapped query, so the cap is enforced from the
    service count first, and nothing is downloaded when it cannot be honoured."""
    script = _script()
    requests = []
    monkeypatch.setattr(script, "_open", _fake_publisher(count=count, requests=requests))
    raw, out = tmp_path / "raw", tmp_path / "out"
    with pytest.raises(SystemExit, match=match):
        script.main(
            ["fetch", "--bbox-27700", "433700,387100,434500,387700", "--max-features", "2",
             "--acquisition-approval-ref", "role:operator",
             "--raw-dir", str(raw), "--output-dir", str(out)]
        )
    acquisition = json.loads((raw / "acquisition.json").read_text())
    assert acquisition["status"] == "failed"
    assert [f["file"] for f in acquisition["files"]] == ["layer.json", "count.json"]
    assert not (raw / "page-0000.json").exists() and not out.exists()
    assert not any("returnCountOnly" not in u and "/query" in u for u in requests)


def test_approval_takes_a_role_or_reference_never_a_name(tmp_path):
    """N1: the approval lands in a committable manifest in a public repository."""
    script = _script()
    import argparse

    for good in (
        "role:data-owner",
        "#69",
        "#69#issuecomment-6856478760",
        "https://github.com/Pimentellll/sheffield-tree-planner/issues/69#issuecomment-1",
        "https://github.com/Pimentellll/sheffield-tree-planner/pull/77",
    ):
        assert script.parse_approval_ref(good) == good
    for bad in ("Synthetic Person", "synthetic", "role:", "role:Has Spaces", "#69 by someone",
                "https://example.com/#69", "", "role:synthetic-person", "#69\nx"):
        with pytest.raises(argparse.ArgumentTypeError):
            script.parse_approval_ref(bad)
    with pytest.raises(SystemExit):  # argparse rejects it before anything is created
        script.main(
            ["fetch", "--bbox-27700", "433700,387100,434500,387700", "--acquisition-approval-ref",
             "Synthetic Person", "--raw-dir", str(tmp_path / "r"), "--output-dir", str(tmp_path / "o")]
        )
    assert not (tmp_path / "r").exists()
    # A receipt carrying free text (or the old field) is refused on replay, before any output.
    raw = tmp_path / "raw"
    acquisition = _write_raw(raw, SYNTHETIC_PAGES)
    acquisition.pop("acquisition_approval_ref")
    acquisition["acquisition_approved_by"] = "Synthetic Person"
    (raw / "acquisition.json").write_text(json.dumps(acquisition))
    with pytest.raises(SystemExit, match="acquisition_approval_ref"):
        script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "out")])
    assert not (tmp_path / "out").exists()
    # A non-canonical reference (trailing newline) is refused on replay too.
    acquisition["acquisition_approval_ref"] = "#69\n"
    (raw / "acquisition.json").write_text(json.dumps(acquisition))
    with pytest.raises(SystemExit, match="acquisition_approval_ref"):
        script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "out")])
    # A valid reference beside an old free-text field replays, but only allowlisted receipt
    # keys reach the committable manifest.
    acquisition["acquisition_approval_ref"] = "#69"
    acquisition["files"][0]["note"] = "Synthetic Person"
    (raw / "acquisition.json").write_text(json.dumps(acquisition))
    assert script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "ok")]) == 0
    manifest = json.loads((tmp_path / "ok" / "manifest.json").read_text())
    assert not any("Synthetic Person" in s for s in _strings(manifest))
    assert "acquisition_approved_by" not in manifest["acquisition"]


def test_location_text_sample_is_marked_local_only(tmp_path):
    """Decision 3a: featurelocation stays in local outputs only."""
    script = _script()
    raw = tmp_path / "raw"
    _write_raw(raw, SYNTHETIC_PAGES)
    script.main(
        ["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "k"), "--keep-location-text"]
    )
    # Written under its own name, never the reviewable sample's.
    assert not (tmp_path / "k" / "review-sample.json").exists()
    sample = json.loads((tmp_path / "k" / "local-only-sample-with-location-text.json").read_text())
    assert "decision 3a" in sample["sample"]["local_only"]
    assert sample["features"][0]["attributes"]["featurelocation"] == "Outside 1"


def test_a_negative_service_count_is_refused(tmp_path, monkeypatch):
    script = _script()
    monkeypatch.setattr(script, "_open", _fake_publisher(count={"count": -1}))
    raw, out = tmp_path / "raw", tmp_path / "out"
    with pytest.raises(SystemExit, match="negative count"):
        script.main(
            ["fetch", "--bbox-27700", "433700,387100,434500,387700",
             "--acquisition-approval-ref", "role:operator",
             "--raw-dir", str(raw), "--output-dir", str(out)]
        )
    acquisition = json.loads((raw / "acquisition.json").read_text())
    assert [f["file"] for f in acquisition["files"]] == ["layer.json", "count.json"]
    assert acquisition["status"] == "failed" and not out.exists()
    # A receipt with a negative count and pages is one fetch could never have completed,
    # so replay refuses it (the count is never used either way).
    raw2 = tmp_path / "raw2"
    _write_raw(raw2, SYNTHETIC_PAGES, count={"count": -1})
    with pytest.raises(SystemExit, match="replay refused: the service count is negative"):
        script.main(["replay", "--raw-dir", str(raw2), "--output-dir", str(tmp_path / "o2")])
    assert not (tmp_path / "o2").exists()


_LAYER = "https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/INSPIRE/FeatureServer/14"


@pytest.mark.parametrize(
    "key,value",
    [
        ("layer_url", "https://example.invalid/layer"),
        ("max_features", 0),
        ("started_at_utc", "Synthetic Person"),
        ("bbox_27700", [-1.5, 53.37, -1.47, 53.39]),
        ("bbox_27700", [10**400, 387100, 434500, 387700]),  # int too large for a float
        ("files[0].url", _LAYER + "?f=json&approved_by=Synthetic+Person"),  # free text in query
        ("files[0].final_url", _LAYER + "/query?f=json&where=Synthetic+Person"),
        ("supports_pagination", "yes"),
        ("files[0].retrieved_at_utc", "Synthetic Person"),
        ("files[0].url", "http://example.invalid/elsewhere"),
    ],
)
def test_replay_refuses_malformed_receipt_values(tmp_path, key, value):
    """Allowlisted receipt values reach the committable manifest, so each must have its
    expected form; nothing is written otherwise."""
    script = _script()
    raw = tmp_path / "raw"
    acquisition = _write_raw(raw, SYNTHETIC_PAGES)
    if key.startswith("files[0]."):
        acquisition["files"][0][key.split(".", 1)[1]] = value
    else:
        acquisition[key] = value
    (raw / "acquisition.json").write_text(json.dumps(acquisition))
    with pytest.raises(SystemExit):
        script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "out")])
    assert not (tmp_path / "out").exists()


def test_receipt_urls_from_fetch_pass_the_query_check(tmp_path, monkeypatch):
    """The query check accepts exactly what fetch() sends (paging and count included)."""
    script = _script()
    layer = {**LAYER, "advancedQueryCapabilities": {"supportsPagination": True}}

    def opener(request):
        url = request.full_url
        if "returnCountOnly" in url:
            value = {"count": 3}
        elif "/query" in url:
            value = page(SYNTHETIC_PAGES[0]["features"] + SYNTHETIC_PAGES[1]["features"])
        else:
            value = layer
        return _FakeResponse(value, url)

    monkeypatch.setattr(script, "_open", opener)
    raw, out = tmp_path / "raw", tmp_path / "out"
    assert script.main(
        ["fetch", "--bbox-27700", "433700,387100,434500,387700", "--acquisition-approval-ref",
         "role:operator", "--raw-dir", str(raw), "--output-dir", str(out)]
    ) == 0
    urls = [f["url"] for f in json.loads((raw / "acquisition.json").read_text())["files"]]
    assert any("orderByFields" in u and "resultOffset" in u for u in urls)
    assert all(script._query_is_expected(u) for u in urls)


def test_approval_reference_digits_are_ascii_only():
    script = _script()
    import argparse

    six, nine, one = chr(0x0666), chr(0x0669), chr(0x0661)  # Arabic-Indic digits
    for bad in ("#" + six + nine, "#6" + nine, "#69#issuecomment-" + one):
        with pytest.raises(argparse.ArgumentTypeError):
            script.parse_approval_ref(bad)
