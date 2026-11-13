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
import json
from pathlib import Path

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
    for bad in (float("nan"), float("inf"), float("-inf")):
        built = build([page([feature(1, bad, 1.0), feature(2, 1.0, 1.0)])])
        assert [f["source_record_id"] for f in built["inventory"]["features"]] == [2]


@pytest.mark.parametrize(
    "sr",
    [None, {}, {"wkid": "27700"}, {"wkid": 3857}, {"wkt": "PROJCS[...]"}],
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


def _write_raw(raw_dir: Path, pages, count=None, status="complete", extra_files=()):
    """SYNTHETIC raw directory in the exact layout `fetch` writes (receipt + hashed files)."""
    raw_dir.mkdir()
    count = {"count": 3} if count is None else count
    files = []
    entries = [("layer.json", LAYER), ("count.json", count)]
    entries += [(f"page-{i:04d}.json", p) for i, p in enumerate(pages)]
    for name, value in [*entries, *extra_files]:
        body = json.dumps(value).encode()
        (raw_dir / name).write_bytes(body)
        files.append({"file": name, "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)})
    acquisition = {
        "status": status,
        "max_features": 500,
        "local_use_approved_by": "synthetic test fixture",
        "files": files,
    }
    (raw_dir / "acquisition.json").write_text(json.dumps(acquisition))
    return acquisition


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
    assert manifest["rights"]["public_display"] == "unknown"  # unknown is not approval
    # Operator-local paths never reach the committable manifest.
    assert str(tmp_path) not in json.dumps(manifest)
    assert "<raw>" in manifest["command"] and "<a>" in manifest["command"]
    sample = json.loads((tmp_path / "a" / "redistributable-sample.json").read_text())
    assert all("featurelocation" not in f["attributes"] for f in sample["features"])
    with pytest.raises(SystemExit):  # outputs are never overwritten
        script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "a")])


@pytest.mark.parametrize(
    "count,status",
    [({"error": {"code": 400, "message": "synthetic"}}, "service_error"), ({"count": "3"}, "non_integer")],
)
def test_replay_reports_a_failed_count_honestly(tmp_path, count, status):
    script = _script()
    raw = tmp_path / "raw"
    _write_raw(raw, SYNTHETIC_PAGES, count=count)
    script.main(["replay", "--raw-dir", str(raw), "--output-dir", str(tmp_path / "out")])
    manifest = json.loads((tmp_path / "out" / "manifest.json").read_text())
    assert manifest["acquisition"]["service_count_status"] == status
    assert manifest["counts"]["completeness_relative_to_service"].startswith("unknown")
    assert "not requested" not in manifest["counts"]["completeness_relative_to_service"]


def test_replay_refuses_changed_bytes_without_leaving_an_output_dir(tmp_path):
    script = _script()
    raw = tmp_path / "raw"
    _write_raw(raw, SYNTHETIC_PAGES)
    (raw / "page-0000.json").write_text("{}")
    with pytest.raises(SystemExit):
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
    with pytest.raises(SystemExit):  # local use must be approved by someone, explicitly
        script.main(
            ["fetch", "--bbox-27700", box, "--raw-dir", str(tmp_path / "r"),
             "--output-dir", str(tmp_path / "o")]
        )
    inside = script.REPO / "raw-should-not-be-here"
    with pytest.raises(SystemExit):
        script.main(
            ["fetch", "--bbox-27700", box, "--local-use-approved-by", "synthetic test",
             "--raw-dir", str(inside), "--output-dir", str(tmp_path / "o")]
        )
    assert not inside.exists() and not (tmp_path / "r").exists()
    with pytest.raises(SystemExit):  # full outputs (with frontage text) never inside the repo
        script.main(
            ["replay", "--raw-dir", str(tmp_path / "r"),
             "--output-dir", str(script.REPO / "docs" / "site-audit" / "source-inventory" / "out")]
        )
    assert not (script.REPO / "docs" / "site-audit" / "source-inventory" / "out").exists()
