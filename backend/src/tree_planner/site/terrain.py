"""Bounded, aligned metre raster operations; no implicit reprojection/resampling.

Cell-centre triangulation/no-data policy extends Arnav Chitriv's PR40 pilot
dac463b5cc949eba43b71e96fbc021ba0dcfd0b5. Inputs here are explicit prepared
coordinates, not a GeoTIFF reader or a claim of geographic accuracy.
"""

from dataclasses import dataclass, replace
from math import isfinite


@dataclass(frozen=True)
class RasterGrid:
    heights_m: tuple[tuple[float | None, ...], ...]
    centre_easting_m: float
    centre_northing_m: float
    cell_size_m: float
    horizontal_crs: str
    vertical_datum: str

    def __post_init__(self):
        if (
            type(self.heights_m) is not tuple
            or not self.heights_m
            or any(type(row) is not tuple for row in self.heights_m)
            or not self.heights_m[0]
            or any(len(row) != len(self.heights_m[0]) for row in self.heights_m)
        ):
            raise ValueError("raster requires immutable nonempty rectangular rows")
        if not all(
            type(v) in (float, int) and isfinite(v)
            for v in (self.centre_easting_m, self.centre_northing_m, self.cell_size_m)
        ):
            raise ValueError("raster coordinates must be finite metres")
        if self.cell_size_m <= 0:
            raise ValueError("cell size must be positive")
        if not self.horizontal_crs or not self.vertical_datum:
            raise ValueError("explicit CRS and vertical datum required")
        if any(
            v is not None and (type(v) not in (float, int) or not isfinite(v))
            for row in self.heights_m
            for v in row
        ):
            raise ValueError("height must be finite or explicit None no-data")

    def xy(self, row, column):
        return (
            self.centre_easting_m + column * self.cell_size_m,
            self.centre_northing_m - row * self.cell_size_m,
        )

    @property
    def grid_key(self):
        return (
            len(self.heights_m),
            len(self.heights_m[0]),
            self.centre_easting_m,
            self.centre_northing_m,
            self.cell_size_m,
            self.horizontal_crs,
            self.vertical_datum,
        )


def require_alignment(dtm: RasterGrid, dsm: RasterGrid):
    if dtm.grid_key != dsm.grid_key:
        raise ValueError("DTM/DSM must align in shape, origin, resolution, CRS and datum")


def clip_pair(dtm: RasterGrid, dsm: RasterGrid, bounds_xy):
    """Inclusive node-window crop. Nonaligned bounds fail; no hidden resampling.

    Bounds are min-east, min-north, max-east, max-north. At least 2x2 nodes
    are required. Output covers node centres, not the full outer pixel edges.
    """
    require_alignment(dtm, dsm)
    if len(bounds_xy) != 4 or not all(isfinite(v) for v in bounds_xy):
        raise ValueError("four finite crop bounds required")
    west, south, east, north = bounds_xy
    if west >= east or south >= north:
        raise ValueError("crop bounds must have positive area")
    indices = (
        (west - dtm.centre_easting_m) / dtm.cell_size_m,
        (dtm.centre_northing_m - north) / dtm.cell_size_m,
        (east - dtm.centre_easting_m) / dtm.cell_size_m,
        (dtm.centre_northing_m - south) / dtm.cell_size_m,
    )
    if any(abs(i - round(i)) > 1e-9 for i in indices):
        raise ValueError("crop bounds must coincide with grid nodes")
    c0, r0, c1, r1 = (round(i) for i in indices)
    if not (0 <= c0 < c1 < len(dtm.heights_m[0]) and 0 <= r0 < r1 < len(dtm.heights_m)):
        raise ValueError("crop requires at least 2x2 nodes inside coverage")
    return tuple(
        replace(
            grid,
            heights_m=tuple(row[c0 : c1 + 1] for row in grid.heights_m[r0 : r1 + 1]),
            centre_easting_m=west,
            centre_northing_m=north,
        )
        for grid in (dtm, dsm)
    )


def affine_point(matrix, point):
    """Apply the published row-major affine matrix to a column point."""
    if len(point) != 3 or not all(isfinite(v) for v in point):
        raise ValueError("three finite source coordinates required")
    result = tuple(sum(row[j] * point[j] for j in range(3)) + row[3] for row in matrix[:3])
    if not all(isfinite(v) for v in result):
        raise ValueError("nonfinite transformed coordinates")
    return result
