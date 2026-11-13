"""Operator-run preparation of the Sheffield recorded street-tree inventory (#69, GEO3D-01 / I1).

Not an agent tool: it contacts one fixed publisher endpoint, only when an operator runs it.
It never touches accepted scenarios, runtime services or model state.

  fetch   bounded acquisition (EPSG:27700 envelope) -> raw bytes + SHA-256 receipts in a fresh
          --raw-dir outside every git working tree, then the inventory/manifest in a separate
          fresh --output-dir (also outside every git working tree). Requires
          --acquisition-approval-ref: a listed role (role:<role>) or a reference to where the approval
          of this download is recorded (#<issue>[#issuecomment-<id>] or its GitHub URL), never
          a person's name, because the manifest is committable and the repository is public.
          It is not a rights decision, so every rights *_status stays unknown until a person
          decides. If the layer does not support paging, the service count must be an integer
          no larger than --max-features, or nothing is downloaded.
  replay  rebuild the inventory/manifest from an existing --raw-dir after re-checking every
          raw file hash (same-source replay must give the same inventory_sha256)

Example (run only in the approved environment):

  python scripts/prepare_tree_inventory.py fetch \
      --bbox-27700 433700,387100,434500,387700 --max-features 500 \
      --acquisition-approval-ref "#69#issuecomment-<id>" \
      --raw-dir /path/outside/repo/raw-street-trees-001 --output-dir /path/out-001
  python scripts/prepare_tree_inventory.py replay \
      --raw-dir /path/outside/repo/raw-street-trees-001 --output-dir /path/out-002

The review sample (``review-sample.json``) keeps only an allowlist of attributes
(``sitename``, ``featuretypename``). It is for review, not redistribution: it may be copied
into the repository only once ``public_display_status`` and ``export_status`` are both
recorded as permitted (today all rights are unknown, decision 2a). With
--keep-location-text the sample, which then also keeps the free-text ``featurelocation``
(house-number frontage text), is written as ``local-only-sample-with-location-text.json``
instead and is never committed (decision 3a). Raw downloads never go into git.
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
CKAN_URL = (
    "https://ckan.publishing.service.gov.uk/api/action/package_show?"
    "id=957a85f3-d56b-4aed-9f29-5f8fe1363e57"
)
ARCGIS_ITEM_URL = (
    "https://www.arcgis.com/sharing/rest/content/items/162d40a383fa48cbadc101ef18829bec?f=json"
)
# Field names follow the SiteBundle rights contract (docs/CONTRACTS.md, contracts/site.py
# Rights). The licence is unresolved, so every purpose stays unknown.
RIGHTS = {
    "source_id": SOURCE["source_key"],
    "source_reference": LAYER_URL,
    "licence_reference": "unresolved: conflicting licence statements (see rights_detail)",
    "required_attribution": "unknown until the licence conflict is resolved",
    "local_use_status": "unknown",
    "team_share_status": "unknown",
    "public_display_status": "unknown",
    "export_status": "unknown",
    "evidence": [CKAN_URL, ARCGIS_ITEM_URL],
}
RIGHTS_DETAIL = {
    "licence_statements": [
        {
            "where": "data.gov.uk / CKAN catalogue record",
            "statement": "UK Open Government Licence (OGL) v3.0 (license_id 'uk-ogl')",
            "licence_url": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
            "evidence_url": CKAN_URL,
            "observed": "2026-11-13 (metadata_modified 2026-01-07); not re-fetched by this script",
        },
        {
            "where": "ArcGIS item metadata for the Street Trees service",
            "statement": "links the INSPIRE End User Licence, which restricts use and "
            "redistribution",
            "licence_url": "https://www.ordnancesurvey.co.uk/documents/licensing/"
            "inspire-end-user-licence.pdf",
            "evidence_url": ARCGIS_ITEM_URL,
            "observed": "cited by docs/SOURCES.md [13]/[18] and reported by two reviewers on "
            "2026-11-13; not re-fetched by this script",
        },
    ],
    "conflict": "unresolved",
    "attribution_if_ogl_is_confirmed": "Contains public sector information licensed under "
    "the Open Government Licence v3.0. Source: Sheffield City Council, Street Trees.",
    "decision_needed": "A person resolves which licence governs this layer and records a "
    "status for each purpose. Until then every *_status stays unknown, which is not approval.",
}
MAX_FEATURES_LIMIT = 5000
MAX_ENVELOPE_KM2 = 25.0
MIN_EXTENT_M = 10.0
BNG_BOUNDS = (0.0, 0.0, 700000.0, 1300000.0)  # EPSG:27700 projected bounds, metres
RAW_NAME = re.compile(r"^(layer|count|page-\d{4})\.json$")
USER_AGENT = "canopy-tree-inventory-prep/1"
REPO = Path(__file__).resolve().parents[1]
# Allowlist: only these attributes reach the review sample. A new or unexpected
# free-text field on the layer is withheld by default.
SAMPLE_ATTRIBUTES = ("sitename", "featuretypename")
LOCATION_TEXT_FIELD = "featurelocation"
APPROVAL_SCOPE = (
    "authorises this download only; it is not a rights decision, so every rights *_status "
    "stays unknown until a person decides"
)
# A role from a fixed list, or a reference to where the approval is recorded; never a
# person's name, because the manifest is committable and the repository is public. Roles
# are an allowlist so that a name cannot pass as a slug.
APPROVAL_ROLES = ("coordinator", "data-owner", "integrator", "operator", "site-lead", "team-lead")
APPROVAL_REF = re.compile(
    r"(role:(" + "|".join(APPROVAL_ROLES) + r")"
    r"|#\d{1,7}(#issuecomment-\d{1,12})?"
    r"|https://github\.com/Pimentellll/sheffield-tree-planner/(issues|pull)/\d{1,7}"
    r"(#issuecomment-\d{1,12})?)",
    re.ASCII,  # \d is 0-9 only, never other Unicode digits
)
REVIEW_SAMPLE_NAME = "review-sample.json"
LOCAL_ONLY_SAMPLE_NAME = "local-only-sample-with-location-text.json"
ISO_UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", re.ASCII)
SHA256_HEX = re.compile(r"[0-9a-f]{64}", re.ASCII)
DECISION_1A_BBOX = [433700.0, 387100.0, 434500.0, 387700.0]
# Only these receipt keys reach the committable manifest; anything else (for example an old
# free-text approval field) stays in the local receipt.
MANIFEST_ACQUISITION_KEYS = (
    "layer_url",
    "bbox_27700",
    "max_features",
    "acquisition_approval_ref",
    "acquisition_approval_scope",
    "started_at_utc",
    "finished_at_utc",
    "page_size",
    "supports_pagination",
    "status",
)
MANIFEST_FILE_KEYS = ("file", "url", "final_url", "retrieved_at_utc", "http_status", "bytes", "sha256")
# The three #69 decisions, as recorded on issue #69 (13 Nov 2026).
RECORDED_DECISIONS = {
    "decided_by": "the #69 owner's coordinating session, under the owner's general "
    "delegation (issue #69, 2026-11-13); the owner's own confirmation is pending",
    "sample_envelope": "1a: Weston Park with surrounding streets, approximately "
    "433700,387100,434500,387700 in EPSG:27700, with the service count recorded first; "
    "park-interior coverage is unverified because the layer likely holds highway trees only",
    "rights": "2a: all four purposes stay unknown; the OGL v3.0 vs INSPIRE End User Licence "
    "conflict rules out recording any as permitted. Nothing may be displayed, shared or "
    "exported until a person records the endpoint's actual terms",
    "featurelocation": "3a: dropped from anything committed (including the review sample); "
    "kept in local outputs only",
}


def parse_approval_ref(text: str) -> str:
    value = text.strip()
    if not APPROVAL_REF.fullmatch(value):
        raise argparse.ArgumentTypeError(
            f"must be a role (role:{{{','.join(APPROVAL_ROLES)}}}) or a reference to where the "
            "approval is recorded (#<issue>, #<issue>#issuecomment-<id>, or that GitHub URL), "
            "never a person's name"
        )
    return value


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


def _inside_git_working_tree(path: Path) -> bool:
    """True inside any checkout or worktree (a ``.git`` dir or file on the path or above)."""
    resolved = path.resolve()
    return any((p / ".git").exists() for p in (resolved, *resolved.parents))


def _outside_repository(path: Path, flag: str) -> None:
    if path.resolve().is_relative_to(REPO) or _inside_git_working_tree(path):
        raise SystemExit(
            f"{flag} must be outside every git working tree (raw and full outputs stay out of git)"
        )


def _disjoint(raw_dir: Path, output_dir: Path) -> None:
    a, b = raw_dir.resolve(), output_dir.resolve()
    if a == b or a.is_relative_to(b) or b.is_relative_to(a):
        raise SystemExit("--raw-dir and --output-dir must be separate, non-nested directories")


class _RefuseRedirects(urllib.request.HTTPRedirectHandler):
    """A redirect could leave the fixed HTTPS host; refuse it and record the 3xx instead."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, f"redirect refused: {newurl}", headers, fp)


def _open(request: urllib.request.Request):
    """The script's only network call: redirects are refused, never followed."""
    return urllib.request.build_opener(_RefuseRedirects).open(request, timeout=60)


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
        "acquisition_approval_ref": approval,
        "acquisition_approval_scope": APPROVAL_SCOPE,
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
            with _open(request) as response:
                body, meta["http_status"] = response.read(), response.status
                meta["final_url"] = response.geturl()
        except urllib.error.HTTPError as exc:
            body, meta["http_status"] = exc.read(), exc.code
            meta["final_url"] = url
        (raw_dir / name).write_bytes(body)
        meta.update(bytes=len(body), sha256=_sha256(body))
        acquisition["files"].append(meta)
        if meta["final_url"] != url:
            check_url(meta["final_url"])
            raise SystemExit(f"{name}: the response came from a different URL than requested")
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
        count = get("count.json", _query_url({**spatial, "returnCountOnly": "true", "f": "json"}))
        common = {**spatial, "outFields": "*", "returnGeometry": "true", "outSR": "27700", "f": "json"}
        reported_count = count.get("count") if isinstance(count, dict) else None
        if type(reported_count) is int and reported_count < 0:
            raise SystemExit(
                f"the service reported a negative count ({reported_count}); refusing to fetch"
            )
        if not paging:
            # A single query cannot be capped, so --max-features is enforced from the count
            # first; the service's exceededTransferLimit still reports any truncation.
            reported = count.get("count") if isinstance(count, dict) else None
            if type(reported) is not int:
                raise SystemExit(
                    "layer does not support paging and the service count is not an integer; "
                    "refusing an uncapped single query"
                )
            if reported > max_features:
                raise SystemExit(
                    f"layer does not support paging and the service reports {reported} features, "
                    f"more than --max-features {max_features}; refusing an uncapped single query"
                )
            page = get("page-0000.json", _query_url(common))
            received = len(page.get("features") or []) if isinstance(page, dict) else 0
            if received > max_features:  # the layer changed between count and query
                raise SystemExit(
                    f"single query returned {received} features, more than --max-features "
                    f"{max_features}; refusing the acquisition"
                )
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
        if count_value["count"] < 0:
            return None, "negative_count"
        return count_value["count"], "ok"
    return None, "non_integer"


def _validate_receipt_values(acquisition: dict) -> None:
    """Every receipt value that can reach the committable manifest must have its expected
    form; anything else is refused before any output is written."""

    def bad(key, value):
        raise SystemExit(f"acquisition receipt value for {key!r} is not valid: {value!r}")

    checks = {
        "layer_url": lambda v: v == LAYER_URL,
        "max_features": lambda v: type(v) is int and 1 <= v <= MAX_FEATURES_LIMIT,
        "acquisition_approval_scope": lambda v: v == APPROVAL_SCOPE,
        "started_at_utc": lambda v: isinstance(v, str) and ISO_UTC.fullmatch(v),
        "finished_at_utc": lambda v: isinstance(v, str) and ISO_UTC.fullmatch(v),
        "page_size": lambda v: type(v) is int and 1 <= v <= 1000,
        "supports_pagination": lambda v: type(v) is bool,
        "status": lambda v: v == "complete",
    }
    for key, ok in checks.items():
        if key in acquisition and not ok(acquisition[key]):
            bad(key, acquisition[key])
    if "bbox_27700" in acquisition:
        box = acquisition["bbox_27700"]
        if not (isinstance(box, list) and len(box) == 4 and all(type(v) in (int, float) for v in box)):
            bad("bbox_27700", box)
        try:
            parse_bbox(",".join(repr(float(v)) for v in box))
        except (argparse.ArgumentTypeError, OverflowError, ValueError):
            bad("bbox_27700", box)
    file_checks = {
        "file": lambda v: isinstance(v, str) and RAW_NAME.match(v),
        "retrieved_at_utc": lambda v: isinstance(v, str) and ISO_UTC.fullmatch(v),
        "http_status": lambda v: type(v) is int and 100 <= v <= 599,
        "bytes": lambda v: type(v) is int and v >= 0,
        "sha256": lambda v: isinstance(v, str) and SHA256_HEX.fullmatch(v),
    }
    for record in acquisition.get("files", []):
        for key, ok in file_checks.items():
            if key in record and not ok(record[key]):
                bad(f"files[].{key}", record[key])
        for key in ("url", "final_url"):
            if key in record:
                if not isinstance(record[key], str) or not _query_is_expected(record[key]):
                    bad(f"files[].{key}", record[key])
                check_url(record[key])


# The query parameters fetch() itself sends, with the forms their values take; a receipt URL
# carrying anything else (for example free text) is refused before it reaches the manifest.
_QUERY_FORMS = {
    "f": re.compile(r"json", re.ASCII),
    "where": re.compile(r"1=1", re.ASCII),
    "geometry": re.compile(r"[0-9.eE+-]+(,[0-9.eE+-]+){3}", re.ASCII),
    "geometryType": re.compile(r"esriGeometryEnvelope", re.ASCII),
    "inSR": re.compile(r"27700", re.ASCII),
    "outSR": re.compile(r"27700", re.ASCII),
    "spatialRel": re.compile(r"esriSpatialRelIntersects", re.ASCII),
    "returnCountOnly": re.compile(r"true", re.ASCII),
    "outFields": re.compile(r"\*", re.ASCII),
    "returnGeometry": re.compile(r"true", re.ASCII),
    "orderByFields": re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,63} ASC", re.ASCII),
    "resultOffset": re.compile(r"\d{1,7}", re.ASCII),
    "resultRecordCount": re.compile(r"\d{1,4}", re.ASCII),
}


def _query_is_expected(url: str) -> bool:
    query = urllib.parse.urlsplit(url).query
    try:
        pairs = urllib.parse.parse_qsl(query, keep_blank_values=True, strict_parsing=bool(query))
    except ValueError:
        return False
    keys = [k for k, _ in pairs]
    if len(set(keys)) != len(keys):
        return False
    return all(k in _QUERY_FORMS and _QUERY_FORMS[k].fullmatch(v) for k, v in pairs)


def _recorded_command(args: argparse.Namespace) -> list[str]:
    """Rebuilt from the parsed arguments, never copied from argv, so no operator-local path
    (in any spelling, such as ``--output-dir=PATH``) reaches the committable manifest. Paths
    are replaced by fixed placeholders, because even a final directory name could be a
    person's name. The approval reference is validated (a role or a reference, never a
    name), so it is recorded as given."""
    out = [args.mode]
    if args.mode == "fetch":
        out += ["--bbox-27700", ",".join(repr(v) for v in args.bbox_27700)]
        out += ["--max-features", str(args.max_features)]
        out += ["--acquisition-approval-ref", args.acquisition_approval_ref]
    out += ["--raw-dir", "<raw-dir>", "--output-dir", "<output-dir>"]
    out += ["--sample-size", str(args.sample_size)]
    if args.keep_location_text:
        out.append("--keep-location-text")
    return out


def _native_crs_check(layer: dict) -> str:
    """Queries force outSR=27700, so the page CRS cannot reveal a server reprojection; the
    layer's own declared CRS must agree, or the build is refused."""
    declared = layer.get("spatialReference")
    if not isinstance(declared, dict):
        return "not declared by the layer metadata; native CRS unverified"
    codes = [declared.get(k) for k in ("latestWkid", "wkid") if type(declared.get(k)) is int]
    if not codes:
        return "not declared by the layer metadata; native CRS unverified"
    if 27700 not in codes:
        raise SystemExit(
            f"layer native CRS wkid {codes[0]} is not EPSG:27700; outSR=27700 would hide a "
            "server-side reprojection"
        )
    return "matches: layer declares EPSG:27700"


def build_outputs(raw_dir: Path, output_dir: Path, sample_size: int, keep_location: bool, mode, command):
    acquisition, receipt_sha256, layer, count_value, pages = load_raw(raw_dir)
    approval_ref = acquisition.get("acquisition_approval_ref")
    if not isinstance(approval_ref, str) or not APPROVAL_REF.fullmatch(approval_ref):
        raise SystemExit(
            "acquisition receipt has no valid acquisition_approval_ref (a role or a reference, "
            "never a person's name); refusing to write a committable manifest"
        )
    _validate_receipt_values(acquisition)
    native_crs = _native_crs_check(layer)
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
        keep = set(SAMPLE_ATTRIBUTES) | ({LOCATION_TEXT_FIELD} if keep_location else set())
        drop = tuple(f for f in attribute_fields if f not in keep)
        sample = redistributable_sample(built["inventory"], limit=sample_size, drop_attributes=drop)
    except InventoryError as exc:
        raise SystemExit(f"inventory refused: {exc}") from exc
    if keep_location:
        # Decision 3a: location text stays in local outputs only.
        sample["sample"]["local_only"] = (
            "includes featurelocation text (--keep-location-text); decision 3a: never commit "
            "this file"
        )
    inventory, receipt = built["inventory"], built["receipt"]
    envelope_is_1a = acquisition.get("bbox_27700") == DECISION_1A_BBOX
    limitations = [
        "Recorded locations only: no crowns, heights, health, survival or planting "
        "permission are implied.",
        "Species values are the source's 'featuretypename' text as recorded; not verified.",
        "Coordinates stay in the source CRS; no ENU/WGS84 conversion has been verified here.",
        "Bounded envelope sample; not a citywide or complete inventory unless counts say so.",
        "Reviewers report the layer likely covers council highway (street) trees only, not "
        "park, private or other trees; not verified here.",
        "Licence unresolved (OGL v3.0 vs INSPIRE End User Licence); every rights status is "
        "unknown.",
    ]
    if envelope_is_1a:
        limitations.append(
            "Park-interior coverage of the Weston Park envelope (decision 1a) is unverified; "
            "absence of a record is not absence of a tree."
        )
    manifest = {
        "schema": "canopy-source-tree-inventory-manifest/1",
        "mode": mode,
        "built_at_utc": _now(),
        "command": ["scripts/prepare_tree_inventory.py", *command],
        "source": SOURCE,
        "rights": RIGHTS,
        "rights_detail": {**RIGHTS_DETAIL, "layer_copyright_text": layer.get("copyrightText")},
        "acquisition_approval": {"reference": approval_ref, "scope": APPROVAL_SCOPE},
        "recorded_decisions": {
            **RECORDED_DECISIONS,
            "sample_envelope_applies_to_this_acquisition": envelope_is_1a,
        },
        "acquisition": {
            **{k: acquisition[k] for k in MANIFEST_ACQUISITION_KEYS if k in acquisition},
            "receipt_sha256": receipt_sha256,
            "files": [
                {k: f[k] for k in MANIFEST_FILE_KEYS if k in f} for f in acquisition.get("files", [])
            ],
            "service_count_status": count_status,
        },
        "layer_schema": {
            "name": layer.get("name"),
            "geometryType": layer.get("geometryType"),
            "spatialReference": layer.get("spatialReference"),
            "native_crs_check": native_crs,
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
            # Publisher text (untrusted, AGENTS.md 8): only the structural keys of each field.
            "fields": [
                {k: f[k] for k in ("name", "type", "alias", "length") if k in f} for f in fields
            ],
            "declared_but_not_imported": not_imported,
            "per_record_date_fields": date_fields or "none declared by the layer",
        },
        "counts": receipt["counts"],
        "inventory_sha256": receipt["inventory_sha256"],
        "limitations": limitations,
    }
    # Everything was computed; only now create the (fresh) output directory.
    output_dir = _fresh_dir(output_dir, "--output-dir")
    for name, value in (
        ("inventory.json", inventory),
        ("receipt.json", receipt),
        ("manifest.json", manifest),
        (LOCAL_ONLY_SAMPLE_NAME if keep_location else REVIEW_SAMPLE_NAME, sample),
    ):
        (output_dir / name).write_text(
            json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8"
        )
    return manifest, output_dir


def main(argv=None) -> int:
    # No prefix abbreviations: every option must be spelled out.
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    sub = parser.add_subparsers(dest="mode", required=True)
    fetch_p = sub.add_parser(
        "fetch", help="bounded acquisition from the fixed publisher layer", allow_abbrev=False
    )
    fetch_p.add_argument("--bbox-27700", type=parse_bbox, required=True)
    fetch_p.add_argument("--max-features", type=int, default=500)
    fetch_p.add_argument(
        "--acquisition-approval-ref",
        type=parse_approval_ref,
        required=True,
        help="role:<one of " + ", ".join(APPROVAL_ROLES) + ">, or #<issue>[#issuecomment-<id>] "
        "/ its GitHub URL, recording who authorised this download; never a person's name "
        "(not a rights decision)",
    )
    replay_p = sub.add_parser(
        "replay", help="rebuild outputs from a saved raw directory", allow_abbrev=False
    )
    for p in (fetch_p, replay_p):
        p.add_argument("--raw-dir", type=Path, required=True)
        p.add_argument("--output-dir", type=Path, required=True)
        p.add_argument("--sample-size", type=int, default=25)
        p.add_argument("--keep-location-text", action="store_true")
    args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.sample_size < 1:
        parser.error("--sample-size must be at least 1")
    _outside_repository(args.output_dir, "--output-dir")
    _disjoint(args.raw_dir, args.output_dir)
    if args.output_dir.resolve().exists():
        parser.error(f"--output-dir {args.output_dir} already exists; use a fresh path")
    if args.mode == "fetch":
        if not 1 <= args.max_features <= MAX_FEATURES_LIMIT:
            parser.error(f"--max-features must be between 1 and {MAX_FEATURES_LIMIT}")
        _outside_repository(args.raw_dir, "--raw-dir")
        raw_dir = _fresh_dir(args.raw_dir, "--raw-dir")
        fetch(args.bbox_27700, args.max_features, raw_dir, args.acquisition_approval_ref)
    else:
        raw_dir = args.raw_dir.resolve()
    manifest, output_dir = build_outputs(
        raw_dir,
        args.output_dir,
        args.sample_size,
        args.keep_location_text,
        args.mode,
        _recorded_command(args),
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
