"""Labelled synthetic raster tests, never Sheffield observations."""

from dataclasses import replace

import pytest

from tree_planner.contracts import SiteBundle
from tree_planner.site.terrain import RasterGrid, clip_pair
from tree_planner.site.import_pipeline import import_pair
from synthetic_inputs import site_data


def bundle(**changes):
    data = site_data()
    data["vertical_datum"] = dict(name="synthetic_local_m", status="assumed", evidence=[])
    data.update(changes)
    return SiteBundle.model_validate(data)


def raster(heights=None, **changes):
    return RasterGrid(
        heights_m=heights or ((10.0, 10.0, 10.0),) * 3,
        centre_easting_m=0.0,
        centre_northing_m=2.0,
        cell_size_m=1.0,
        horizontal_crs="EPSG:27700",
        vertical_datum="synthetic_local_m",
        **changes,
    )


def test_clip_is_exact_node_window_and_alignment_fails_closed():
    a = raster()
    x, y = clip_pair(a, a, (0.0, 0.0, 1.0, 2.0))
    assert x.heights_m == ((10.0, 10.0),) * 3
    assert x == y
    with pytest.raises(ValueError, match="align"):
        clip_pair(a, replace(a, centre_easting_m=0.5), (0.0, 0.0, 1.0, 2.0))
    with pytest.raises(ValueError, match="grid nodes"):
        clip_pair(a, a, (0.1, 0.0, 1.0, 2.0))


def test_exact_bundle_matrix_preserves_metres_height_north_and_viewer():
    matrix = [[1, 0, 0, -1], [0, 1, 0, -1], [0, 0, 1, -10], [0, 0, 0, 1]]
    viewer = [[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]]
    out = import_pair(
        bundle(source_to_analysis=matrix, analysis_to_viewer=viewer), raster(), raster()
    )
    assert out.vertices_enu_m[0] == (-1.0, 1.0, 0.0)
    assert out.vertices_viewer_m[0] == (-1.0, 0.0, -1.0)
    assert len(out.triangles) == 8
    scene = out.physical_scene("target", "surface")
    assert scene["format_version"] == "canopy-physical-scene/1"
    assert scene["flat_ground_z_m"] == 0
    assert sum(s["area_m2"] for s in scene["samples"]) == 4
    assert all(s["normal_enu"] == (0, 0, 1) for s in scene["samples"])
    assert out.elapsed_seconds >= 0
    assert (
        out.content_sha256
        == import_pair(
            bundle(source_to_analysis=matrix, analysis_to_viewer=viewer), raster(), raster()
        ).content_sha256
    )
    assert out.warnings


def test_no_data_never_bridged_and_blocks_evaluation():
    dtm = raster(((None, 10.0, 10.0), (10.0, 10.0, 10.0), (10.0, 10.0, 10.0)))
    out = import_pair(bundle(), dtm, raster())
    assert out.missing_cells == ((0, 0),)
    assert len(out.triangles) == 7
    with pytest.raises(ValueError, match="no-data"):
        out.physical_scene("target", "surface")


def test_unknown_elevations_are_not_buildings_and_ground_is_not_dsm():
    dsm = raster(((14.0, 10.0, 10.0), (10.0, 10.0, 10.0), (10.0, 10.0, 10.0)))
    out = import_pair(bundle(), raster(), dsm)
    assert out.elevated_cells == ((0, 0, "unknown"),)
    assert out.vertices_enu_m[0][2] == 10
    with pytest.raises(ValueError, match="unknown"):
        out.physical_scene("target", "surface")
    with pytest.raises(ValueError, match="below"):
        import_pair(bundle(), dsm, raster())


def test_baked_vegetation_requires_state_evidence_and_no_duplicate_trees():
    dsm = raster(((14.0, 10.0, 10.0), (10.0, 10.0, 10.0), (10.0, 10.0, 10.0)))
    semantics = (("vegetation", "ground", "ground"), ("ground",) * 3, ("ground",) * 3)
    out = import_pair(bundle(), raster(), dsm, semantic_mask=semantics)
    with pytest.raises(ValueError, match="state"):
        out.physical_scene("target", "surface")
    scene = out.physical_scene("target", "surface", baked_profile_states=("summer",))
    assert scene["baked_vegetation"] == {
        "supported_profile_states": ["summer"],
        "existing_trees_separate": True,
    }
    assert len(scene["triangles"]) == 20  # 8 terrain + 12 synthetic cell-box triangles
    with pytest.raises(ValueError, match="double"):
        out.physical_scene(
            "target",
            "surface",
            baked_profile_states=("summer",),
            existing_trees=({"placement_id": "existing"},),
        )


def test_nonflat_import_preserved_but_current_evaluator_rejected():
    dtm = raster(((11.0, 10.0, 10.0), (10.0, 10.0, 10.0), (10.0, 10.0, 10.0)))
    out = import_pair(bundle(), dtm, dtm)
    assert out.vertices_enu_m[0][2] == 11
    with pytest.raises(ValueError, match="nonflat"):
        out.physical_scene("target", "surface")


@pytest.mark.parametrize(
    "change",
    [
        {"site_kind": "real_site"},
        {"source_units": "degrees"},
        {"vertical_datum": dict(name="ODN", status="known", evidence=["metadata"])},
        {
            "vertical_datum": dict(
                name="Ordnance Datum Newlyn", status="known", evidence=["metadata"]
            )
        },
    ],
)
def test_unverified_real_geodesy_units_or_odn_rejected(change):
    with pytest.raises(ValueError):
        import_pair(bundle(**change), raster(), raster())


def test_bounds_semantics_and_finite_values_rejected():
    with pytest.raises(ValueError):
        raster(((float("nan"),),))
    with pytest.raises(ValueError, match="semantic"):
        import_pair(bundle(), raster(), raster(), semantic_mask=(("ground",),))
    with pytest.raises(ValueError, match="CRS"):
        import_pair(
            bundle(),
            replace(raster(), horizontal_crs="EPSG:4326"),
            replace(raster(), horizontal_crs="EPSG:4326"),
        )


def test_import_crop_applies_identical_semantic_window_and_hash_changes():
    surface = raster(((10.0, 10.0, 14.0), (10.0, 10.0, 10.0), (10.0, 10.0, 10.0)))
    mask = (("ground", "ground", "building"), ("ground",) * 3, ("ground",) * 3)
    out = import_pair(
        bundle(), raster(), surface, bounds_xy=(1.0, 0.0, 2.0, 2.0), semantic_mask=mask
    )
    assert len(out.vertices_enu_m) == 6
    assert len(out.triangles) == 4
    assert out.elevated_cells == ((0, 1, "building"),)
    assert len(out.physical_scene("target", "planimetric")["triangles"]) == 16
    ground = import_pair(bundle(), raster(), raster(), bounds_xy=(1.0, 0.0, 2.0, 2.0))
    assert ground.content_sha256 != out.content_sha256


def test_explicit_resource_bound_and_degenerate_grid_rejected():
    with pytest.raises(ValueError, match="bound"):
        import_pair(bundle(), raster(), raster(), max_cells=8)
    with pytest.raises(ValueError, match="2x2"):
        import_pair(bundle(), raster(((10.0,),)), raster(((10.0,),)))


def test_scene_placement_and_target_validation():
    out = import_pair(bundle(), raster(), raster())
    with pytest.raises(ValueError, match="Placements"):
        out.physical_scene("target", "surface", existing_trees=({"unknown": "tree"},))
    with pytest.raises(ValueError, match="target"):
        out.physical_scene("not-target", "surface")
    with pytest.raises(ValueError, match="area basis"):
        out.physical_scene("target", "unknown")
