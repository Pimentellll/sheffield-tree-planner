"""Synthetic-only BNG to true local ENU and aligned raster pilot for STP-006.

Heights must already be WGS84 ellipsoidal metres. ODN heights need a verified
vertical conversion before this code may be used for real Sheffield assets.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, isfinite, radians, sin

from pyproj import Transformer

_BNG_TO_GEO = Transformer.from_crs("EPSG:27700", "EPSG:4979", always_xy=True)
_GEO_TO_BNG = Transformer.from_crs("EPSG:4979", "EPSG:27700", always_xy=True)
_GEO_TO_ECEF = Transformer.from_crs("EPSG:4979", "EPSG:4978", always_xy=True)
_ECEF_TO_GEO = Transformer.from_crs("EPSG:4978", "EPSG:4979", always_xy=True)


def _finite3(values: tuple[float, float, float]) -> None:
    if len(values) != 3 or not all(isfinite(value) for value in values):
        raise ValueError("expected three finite metre values")


@dataclass(frozen=True)
class BngEnuTransform:
    """True ENU at a synthetic origin; source horizontal CRS is EPSG:27700."""

    origin_easting_m: float
    origin_northing_m: float
    origin_height_m: float
    height_datum: str = "WGS84_ELLIPSOIDAL"
    source_crs: str = "EPSG:27700"

    def __post_init__(self) -> None:
        _finite3((self.origin_easting_m, self.origin_northing_m, self.origin_height_m))
        if self.source_crs != "EPSG:27700":
            raise ValueError("source CRS must be EPSG:27700")
        if self.height_datum != "WGS84_ELLIPSOIDAL":
            raise ValueError(
                "ODN/unknown vertical datum requires a verified conversion"
            )

    def _origin(self) -> tuple[float, float, float, float, float]:
        lon, lat, _ = _BNG_TO_GEO.transform(
            self.origin_easting_m, self.origin_northing_m, self.origin_height_m
        )
        xyz = _GEO_TO_ECEF.transform(lon, lat, self.origin_height_m)
        if not all(isfinite(v) for v in (*xyz, lon, lat)):
            raise ValueError("origin could not be transformed")
        return lon, lat, *xyz

    def to_enu(
        self, easting_m: float, northing_m: float, height_m: float
    ) -> tuple[float, float, float]:
        _finite3((easting_m, northing_m, height_m))
        lon0, lat0, x0, y0, z0 = self._origin()
        lon, lat, _ = _BNG_TO_GEO.transform(easting_m, northing_m, height_m)
        x, y, z = _GEO_TO_ECEF.transform(lon, lat, height_m)
        if not all(isfinite(v) for v in (lon, lat, x, y, z)):
            raise ValueError("point could not be transformed")
        dl, dp = radians(lon0), radians(lat0)
        dx, dy, dz = x - x0, y - y0, z - z0
        return (
            -sin(dl) * dx + cos(dl) * dy,
            -sin(dp) * cos(dl) * dx - sin(dp) * sin(dl) * dy + cos(dp) * dz,
            cos(dp) * cos(dl) * dx + cos(dp) * sin(dl) * dy + sin(dp) * dz,
        )

    def from_enu(
        self, east_m: float, north_m: float, up_m: float
    ) -> tuple[float, float, float]:
        _finite3((east_m, north_m, up_m))
        lon0, lat0, x0, y0, z0 = self._origin()
        dl, dp = radians(lon0), radians(lat0)
        x = (
            x0
            - sin(dl) * east_m
            - sin(dp) * cos(dl) * north_m
            + cos(dp) * cos(dl) * up_m
        )
        y = (
            y0
            + cos(dl) * east_m
            - sin(dp) * sin(dl) * north_m
            + cos(dp) * sin(dl) * up_m
        )
        z = z0 + cos(dp) * north_m + sin(dp) * up_m
        lon, lat, height = _ECEF_TO_GEO.transform(x, y, z)
        easting, northing, _ = _GEO_TO_BNG.transform(lon, lat, height)
        if not all(isfinite(v) for v in (easting, northing, height)):
            raise ValueError("ENU point could not be transformed back")
        return easting, northing, height


@dataclass(frozen=True)
class SyntheticRaster:
    """North-up grid of cell-centre heights; no-data is None."""

    heights_m: tuple[tuple[float | None, ...], ...]
    centre_easting_m: float
    centre_northing_m: float
    cell_size_m: float
    height_datum: str = "WGS84_ELLIPSOIDAL"
    source_crs: str = "EPSG:27700"

    def __post_init__(self) -> None:
        if not self.heights_m or not self.heights_m[0]:
            raise ValueError("raster must contain cells")
        if any(len(row) != len(self.heights_m[0]) for row in self.heights_m):
            raise ValueError("raster rows must have equal length")
        if not all(
            isfinite(v)
            for v in (self.centre_easting_m, self.centre_northing_m, self.cell_size_m)
        ):
            raise ValueError("grid coordinates must be finite")
        if self.cell_size_m <= 0:
            raise ValueError("cell size must be positive")
        if self.source_crs != "EPSG:27700":
            raise ValueError("source CRS must be EPSG:27700")
        if self.height_datum != "WGS84_ELLIPSOIDAL":
            raise ValueError("unknown or ODN height datum is unsupported in pilot")
        if any(
            value is not None and not isfinite(value)
            for row in self.heights_m
            for value in row
        ):
            raise ValueError("heights must be finite or None")

    def source_xy(self, row: int, column: int) -> tuple[float, float]:
        return (
            self.centre_easting_m + column * self.cell_size_m,
            self.centre_northing_m - row * self.cell_size_m,
        )


@dataclass(frozen=True)
class SyntheticScene:
    terrain_vertices_enu_m: tuple[tuple[float, float, float] | None, ...]
    terrain_triangles: tuple[tuple[int, int, int], ...]
    elevated_cells: tuple[tuple[int, int, str], ...]
    missing_cells: tuple[tuple[int, int], ...]
    context_warning: str


def import_synthetic_pair(
    dtm: SyntheticRaster,
    dsm: SyntheticRaster,
    transform: BngEnuTransform,
    *,
    height_tolerance_m: float = 0.01,
    semantic_mask: tuple[tuple[str, ...], ...] | None = None,
) -> SyntheticScene:
    """Build deterministic terrain vertices; elevated DSM cells remain explicitly classified/unknown."""
    if (
        len(dtm.heights_m) != len(dsm.heights_m)
        or len(dtm.heights_m[0]) != len(dsm.heights_m[0])
        or (
            dtm.centre_easting_m,
            dtm.centre_northing_m,
            dtm.cell_size_m,
            dtm.height_datum,
            dtm.source_crs,
        )
        != (
            dsm.centre_easting_m,
            dsm.centre_northing_m,
            dsm.cell_size_m,
            dsm.height_datum,
            dsm.source_crs,
        )
        or dtm.height_datum != transform.height_datum
    ):
        raise ValueError("DTM/DSM grid, transform or vertical datum mismatch")
    if not isfinite(height_tolerance_m) or height_tolerance_m < 0:
        raise ValueError("height tolerance must be nonnegative and finite")
    rows, cols = len(dtm.heights_m), len(dtm.heights_m[0])
    if semantic_mask is not None and (
        len(semantic_mask) != rows or any(len(row) != cols for row in semantic_mask)
    ):
        raise ValueError("semantic mask must align with rasters")
    vertices = []
    elevated = []
    missing = []
    for row in range(rows):
        for col in range(cols):
            ground, surface = dtm.heights_m[row][col], dsm.heights_m[row][col]
            if ground is None or surface is None:
                vertices.append(None)
                missing.append((row, col))
                continue
            if surface < ground - height_tolerance_m:
                raise ValueError("DSM below DTM beyond declared tolerance")
            east, north = dtm.source_xy(row, col)
            vertices.append(transform.to_enu(east, north, ground))
            if surface > ground + height_tolerance_m:
                category = (
                    semantic_mask[row][col] if semantic_mask is not None else "unknown"
                )
                if category not in ("building", "vegetation", "unknown"):
                    raise ValueError("unsupported elevated-cell semantic class")
                elevated.append((row, col, category))
    triangles = []
    for row in range(rows - 1):
        for col in range(cols - 1):
            a = row * cols + col
            for tri in ((a, a + cols, a + 1), (a + 1, a + cols, a + cols + 1)):
                if all(vertices[index] is not None for index in tri):
                    triangles.append(tri)
    return SyntheticScene(
        tuple(vertices),
        tuple(triangles),
        tuple(elevated),
        tuple(missing),
        "Synthetic crop only; outside shadow-casting context and planting conditions are unknown.",
    )
