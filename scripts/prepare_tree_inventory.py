"""Operator-run preparation of the Sheffield recorded street-tree inventory (#69, GEO3D-01 / I1).

Not an agent tool: it contacts one fixed publisher endpoint, only when an operator runs it.
It never touches accepted scenarios, runtime services or model state.

  fetch   bounded acquisition (EPSG:27700 envelope) -> raw bytes + SHA-256 receipts in a fresh
          --raw-dir OUTSIDE the repository, then the inventory/manifest in a fresh --output-dir
          (also outside the repository). Requires --local-use-approved-by: rights are recorded
          as unknown until a person approves, and downloading is itself local use.
  replay  rebuild the inventory/manifest from an existing --raw-dir after re-checking every
          raw file hash (same-source replay must give the same inventory_sha256)

Example (run only in the approved environment):

  python scripts/prepare_tree_inventory.py fetch \
      --bbox-27700 433700,387100,434500,387700 --max-features 500 \
      --local-use-approved-by "<who/where approved>" \
      --raw-dir /path/outside/repo/raw-street-trees-001 --output-dir /path/out-001
  python scripts/prepare_tree_inventory.py replay \
      --raw-dir /path/outside/repo/raw-street-trees-001 --output-dir /path/out-002

The redistributable sample withholds the free-text ``featurelocation`` field (house-number
frontage text) unless --keep-location-text is given; raw downloads never go into git.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

from tree_planner.site.source_inventory import (
    InventoryError,
    build_inventory,
    redistributable_sample,
)

LAYER_URL = (
    "https://sheffieldcitycouncil.cloud.esriuk.com/server/rest/services/AGOL/INSPIRE/"
    "FeatureServer/14"
)
SOURCE = {
    "source_key": "sheffield-street-trees",
    "title": "Street Trees",
    "publisher": "Sheffield City Council",
    "catalogue_url": "https://www.data.gov.uk/dataset/957a85f3-d56b-4aed-9f29-5f8fe1363e57/street-trees",
    "layer_url": LAYER_URL,
}
RIGHTS = {
    "publisher_stated_licence": {
        "name": "UK Open Government Licence (OGL) v3.0",
        "url": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        "evidence": "CKAN package_show https://ckan.publishing.service.gov.uk/api/action/"
        "package_show?id=957a85f3-d56b-4aed-9f29-5f8fe1363e57 reported license_id 'uk-ogl' "
        "(observed 2026-11-13, metadata_modified 2026-01-07); not re-fetched by this script",
    },
    "proposed_attribution": "Contains public sector information licensed under the Open "
    "Government Licence v3.0. Source: Sheffield City Council, Street Trees.",
    "local_use": "unknown",
    "team_share": "unknown",
    "public_display": "unknown",
    "export": "unknown",
    "decision_needed": "A person confirms that the publisher-stated OGL v3.0 covers this layer "
    "for each purpose (the council notes some of its data carries other terms). Until then "
    "each purpose stays unknown, which is not approval.",
}
MAX_FEATURES_LIMIT = 5000
MAX_ENVELOPE_KM2 = 25.0
MIN_EXTENT_M = 10.0
BNG_BOUNDS = (0.0, 0.0, 700000.0, 1300000.0)  # EPSG:27700 projected bounds, metres
RAW_NAME = re.compile(r"^(layer|count|page-\d{4})\.json$")
USER_AGENT = "canopy-tree-inventory-prep/1"
REPO = Path(__file__).resolve().parents[1]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_url(url: str) -> str:
    """Only HTTPS requests to the fixed publisher layer are allowed."""
    parsed = urllib.parse.urlsplit(url)
    layer = urllib.parse.urlsplit(LAYER_URL)
    if (
        parsed.scheme != "https"
        or parsed.netloc != layer.netloc
        or not (parsed.path == layer.path or parsed.path == layer.path + "/query")
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise SystemExit(f"refusing request outside the fixed publisher layer: {url}")
    return url


def parse_bbox(text: str) -> tuple[float, float, float, float]:
    try:
        values = tuple(float(v) for v in text.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("bbox must be four numbers") from exc
    if len(values) != 4 or not all(math.isfinite(v) for v in values):
        raise argparse.ArgumentTypeError("bbox must be four finite numbers")
    xmin, ymin, xmax, ymax = values
    if not (xmin < xmax and ymin < ymax):
        raise argparse.ArgumentTypeError("bbox must be xmin,ymin,xmax,ymax with min < max")
    bx0, by0, bx1, by1 = BNG_BOUNDS
    if not (bx0 <= xmin and xmax <= bx1 and by0 <= ymin and ymax <= by1) or (
        xmax - xmin < MIN_EXTENT_M or ymax - ymin < MIN_EXTENT_M
    ):
        raise argparse.ArgumentTypeError(
            "bbox does not look like EPSG:27700 metres (eastings 0-700000, northings "
            f"0-1300000, extent >= {MIN_EXTENT_M:g} m); WGS84 lon/lat is not accepted"
        )
    if (xmax - xmin) * (ymax - ymin) / 1e6 > MAX_ENVELOPE_KM2:
        raise argparse.ArgumentTypeError(f"bbox larger than {MAX_ENVELOPE_KM2} km2; keep it bounded")
    return values


def _outside_repository(path: Path, flag: str) -> None:
    if path.resolve().is_relative_to(REPO):
        raise SystemExit(f"{flag} must be outside the repository (raw and full outputs stay out of git)")


def _fresh_dir(path: Path, flag: str) -> Path:
    path = path.resolve()
    if path.exists():
        raise SystemExit(f"{flag} {path} already exists; use a fresh path")
    path.mkdir(parents=True)
    return path


def _query_url(params: dict) -> str:
    return LAYER_URL + "/query?" + urllib.parse.urlencode(params)


def fetch(bbox, max_features: int, raw_dir: Path, approval: str) -> None:
    """Acquire layer metadata, the service count and pages; always leave a receipt."""
    acquisition = {
        "layer_url": LAYER_URL,
        "bbox_27700": list(bbox),
        "max_features": max_features,
        "local_use_approved_by": approval,
        "started_at_utc": _now(),
        "files": [],
        "status": "failed",
    }

    def get(name: str, url: str):
        """Fetch, save the exact bytes with a receipt, then parse (errors are recorded)."""
        check_url(url)
        meta = {"file": name, "url": url, "retrieved_at_utc": _now()}
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body, meta["http_status"] = response.read(), response.status
        except urllib.error.HTTPError as exc:
            body, meta["http_status"] = exc.read(), exc.code
        (raw_dir / name).write_bytes(body)
        meta.update(bytes=len(body), sha256=_sha256(body))
        acquisition["files"].append(meta)
        if meta["http_status"] != 200:
            raise SystemExit(f"{name}: HTTP {meta['http_status']} from the publisher")
        try:
            value = json.loads(body)
        except ValueError as exc:
            raise SystemExit(f"{name}: response is not JSON") from exc
        if isinstance(value, dict) and "error" in value:
            raise SystemExit(f"{name}: the service returned an error body")
        return value

    try:
        layer = get("layer.json", LAYER_URL + "?f=json")
        id_field = layer.get("objectIdField")
        if not isinstance(id_field, str) or not id_field:
            raise SystemExit("layer metadata declares no objectIdField")
        page_size = min(int(layer.get("maxRecordCount") or 1000), 1000)
        paging = bool((layer.get("advancedQueryCapabilities") or {}).get("supportsPagination"))
        acquisition.update(page_size=page_size, supports_pagination=paging)
        spatial = {
            "geometry": ",".join(repr(v) for v in bbox),
            "geometryType": "esriGeometryEnvelope",
            "inSR": "27700",
            "spatialRel": "esriSpatialRelIntersects",
            "where": "1=1",
        }
        get("count.json", _query_url({**spatial, "returnCountOnly": "true", "f": "json"}))
        common = {**spatial, "outFields": "*", "returnGeometry": "true", "outSR": "27700", "f": "json"}
        if not paging:
            # One query; the service's exceededTransferLimit reports any truncation.
            get("page-0000.json", _query_url(common))
        else:
            pages, offset = 0, 0
            while offset < max_features:
                size = min(page_size, max_features - offset)
                params = {
                    **common,
                    "orderByFields": f"{id_field} ASC",
                    "resultOffset": str(offset),
                    "resultRecordCount": str(size),
                }
                page = get(f"page-{pages:04d}.json", _query_url(params))
                pages += 1
                received = len(page.get("features") or [])
                offset += received
                if received < size or not page.get("exceededTransferLimit"):
                    break
        acquisition["status"] = "complete"
    except SystemExit as exc:
        acquisition["error"] = str(exc)
        raise
    except Exception as exc:  # network failures etc.: keep the receipt, then stop clearly
        acquisition["error"] = f"{type(exc).__name__}: {exc}"[:300]
        raise SystemExit(f"acquisition failed: {acquisition['error']}") from exc
    finally:
        acquisition["finished_at_utc"] = _now()
        (raw_dir / "acquisition.json").write_text(json.dumps(acquisition, indent=2) + "\n")


def load_raw(raw_dir: Path) -> tuple[dict, str, dict, dict, list[dict]]:
    """Read and verify raw files; refuse anything the receipt does not exactly account for."""
    receipt_path = raw_dir / "acquisition.json"
    if not receipt_path.is_file():
        raise SystemExit("raw directory has no acquisition.json receipt")
    receipt_bytes = receipt_path.read_bytes()
    acquisition = json.loads(receipt_bytes)
    if acquisition.get("status") != "complete":
        raise SystemExit(f"acquisition is not complete: {acquisition.get('error', 'unknown')}")
    root = raw_dir.resolve()
    values, names = {}, []
    for record in acquisition.get("files", []):
        name = record.get("file")
        if not isinstance(name, str) or not RAW_NAME.match(name):
            raise SystemExit(f"unexpected raw file name in receipt: {name!r}")
        path = (raw_dir / name).resolve()
        if not path.is_relative_to(root):
            raise SystemExit(f"raw file outside the raw directory: {name!r}")
        body = path.read_bytes()
        if _sha256(body) != record.get("sha256"):
            raise SystemExit(f"raw file {name} does not match its recorded SHA-256")
        values[name] = json.loads(body)
        names.append(name)
    on_disk = sorted(p.name for p in raw_dir.iterdir() if p.name != "acquisition.json")
    if sorted(names) != on_disk or len(set(names)) != len(names):
        raise SystemExit("raw directory files do not match the acquisition receipt")
    pages = sorted(n for n in names if n.startswith("page-"))
    if not pages or pages != [f"page-{i:04d}.json" for i in range(len(pages))]:
        raise SystemExit("raw pages are missing or not contiguous")
    if "layer.json" not in values or "count.json" not in values:
        raise SystemExit("raw directory lacks layer metadata or the count response")
    count = values["count.json"]
    return (
        acquisition,
        _sha256(receipt_bytes),
        values["layer.json"],
        count,
        [values[name] for name in pages],
    )


def _count(count_value) -> tuple[int | None, str]:
    if isinstance(count_value, dict) and "error" in count_value:
        return None, "service_error"
    if isinstance(count_value, dict) and type(count_value.get("count")) is int:
        return count_value["count"], "ok"
    return None, "non_integer"


def _redacted(command: list[str]) -> list[str]:
    """Keep substantive arguments; never record operator-local paths in a committable file."""
    out, hide = [], False
    for item in command:
        if hide:
            out.append(f"<{Path(item).name}>")
            hide = False
            continue
        out.append(item)
        hide = item in ("--raw-dir", "--output-dir")
    return out


def build_outputs(raw_dir: Path, output_dir: Path, sample_size: int, keep_location: bool, mode, command):
    acquisition, receipt_sha256, layer, count_value, pages = load_raw(raw_dir)
    fields = layer.get("fields") or []
    id_field = layer.get("objectIdField")
    attribute_fields = [
        f["name"] for f in fields if f.get("type") == "esriFieldTypeString" and f["name"] != id_field
    ]
    not_imported = [
        f["name"]
        for f in fields
        if f["name"] != id_field
        and f["name"] not in attribute_fields
        and f.get("type") != "esriFieldTypeGeometry"
    ]
    date_fields = [f["name"] for f in fields if f.get("type") == "esriFieldTypeDate"]
    service_count, count_status = _count(count_value)
    try:
        built = build_inventory(
            pages,
            source={**SOURCE, "source_layer_name": layer.get("name")},
            id_field=id_field,
            attribute_fields=attribute_fields,
            declared_fields=[f["name"] for f in fields],
            service_count=service_count,
            service_count_status=count_status,
            requested_limit=acquisition.get("max_features"),
        )
        drop = () if keep_location else ("featurelocation",)
        sample = redistributable_sample(built["inventory"], limit=sample_size, drop_attributes=drop)
    except InventoryError as exc:
        raise SystemExit(f"inventory refused: {exc}") from exc
    inventory, receipt = built["inventory"], built["receipt"]
    manifest = {
        "schema": "canopy-source-tree-inventory-manifest/1",
        "mode": mode,
        "built_at_utc": _now(),
        "command": ["scripts/prepare_tree_inventory.py", *_redacted(command)],
        "source": SOURCE,
        "rights": {
            **RIGHTS,
            "layer_copyright_text": layer.get("copyrightText"),
            "local_use_approved_by": acquisition.get("local_use_approved_by"),
        },
        "acquisition": {
            **{k: v for k, v in acquisition.items() if k != "files"},
            "receipt_sha256": receipt_sha256,
            "files": acquisition.get("files"),
            "service_count_status": count_status,
        },
        "layer_schema": {
            "name": layer.get("name"),
            "geometryType": layer.get("geometryType"),
            "spatialReference": layer.get("spatialReference"),
            "hasZ": layer.get("hasZ"),
            "objectIdField": id_field,
            # Snapshot identity: record IDs are only stable within this recorded snapshot.
            "serviceItemId": layer.get("serviceItemId"),
            "editingInfo": layer.get("editingInfo"),
            "layer_metadata_sha256": next(
                (f["sha256"] for f in acquisition.get("files", []) if f["file"] == "layer.json"),
                None,
            ),
            "maxRecordCount": layer.get("maxRecordCount"),
            "fields": fields,
            "declared_but_not_imported": not_imported,
            "per_record_date_fields": date_fields or "none declared by the layer",
        },
        "counts": receipt["counts"],
        "inventory_sha256": receipt["inventory_sha256"],
        "limitations": [
            "Recorded locations only: no crowns, heights, health, survival or planting "
            "permission are implied.",
            "Species values are the source's 'featuretypename' text as recorded; not verified.",
            "Coordinates stay in the source CRS; no ENU/WGS84 conversion has been verified here.",
            "Bounded envelope sample; not a citywide or complete inventory unless counts say so.",
        ],
    }
    # Everything was computed; only now create the (fresh) output directory.
    output_dir = _fresh_dir(output_dir, "--output-dir")
    for name, value in (
        ("inventory.json", inventory),
        ("receipt.json", receipt),
        ("manifest.json", manifest),
        ("redistributable-sample.json", sample),
    ):
        (output_dir / name).write_text(
            json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8"
        )
    return manifest, output_dir


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    fetch_p = sub.add_parser("fetch", help="bounded acquisition from the fixed publisher layer")
    fetch_p.add_argument("--bbox-27700", type=parse_bbox, required=True)
    fetch_p.add_argument("--max-features", type=int, default=500)
    fetch_p.add_argument(
        "--local-use-approved-by",
        required=True,
        help="who approved local use of this dataset, and where that approval is recorded",
    )
    replay_p = sub.add_parser("replay", help="rebuild outputs from a saved raw directory")
    for p in (fetch_p, replay_p):
        p.add_argument("--raw-dir", type=Path, required=True)
        p.add_argument("--output-dir", type=Path, required=True)
        p.add_argument("--sample-size", type=int, default=25)
        p.add_argument("--keep-location-text", action="store_true")
    command = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(command)
    if args.sample_size < 1:
        parser.error("--sample-size must be at least 1")
    _outside_repository(args.output_dir, "--output-dir")
    if args.output_dir.resolve().exists():
        parser.error(f"--output-dir {args.output_dir} already exists; use a fresh path")
    if args.mode == "fetch":
        if not 1 <= args.max_features <= MAX_FEATURES_LIMIT:
            parser.error(f"--max-features must be between 1 and {MAX_FEATURES_LIMIT}")
        if not args.local_use_approved_by.strip():
            parser.error("--local-use-approved-by must name the approval")
        _outside_repository(args.raw_dir, "--raw-dir")
        raw_dir = _fresh_dir(args.raw_dir, "--raw-dir")
        fetch(args.bbox_27700, args.max_features, raw_dir, args.local_use_approved_by.strip())
    else:
        raw_dir = args.raw_dir.resolve()
    manifest, output_dir = build_outputs(
        raw_dir, args.output_dir, args.sample_size, args.keep_location_text, args.mode, command
    )
    counts = manifest["counts"]
    print(
        f"{counts['features_kept']} features kept of {counts['features_received']} received; "
        f"service reported {counts['service_reported_count']}; "
        f"{counts['completeness_relative_to_service']}"
    )
    print(f"inventory_sha256 {manifest['inventory_sha256']}")
    print(f"outputs: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
