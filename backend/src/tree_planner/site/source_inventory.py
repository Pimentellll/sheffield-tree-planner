"""Source-backed recorded-tree inventory from ArcGIS point-layer query pages (GEO3D-01 / I1).

Internal preprocessing adapter. It is pure and deterministic: it never fetches, never
touches scenarios, runtime services or model state, and changes no public API or schema.
The operator-run ``scripts/prepare_tree_inventory.py`` acquires pages and calls it.

What a record means here: a council record of a tree *location* (evidence class
``recorded_location``). It is not a verified current crown, species, health state,
surveyed position or planting permission, and record presence is not proof of survival.

Rules this adapter keeps:

* Geometry and CRS are preserved exactly as the source supplied them. No coordinate
  conversion happens here; a later, verified ENU transform consumes ``source_crs``. The
  output is deliberately **not** GeoJSON, so British National Grid coordinates can never
  be mistaken for RFC 7946 WGS84.
* Only attributes the source actually supplied are kept; absent, null or blank values are
  listed under ``unknown`` and never filled in.
* Records are never fused by proximity. Identical repeats of one source ID (for example a
  pagination overlap) are kept once and counted; conflicting *valid* records sharing a
  source ID are both rejected and reported. A copy already rejected for unusable geometry
  or ID does not take part in that comparison, so its valid twin is kept. Distinct IDs at
  identical coordinates are both kept and reported as coincident.
* An unknown or inconsistent CRS or a non-point layer fails explicitly
  (:class:`InventoryError`) instead of producing plausible output. Fields the caller did
  not declare are counted as schema drift and their values are not imported.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import math
from typing import Any

from tree_planner.canonical import content_hash

INVENTORY_SCHEMA = "canopy-source-tree-inventory/1"
EVIDENCE_CLASS = "recorded_location"
MEANING = (
    "Council record of a tree location. Not a verified current crown, species, health "
    "state, surveyed position or planting permission; presence is not proof of survival."
)
ID_STABILITY = (
    "per-snapshot: feature_id wraps the service record ID (e.g. ArcGIS objectid), which a "
    "republish or reload may renumber. Treat an ID as stable only within one recorded source "
    "snapshot; never match records across snapshots by feature_id alone."
)
# EPSG codes this adapter can label without guessing. Anything else fails closed.
KNOWN_CRS = {27700: "EPSG:27700", 4326: "EPSG:4326"}
CRS_AXES = {
    "EPSG:27700": {"x_axis": "easting", "y_axis": "northing", "unit": "metre"},
    "EPSG:4326": {"x_axis": "longitude", "y_axis": "latitude", "unit": "degree"},
}


class InventoryError(ValueError):
    """The source pages cannot be turned into an inventory without guessing."""


def _crs(spatial_reference: Any) -> str:
    if not isinstance(spatial_reference, Mapping):
        raise InventoryError("page has no spatialReference; source CRS is unknown")
    for key in ("latestWkid", "wkid"):
        code = spatial_reference.get(key)
        if type(code) is int:
            if code not in KNOWN_CRS:
                raise InventoryError(f"unsupported source CRS wkid {code}")
            return KNOWN_CRS[code]
    raise InventoryError("spatialReference has no integer wkid; source CRS is unknown")


def _finite_number(value: Any) -> bool:
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:  # an int too large for a float, e.g. 10**400
        return False


def build_inventory(
    pages: Sequence[Mapping[str, Any]],
    *,
    source: Mapping[str, Any],
    id_field: str,
    attribute_fields: Sequence[str],
    declared_fields: Sequence[str] | None = None,
    service_count: int | None = None,
    service_count_status: str = "not_requested",
    requested_limit: int | None = None,
) -> dict:
    """Turn ArcGIS ``f=json`` query pages into a versioned inventory and receipt.

    ``source`` must include ``source_key`` (stable short name used in feature IDs),
    ``layer_url`` and anything else to carry into the output unchanged. ``id_field`` and
    ``attribute_fields`` are the declared fields to import; ``declared_fields`` is the whole
    declared field list, used only to tell real schema drift from declared-but-not-imported
    fields. ``service_count`` is the count the service reported for the same query, and
    ``service_count_status`` says why it may be absent (``not_requested``, ``service_error``,
    ``non_integer``); ``requested_limit`` is the operator's cap. All are only reported.
    """
    if not isinstance(source, Mapping) or not isinstance(source.get("source_key"), str):
        raise InventoryError("source must name a source_key")
    if not pages:
        raise InventoryError("no source pages")
    declared = [id_field, *attribute_fields]
    if len(set(declared)) != len(declared) or not all(isinstance(f, str) and f for f in declared):
        raise InventoryError("declared fields must be distinct non-empty names")
    known_fields = set(declared) | set(declared_fields or ())

    crs_values, received = set(), []
    last_page_truncated = False
    for index, page in enumerate(pages):
        if not isinstance(page, Mapping):
            raise InventoryError(f"page {index} is not an object")
        if "error" in page:
            raise InventoryError(f"page {index} is a service error response")
        geometry_type = page.get("geometryType")
        if geometry_type is not None and geometry_type != "esriGeometryPoint":
            raise InventoryError(f"page {index} geometryType {geometry_type!r} is not a point layer")
        features = page.get("features")
        if not isinstance(features, list):
            raise InventoryError(f"page {index} has no features list")
        crs_values.add(_crs(page.get("spatialReference")))
        last_page_truncated = page.get("exceededTransferLimit") is True
        received.extend((index, position, f) for position, f in enumerate(features))
    if len(crs_values) != 1:
        raise InventoryError(f"pages disagree on source CRS: {sorted(crs_values)}")
    crs = crs_values.pop()

    rejected, by_id, schema_drift = [], {}, {}
    for page_index, position, feature in received:
        where = {"page": page_index, "position": position}
        if not isinstance(feature, Mapping) or not isinstance(feature.get("attributes"), Mapping):
            rejected.append({**where, "reason": "feature has no attributes object"})
            continue
        attributes = feature["attributes"]
        for key in attributes:
            if key not in known_fields:
                schema_drift[key] = schema_drift.get(key, 0) + 1
        source_id = attributes.get(id_field)
        if type(source_id) is not int:
            rejected.append({**where, "reason": f"missing or non-integer {id_field}"})
            continue
        geometry = feature.get("geometry")
        if (
            not isinstance(geometry, Mapping)
            or not _finite_number(geometry.get("x"))
            or not _finite_number(geometry.get("y"))
        ):
            rejected.append(
                {**where, "source_record_id": source_id, "reason": "missing or non-finite point"}
            )
            continue
        supplied, unknown, anomalies = {}, [], []
        for name in attribute_fields:
            value = attributes.get(name)
            if value is None or (isinstance(value, str) and not value.strip()):
                unknown.append(name)
            elif isinstance(value, str):
                supplied[name] = value
            else:
                unknown.append(name)
                anomalies.append(f"{name}: non-string value not used")
        record = {
            "feature_id": f"{source['source_key']}:{source_id}",
            "source_record_id": source_id,
            "evidence_class": EVIDENCE_CLASS,
            "geometry": {
                "kind": "point",
                "source_crs": crs,
                "x": geometry["x"],
                "y": geometry["y"],
                **CRS_AXES[crs],
            },
            "attributes": supplied,
            "unknown": unknown,
        }
        if anomalies:
            record["anomalies"] = anomalies
        by_id.setdefault(source_id, []).append((where, record))

    features, duplicates, conflicts = [], 0, []
    for source_id in sorted(by_id):
        entries = by_id[source_id]
        distinct = {content_hash(record) for _, record in entries}
        if len(distinct) > 1:
            conflicts.append(
                {
                    "source_record_id": source_id,
                    "occurrences": [where for where, _ in entries],
                    "reason": "records share a source ID but differ; neither is used",
                }
            )
            continue
        duplicates += len(entries) - 1
        features.append(entries[0][1])

    by_position: dict[tuple, list[str]] = {}
    for record in features:
        key = (record["geometry"]["x"], record["geometry"]["y"])
        by_position.setdefault(key, []).append(record["feature_id"])
    coincident = [
        {"x": x, "y": y, "feature_ids": ids}
        for (x, y), ids in sorted(by_position.items())
        if len(ids) > 1
    ]

    counts = {
        "pages": len(pages),
        "features_received": len(received),
        "features_kept": len(features),
        "rejected": len(rejected),
        "identical_repeats_dropped": duplicates,
        "conflicting_source_ids": len(conflicts),
        "coincident_location_groups": len(coincident),
        "service_reported_count": service_count,
        "requested_limit": requested_limit,
        "last_page_reported_more_records": last_page_truncated,
    }
    # Distinct source IDs seen at all (kept, conflicting or rejected); records rejected
    # before an ID could be read cannot be matched to the service count and are excluded.
    seen_ids = set(by_id) | {r["source_record_id"] for r in rejected if "source_record_id" in r}
    unique_received = len(seen_ids)
    counts["distinct_source_ids_seen"] = unique_received
    counts["service_count_status"] = service_count_status
    if last_page_truncated:
        completeness = "incomplete: the service reported more records than were retrieved"
    elif service_count is None:
        completeness = {
            "not_requested": "unknown: no service count was requested",
            "service_error": "unknown: the service count request returned an error",
            "non_integer": "unknown: the service count response had no integer count",
        }.get(service_count_status, f"unknown: service count {service_count_status}")
    elif not received:
        completeness = (
            f"empty: no records retrieved for this query (service reported {service_count})"
        )
    elif not features:
        completeness = (
            f"no usable records: all {len(received)} retrieved records were rejected or "
            f"conflicting (service reported {service_count})"
        )
    else:
        tally = (
            f"{len(features)} kept, {len(rejected)} rejected, "
            f"{len(conflicts)} conflicting source IDs"
        )
        if unique_received == service_count:
            completeness = f"matches the service-reported count for this query ({tally})"
        else:
            completeness = (
                f"mismatch: {unique_received} distinct source IDs retrieved, "
                f"service reported {service_count} ({tally})"
            )
    counts["completeness_relative_to_service"] = completeness

    inventory = {
        "schema": INVENTORY_SCHEMA,
        "meaning": MEANING,
        "id_stability": ID_STABILITY,
        "source": dict(source),
        "source_crs": crs,
        "coordinate_conversion": "none; source geometry preserved for a later verified transform",
        "declared_fields": {"id": id_field, "attributes": list(attribute_fields)},
        "features": features,
    }
    receipt = {
        "schema": INVENTORY_SCHEMA + "#receipt",
        "counts": counts,
        "rejected": rejected,
        "conflicts": conflicts,
        "coincident_locations": coincident,
        "schema_drift_undeclared_attribute_counts": dict(sorted(schema_drift.items())),
        "inventory_sha256": content_hash(inventory),
    }
    return {"inventory": inventory, "receipt": receipt}


def redistributable_sample(inventory: Mapping[str, Any], *, limit: int, drop_attributes=()) -> dict:
    """First ``limit`` features (inventory order), optionally without named attributes.

    Used to prepare a small sample for review before any commit; dropped attribute names
    are recorded so the sample never looks more complete than it is.
    """
    if type(limit) is not int or limit <= 0:
        raise InventoryError("sample limit must be a positive integer")
    dropped = sorted(set(drop_attributes))
    features = []
    for record in list(inventory["features"])[:limit]:
        trimmed = dict(record)
        trimmed["attributes"] = {
            k: v for k, v in record["attributes"].items() if k not in dropped
        }
        # Supplied by the source but withheld here; distinct from "unknown" (not supplied).
        withheld = sorted(k for k in record["attributes"] if k in dropped)
        if withheld:
            trimmed["withheld_for_sample"] = withheld
        features.append(trimmed)
    sample = {
        **{k: v for k, v in inventory.items() if k != "features"},
        "schema": inventory["schema"] + "#sample",
        "sample": {
            "of_inventory_sha256": content_hash(dict(inventory)),
            "features": len(features),
            "selection": "first features in source-ID order",
            "attributes_removed_for_sample": dropped,
        },
        "features": features,
    }
    return sample
