"""Crop Environment Agency 1 m LiDAR tiles to a view-only terrain context file (STP-005 / STP-012).

Reads the DTM and first-return DSM GeoTIFFs (or the downloaded .zip files that contain
them), crops both to one British National Grid box, and writes:

  <out>/<name>.json   metadata: grid, source file hashes, licence, attribution, markers
  <out>/<name>.bin    float32 little-endian heights: DTM rows north-to-south, then DSM

The output is for DISPLAY ONLY. It is not a SiteBundle, is not registered with the backend
and is never used by the evaluator. Heights are copied from the rasters; the only
processing is cropping and block reduction (DTM block mean, DSM block max), both recorded
in the metadata. Raw tiles and outputs stay out of git.

    uv run --with rasterio --with numpy python frontend/scripts/prepare_terrain.py \
        --dtm <DTM .tif or .zip> --dsm <first-return DSM .tif or .zip> --out ../canopy-terrain

Defaults crop Weston Park with the 450 m context buffer from docs/site-audit/STP-005-desk-audit.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# From the STP-005 desk audit (13 Nov 2026). Boxes are discovery extents, not surveyed boundaries.
WESTON_BUFFERED = (433389, 386799, 434611, 388013)
WESTON_DISCOVERY = (433839, 387249, 434161, 387563)
ARTS_TOWER_BNG = (434201, 387444)
ATTRIBUTION = "© Environment Agency copyright and/or database right 2022. All rights reserved."
LICENCE = "Open Government Licence v3.0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_tif(path: Path, tile: str, scratch: Path) -> tuple[Path, str]:
    """Return a readable GeoTIFF and a description of where it came from."""
    if path.suffix.lower() != ".zip":
        return path, path.name
    with zipfile.ZipFile(path) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith((".tif", ".tiff"))]
        wanted = [n for n in names if tile.lower() in n.lower()] or names
        if len(wanted) != 1:
            raise SystemExit(f"{path.name}: expected one GeoTIFF for tile {tile}, found {wanted or 'none'}")
        archive.extract(wanted[0], scratch)
        return scratch / wanted[0], f"{path.name}!{wanted[0]}"


def read_crop(tif: Path, box, step: int, reduce: str):
    import numpy as np
    import rasterio
    from rasterio.windows import from_bounds

    with rasterio.open(tif) as src:
        if src.crs is None or src.crs.to_epsg() != 27700:
            raise SystemExit(f"{tif.name}: expected EPSG:27700, found {src.crs}")
        if abs(src.res[0] - 1) > 1e-6 or abs(src.res[1] - 1) > 1e-6:
            raise SystemExit(f"{tif.name}: expected 1 m cells, found {src.res}")
        left, bottom, right, top = src.bounds
        if not (left <= box[0] and box[2] <= right and bottom <= box[1] and box[3] <= top):
            raise SystemExit(f"{tif.name}: crop box {box} is not inside tile bounds {tuple(src.bounds)}")
        window = from_bounds(*box, transform=src.transform).round_offsets().round_lengths()
        data = src.read(1, window=window).astype("float64")
        nodata = src.nodata
        tags = {k: v for k, v in src.tags().items() if len(str(v)) < 200}
        info = dict(crs="EPSG:27700", nodata=nodata, dtype=src.dtypes[0], tile_bounds=[left, bottom, right, top], tags=tags)
    if nodata is not None:
        data[data == nodata] = np.nan
    rows, cols = (data.shape[0] // step) * step, (data.shape[1] // step) * step
    blocks = data[:rows, :cols].reshape(rows // step, step, cols // step, step)
    with np.errstate(all="ignore"):
        reduced = np.nanmean(blocks, axis=(1, 3)) if reduce == "mean" else np.nanmax(blocks, axis=(1, 3))
    return reduced.astype("<f4"), info


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dtm", type=Path, required=True)
    parser.add_argument("--dsm", type=Path, required=True, help="first-return DSM")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--name", default="weston-park")
    parser.add_argument("--title", default="Weston Park and context")
    parser.add_argument("--tile", default="SK38nw")
    parser.add_argument("--box", type=int, nargs=4, default=WESTON_BUFFERED, metavar=("E_MIN", "N_MIN", "E_MAX", "N_MAX"))
    parser.add_argument("--step", type=int, default=2, help="output spacing in metres (block reduction)")
    parser.add_argument("--survey", default="EA survey polygon P_10706, flown 16–17 March 2021 (leaf-off), 2022 composite")
    args = parser.parse_args(argv)

    import numpy as np

    with tempfile.TemporaryDirectory() as scratch:
        dtm_tif, dtm_from = resolve_tif(args.dtm, args.tile, Path(scratch) / "dtm")
        dsm_tif, dsm_from = resolve_tif(args.dsm, args.tile, Path(scratch) / "dsm")
        dtm, dtm_info = read_crop(dtm_tif, args.box, args.step, "mean")
        dsm, dsm_info = read_crop(dsm_tif, args.box, args.step, "max")
        tif_hashes = dict(dtm=sha256(dtm_tif), dsm=sha256(dsm_tif))
    if dtm.shape != dsm.shape:
        raise SystemExit(f"DTM {dtm.shape} and DSM {dsm.shape} crops differ")
    rows, cols = dtm.shape
    args.out.mkdir(parents=True, exist_ok=True)
    payload = dtm.tobytes() + dsm.tobytes()
    bin_path = args.out / f"{args.name}.bin"
    bin_path.write_bytes(payload)
    default_site = tuple(args.box) == WESTON_BUFFERED
    meta = dict(
        kind="canopy-terrain-context/1",
        name=args.name,
        title=args.title,
        synthetic_test=False,
        purpose="View-only context. Not a SiteBundle; never used by the evaluator.",
        crs="EPSG:27700 (British National Grid); grid north, not true north",
        box_bng=list(args.box),
        spacing_m=args.step,
        cols=cols,
        rows=rows,
        layout="float32 little-endian; DTM rows north-to-south, then DSM rows north-to-south; NaN = no data",
        reduction=f"{args.step} m blocks from 1 m cells: DTM block mean, DSM block max",
        bin=bin_path.name,
        bin_sha256=hashlib.sha256(payload).hexdigest(),
        vertical_datum="Ordnance Datum Newlyn as documented by the publisher; not confirmed from file tags" ,
        survey=args.survey,
        licence=LICENCE,
        attribution=ATTRIBUTION,
        sources=[
            dict(role="DTM (last return, bare ground)", file=dtm_from, download_sha256=sha256(args.dtm), geotiff_sha256=tif_hashes["dtm"], **dtm_info),
            dict(role="DSM (first return: ground, buildings, vegetation)", file=dsm_from, download_sha256=sha256(args.dsm), geotiff_sha256=tif_hashes["dsm"], **dsm_info),
        ],
        stats=dict(
            dtm_min_m=float(np.nanmin(dtm)), dtm_max_m=float(np.nanmax(dtm)),
            max_height_above_ground_m=float(np.nanmax(dsm - dtm)),
            nodata_cells=int(np.isnan(dtm).sum() + np.isnan(dsm).sum()),
        ),
        boxes=[dict(label="Weston Park discovery box (OSM extent; not a surveyed boundary)", bng=list(WESTON_DISCOVERY))] if default_site else [],
        markers=[dict(label="Arts Tower (78 m, published coordinates)", bng=list(ARTS_TOWER_BNG), note="Position converted without OSTN15; metre-level error")] if default_site else [],
        limitations=[
            "Leaf-off March survey: deciduous crowns are under-represented",
            "A 1 m surface model cannot tell buildings from tree canopy; elevated cells are unclassified",
            "Not co-registered to a surveyed control point; do not measure from this view",
        ],
        generated_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
    (args.out / f"{args.name}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(dict(written=str(args.out / f"{args.name}.json"), cols=cols, rows=rows, bytes=len(payload), stats=meta["stats"], dtm_sha256=tif_hashes["dtm"], dsm_sha256=tif_hashes["dsm"]), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
