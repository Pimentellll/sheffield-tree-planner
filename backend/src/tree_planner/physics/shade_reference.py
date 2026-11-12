"""Synthetic-only baseline-versus-one-tree shade arithmetic for STP-010.

This is a mathematical reference, not the accepted Scenario/Result contract.
All geometry uses local ENU metres and binary opaque direct-solar visibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import isfinite

from tree_planner.physics.ray import (
    Vec3,
    ray_ellipsoid_distance,
    ray_triangle_distance,
    ray_vertical_trunk_distance,
)


@dataclass(frozen=True)
class ReceiverSample:
    point_enu_m: Vec3
    outward_normal_enu: Vec3
    area_m2: float
    target_id: str


@dataclass(frozen=True)
class DraftSolarBin:
    midpoint_utc: datetime
    duration_h: float
    direction_enu: Vec3
    above_horizon: bool


@dataclass(frozen=True)
class OpaqueEllipsoid:
    center_enu_m: Vec3
    radii_m: Vec3


@dataclass(frozen=True)
class OpaqueTrunk:
    center_east_m: float
    center_north_m: float
    base_up_m: float
    radius_m: float
    height_m: float


@dataclass(frozen=True)
class StaticTriangle:
    vertices_enu_m: tuple[Vec3, Vec3, Vec3]


Obstacle = OpaqueEllipsoid | OpaqueTrunk | StaticTriangle


@dataclass(frozen=True)
class ProposedTree:
    crown: OpaqueEllipsoid
    trunk: OpaqueTrunk


@dataclass(frozen=True)
class DraftShadeCalculation:
    baseline_direct_sun_m2_h: float
    proposal_direct_sun_m2_h: float
    additional_useful_shade_m2_h: float
    sample_count: int
    bin_count: int


def _validate(
    samples: tuple[ReceiverSample, ...],
    bins: tuple[DraftSolarBin, ...],
    ray_offset_m: float,
) -> None:
    if not samples or not bins:
        raise ValueError("synthetic reference needs samples and bins")
    if not isfinite(ray_offset_m) or ray_offset_m <= 0:
        raise ValueError("ray offset must be finite and positive")
    previous_end = None
    for sample in samples:
        if not sample.target_id or not isfinite(sample.area_m2) or sample.area_m2 <= 0:
            raise ValueError("target and represented physical area are required")
        if len(sample.point_enu_m) != 3 or not all(
            isfinite(v) for v in sample.point_enu_m
        ):
            raise ValueError("receiver position must be a finite ENU point")
        normal = sample.outward_normal_enu
        if (
            len(normal) != 3
            or not all(isfinite(v) for v in normal)
            or abs(sum(v * v for v in normal) - 1) > 1e-9
        ):
            raise ValueError("receiver normal must be finite and unit length")
    for bin_ in bins:
        if (
            bin_.midpoint_utc.tzinfo is None
            or bin_.midpoint_utc.utcoffset() != timedelta(0)
        ):
            raise ValueError("bin midpoint must be UTC")
        if not isfinite(bin_.duration_h) or bin_.duration_h <= 0:
            raise ValueError("bin duration must be finite and positive")
        direction = bin_.direction_enu
        if (
            len(direction) != 3
            or not all(isfinite(v) for v in direction)
            or abs(sum(v * v for v in direction) - 1) > 1e-9
        ):
            raise ValueError("sun direction must be finite and unit length")
        half = timedelta(hours=bin_.duration_h / 2)
        start, end = bin_.midpoint_utc - half, bin_.midpoint_utc + half
        if previous_end is not None and start < previous_end:
            raise ValueError("draft midpoint-centred bins overlap or are unsorted")
        previous_end = end


def _hit(
    origin: Vec3, direction: Vec3, obstacle: Obstacle, min_distance: float
) -> bool:
    if isinstance(obstacle, OpaqueEllipsoid):
        distance = ray_ellipsoid_distance(
            origin,
            direction,
            obstacle.center_enu_m,
            obstacle.radii_m,
            min_distance=min_distance,
        )
    elif isinstance(obstacle, OpaqueTrunk):
        distance = ray_vertical_trunk_distance(
            origin,
            direction,
            obstacle.center_east_m,
            obstacle.center_north_m,
            obstacle.base_up_m,
            obstacle.radius_m,
            obstacle.height_m,
            min_distance=min_distance,
        )
    elif isinstance(obstacle, StaticTriangle):
        distance = ray_triangle_distance(
            origin, direction, obstacle.vertices_enu_m, min_distance=min_distance
        )
    else:
        raise TypeError("unsupported synthetic obstacle")
    return distance is not None


def evaluate_one_tree_synthetic(
    samples: tuple[ReceiverSample, ...],
    bins: tuple[DraftSolarBin, ...],
    baseline_obstacles: tuple[Obstacle, ...],
    proposed_tree: ProposedTree,
    *,
    ray_offset_m: float = 1e-6,
) -> DraftShadeCalculation:
    """Evaluate both scenes on exactly the same receiver/bin rays."""
    _validate(samples, bins, ray_offset_m)
    if not isinstance(proposed_tree, ProposedTree):
        raise TypeError("exactly one proposed tree is required")
    # Validate geometry even if every bin is night or back-facing.
    for obstacle in (*baseline_obstacles, proposed_tree.crown, proposed_tree.trunk):
        _hit((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), obstacle, ray_offset_m)
    baseline_sun = 0.0
    proposal_sun = 0.0
    for bin_ in bins:
        if not bin_.above_horizon:
            continue
        for sample in samples:
            if (
                sum(
                    a * b for a, b in zip(sample.outward_normal_enu, bin_.direction_enu)
                )
                <= 0
            ):
                continue
            origin = tuple(
                p + ray_offset_m * n
                for p, n in zip(sample.point_enu_m, sample.outward_normal_enu)
            )
            baseline_hit = any(
                _hit(origin, bin_.direction_enu, obstacle, ray_offset_m)
                for obstacle in baseline_obstacles
            )
            if baseline_hit:
                continue
            contribution = sample.area_m2 * bin_.duration_h
            baseline_sun += contribution
            tree_hit = _hit(
                origin, bin_.direction_enu, proposed_tree.crown, ray_offset_m
            ) or _hit(origin, bin_.direction_enu, proposed_tree.trunk, ray_offset_m)
            if not tree_hit:
                proposal_sun += contribution
    return DraftShadeCalculation(
        baseline_direct_sun_m2_h=baseline_sun,
        proposal_direct_sun_m2_h=proposal_sun,
        additional_useful_shade_m2_h=baseline_sun - proposal_sun,
        sample_count=len(samples),
        bin_count=len(bins),
    )
