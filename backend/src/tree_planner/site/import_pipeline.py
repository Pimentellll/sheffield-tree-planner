"""Prepared-coordinate raster importer and explicit physical-scene adapter.

Working contract takeover-v1. This is synthetic engineering. Geographic BNG
reprojection is nonlinear and cannot be advertised as SiteBundle's exact affine
matrix. Real source import is therefore rejected until that contract, controls,
datum conversion, source rights and human reviews are resolved.
"""

from dataclasses import dataclass
import json
from math import isfinite, sqrt
from time import perf_counter

from tree_planner.canonical import content_hash
from tree_planner.contracts import Placement, SiteBundle

from .terrain import RasterGrid, affine_point, clip_pair, require_alignment


@dataclass(frozen=True)
class ImportResult:
    vertices_enu_m: tuple
    vertices_viewer_m: tuple
    triangles: tuple
    obstruction_triangles: tuple
    elevated_cells: tuple
    missing_cells: tuple
    warnings: tuple[str, ...]
    content_sha256: str
    elapsed_seconds: float
    spatial_spacing_m: float
    target_ids: tuple[str, ...]
    existing_tree_features: tuple[str, ...]

    def physical_scene(self, target_id, area_basis, *, existing_trees=(), baked_profile_states=()):
        """Export the frozen scene seam only for supported, flat synthetic data.

        Every triangle represents one disjoint target sample. The complete
        imported node window is the target: arbitrary target polygon clipping
        and overlapping targets are unsupported. No terrain is flattened.
        """
        if target_id not in self.target_ids or len(self.target_ids) != 1:
            raise ValueError("one resolved whole-crop target required")
        if area_basis not in ("surface", "planimetric"):
            raise ValueError("unsupported area basis")
        if self.missing_cells:
            raise ValueError("no-data leaves unresolved geometry; evaluation blocked")
        if any(kind == "unknown" for _, _, kind in self.elevated_cells):
            raise ValueError("unknown elevated semantics block physical evaluation")
        heights = {p[2] for p in self.vertices_enu_m if p is not None}
        if len(heights) != 1:
            raise ValueError("nonflat terrain unsupported by current evaluator; no flattening")
        if self.existing_tree_features:
            raise ValueError("existing tree feature/Placement correspondence requires review")
        vegetation = any(kind == "vegetation" for _, _, kind in self.elevated_cells)
        if vegetation and existing_trees:
            raise ValueError("cannot prove no double counting between DSM canopy and trees")
        if vegetation and (
            not baked_profile_states
            or any(type(s) is not str or not s.strip() for s in baked_profile_states)
            or len(set(baked_profile_states)) != len(baked_profile_states)
        ):
            raise ValueError("baked vegetation requires explicit supported profile state evidence")
        if any(not isinstance(p, Placement) for p in existing_trees):
            raise ValueError("existing_trees requires typed Placements")
        if len({p.placement_id for p in existing_trees}) != len(existing_trees):
            raise ValueError("duplicate existing Placement IDs")
        samples, triangles = [], []
        for index, triangle in enumerate(self.triangles):
            points = tuple(self.vertices_enu_m[i] for i in triangle)
            a, b, c = points
            u, v = tuple(b[i] - a[i] for i in range(3)), tuple(c[i] - a[i] for i in range(3))
            cross = (
                u[1] * v[2] - u[2] * v[1],
                u[2] * v[0] - u[0] * v[2],
                u[0] * v[1] - u[1] * v[0],
            )
            length = sqrt(sum(x * x for x in cross))
            if not length:
                raise ValueError("degenerate target triangle")
            triangle_id = f"terrain-{index}"
            triangles.append(dict(triangle_id=triangle_id, vertices_enu_m=points))
            samples.append(
                dict(
                    sample_id=f"sample-{index}",
                    position_enu_m=tuple(sum(p[i] for p in points) / 3 for i in range(3)),
                    normal_enu=tuple(x / length for x in cross),
                    area_m2=length / 2 if area_basis == "surface" else abs(cross[2]) / 2,
                    target_id=target_id,
                    area_basis=area_basis,
                    origin_triangle_id=triangle_id,
                )
            )
        if not samples:
            raise ValueError("empty target mesh")
        triangles.extend(
            dict(triangle_id=f"obstruction-{i}", vertices_enu_m=p)
            for i, p in enumerate(self.obstruction_triangles)
        )
        return dict(
            format_version="canopy-physical-scene/1",
            spatial_spacing_m=self.spatial_spacing_m,
            samples=samples,
            triangles=triangles,
            existing_trees=[p.model_dump(mode="json") for p in existing_trees],
            flat_ground_z_m=next(iter(heights)),
            baked_vegetation=(
                dict(
                    supported_profile_states=list(baked_profile_states),
                    existing_trees_separate=True,
                )
                if vegetation
                else None
            ),
        )


def import_pair(
    site: SiteBundle,
    dtm: RasterGrid,
    dsm: RasterGrid,
    *,
    bounds_xy=None,
    semantic_mask=None,
    height_tolerance_m=0.01,
    max_cells=1_000_000,
):
    """Triangulate aligned DTM nodes and labelled DSM cell-box approximations.

    Raster XY coordinates are the prepared source geometry coordinates to which
    source_to_analysis applies. horizontal_crs retains source metadata only; it
    does not cause reprojection. Caller must not pass raw BNG as true-north ENU.
    DSM boxes are an explicit synthetic raster approximation, not surveyed walls
    or a biologically validated canopy. Unknown elevated cells stay unknown.
    """
    started = perf_counter()
    if not isinstance(site, SiteBundle):
        raise TypeError("typed SiteBundle required")
    if site.site_kind != "synthetic_test":
        raise ValueError("real-site import rejected: verified geodesy, rights and review required")
    if site.source_units != "m" or site.metres_per_source_unit != 1:
        raise ValueError("prepared raster source units must be metres")
    if site.source_up_axis != (0, 0, 1):
        raise ValueError("raster height axis must be source positive z")
    if site.analysis_to_viewer[3] != (0, 0, 0, 1):
        raise ValueError("viewer matrix must be affine")
    datum_name = site.vertical_datum.name.casefold()
    if "odn" in datum_name or "newlyn" in datum_name or datum_name in ("epsg:5701", "epsg:7405"):
        raise ValueError("ODN requires actual verified vertical grid conversion before import")
    if site.vertical_datum.status == "unknown":
        raise ValueError("unknown height datum")
    require_alignment(dtm, dsm)
    if dtm.horizontal_crs != site.horizontal_crs:
        raise ValueError("raster CRS differs from SiteBundle source CRS")
    if dtm.vertical_datum != site.vertical_datum.name:
        raise ValueError("raster and bundle vertical datum differ")
    rows, columns = len(dtm.heights_m), len(dtm.heights_m[0])
    if rows < 2 or columns < 2:
        raise ValueError("terrain mesh requires at least 2x2 nodes")
    if type(max_cells) is not int or max_cells <= 0 or rows * columns > max_cells:
        raise ValueError("raster exceeds explicit cell bound")
    if not isfinite(height_tolerance_m) or height_tolerance_m < 0:
        raise ValueError("height tolerance must be finite and nonnegative")
    if semantic_mask is not None:
        if (
            len(semantic_mask) != rows
            or any(len(row) != columns for row in semantic_mask)
            or any(
                v not in ("ground", "building", "vegetation", "unknown")
                for row in semantic_mask
                for v in row
            )
        ):
            raise ValueError("semantic mask must align and use supported classes")
    if bounds_xy is not None:
        cropped_dtm, cropped_dsm = clip_pair(dtm, dsm, bounds_xy)
        if semantic_mask is not None:
            c0 = round((cropped_dtm.centre_easting_m - dtm.centre_easting_m) / dtm.cell_size_m)
            r0 = round((dtm.centre_northing_m - cropped_dtm.centre_northing_m) / dtm.cell_size_m)
            semantic_mask = tuple(
                tuple(row[c0 : c0 + len(cropped_dtm.heights_m[0])])
                for row in semantic_mask[r0 : r0 + len(cropped_dtm.heights_m)]
            )
        dtm, dsm = cropped_dtm, cropped_dsm
        rows, columns = len(dtm.heights_m), len(dtm.heights_m[0])
    vertices, missing, elevated, obstructions = [], [], [], []
    for row in range(rows):
        for column in range(columns):
            ground, surface = dtm.heights_m[row][column], dsm.heights_m[row][column]
            if ground is None or surface is None:
                vertices.append(None)
                missing.append((row, column))
                continue
            if surface < ground - height_tolerance_m:
                raise ValueError("DSM below DTM beyond declared tolerance")
            east, north = dtm.xy(row, column)
            vertices.append(affine_point(site.source_to_analysis, (east, north, ground)))
            if surface > ground + height_tolerance_m:
                kind = semantic_mask[row][column] if semantic_mask is not None else "unknown"
                if kind == "ground":
                    raise ValueError("elevated DSM cell conflicts with ground semantic")
                elevated.append((row, column, kind))
                if kind != "unknown":
                    # Clip synthetic cell boxes to the node-window envelope.
                    half = dtm.cell_size_m / 2
                    west = max(east - half, dtm.centre_easting_m)
                    right = min(east + half, dtm.xy(0, columns - 1)[0])
                    south = max(north - half, dtm.xy(rows - 1, 0)[1])
                    top = min(north + half, dtm.centre_northing_m)
                    points = tuple(
                        affine_point(site.source_to_analysis, (x, y, z))
                        for z in (ground, surface)
                        for x, y in ((west, south), (right, south), (right, top), (west, top))
                    )
                    for a, b, c in (
                        (0, 2, 1),
                        (0, 3, 2),
                        (4, 5, 6),
                        (4, 6, 7),
                        (0, 1, 5),
                        (0, 5, 4),
                        (1, 2, 6),
                        (1, 6, 5),
                        (2, 3, 7),
                        (2, 7, 6),
                        (3, 0, 4),
                        (3, 4, 7),
                    ):
                        obstructions.append((points[a], points[b], points[c]))
    triangles = []
    for row in range(rows - 1):
        for column in range(columns - 1):
            a = row * columns + column
            for triangle in ((a, a + columns, a + 1), (a + 1, a + columns, a + columns + 1)):
                if all(vertices[i] is not None for i in triangle):
                    triangles.append(triangle)
    viewer = tuple(
        affine_point(site.analysis_to_viewer, p) if p is not None else None for p in vertices
    )
    warnings = (
        "Synthetic prepared-coordinate crop; no Sheffield or planting permission evidence.",
        "Outside crop shadow-casting context unknown; boundary truncation may bias shade.",
        "DSM cell boxes are a declared synthetic resolution approximation.",
        *site.coverage.horizon_limitations,
        *site.coverage.boundary_limitations,
    )
    digest = content_hash(
        json.loads(
            json.dumps(
                dict(
                    vertices=vertices,
                    triangles=triangles,
                    obstructions=obstructions,
                    viewer=viewer,
                    elevated=elevated,
                    missing=missing,
                    grid=dtm.grid_key,
                    site_id=site.site_id,
                    scene_revision=site.scene_revision,
                    semantic_revision=site.semantic_revision,
                    source_to_analysis=site.source_to_analysis,
                    analysis_to_viewer=site.analysis_to_viewer,
                    datum=site.vertical_datum.model_dump(mode="json"),
                    height_tolerance_m=height_tolerance_m,
                ),
                allow_nan=False,
            )
        )
    )
    return ImportResult(
        tuple(vertices),
        viewer,
        tuple(triangles),
        tuple(obstructions),
        tuple(elevated),
        tuple(missing),
        tuple(warnings),
        digest,
        perf_counter() - started,
        dtm.cell_size_m,
        tuple(t.target_id for t in site.targets),
        tuple(t.feature_id for t in site.existing_trees),
    )
