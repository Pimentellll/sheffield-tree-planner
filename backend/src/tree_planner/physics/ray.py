"""Provisional analytic CPU ray intersections for synthetic STP-009 checks.

All coordinates and distances are local ENU metres. Rays use unit directions.
An intersection at or below min_distance is excluded as a self hit.
"""

from __future__ import annotations

from math import copysign, isfinite, sqrt

Vec3 = tuple[float, float, float]


def _vec(value: Vec3) -> None:
    if len(value) != 3 or not all(isfinite(v) for v in value):
        raise ValueError("expected three finite ENU metre components")


def _ray(origin: Vec3, direction: Vec3, min_distance: float) -> None:
    _vec(origin)
    _vec(direction)
    if abs(sum(v * v for v in direction) - 1) > 1e-9:
        raise ValueError("ray direction must be a unit vector")
    if not isfinite(min_distance) or min_distance < 0:
        raise ValueError("min_distance must be nonnegative and finite")


def _positive_roots(
    a: float, b: float, c: float, minimum: float, tolerance: float
) -> tuple[float, ...]:
    discriminant = b * b - 4 * a * c
    if discriminant < -tolerance:
        return ()
    root = sqrt(max(0.0, discriminant))
    if root == 0:
        roots = (-b / (2 * a),)
    else:
        q = -0.5 * (b + copysign(root, b))
        roots = (q / a, c / q) if q != 0 else (-b / (2 * a),)
    return tuple(sorted(t for t in roots if t > minimum))


def ray_ellipsoid_distance(
    origin: Vec3,
    direction: Vec3,
    center: Vec3,
    radii: Vec3,
    *,
    min_distance: float = 1e-9,
    discriminant_tolerance: float = 1e-12,
) -> float | None:
    """First forward ray hit of an axis-aligned opaque ellipsoid, including tangency."""
    _ray(origin, direction, min_distance)
    _vec(center)
    _vec(radii)
    if any(r <= 0 for r in radii):
        raise ValueError("ellipsoid radii must be positive")
    if not isfinite(discriminant_tolerance) or discriminant_tolerance < 0:
        raise ValueError("discriminant tolerance must be nonnegative and finite")
    offset = tuple((o - c) / r for o, c, r in zip(origin, center, radii))
    scaled = tuple(d / r for d, r in zip(direction, radii))
    a = sum(v * v for v in scaled)
    b = 2 * sum(o * d for o, d in zip(offset, scaled))
    c = sum(v * v for v in offset) - 1
    roots = _positive_roots(a, b, c, min_distance, discriminant_tolerance)
    return roots[0] if roots else None


def ray_vertical_trunk_distance(
    origin: Vec3,
    direction: Vec3,
    center_east_m: float,
    center_north_m: float,
    base_up_m: float,
    radius_m: float,
    height_m: float,
    *,
    min_distance: float = 1e-9,
) -> float | None:
    """First hit of a closed finite vertical cylinder, including side and caps."""
    _ray(origin, direction, min_distance)
    if not all(
        isfinite(v)
        for v in (center_east_m, center_north_m, base_up_m, radius_m, height_m)
    ):
        raise ValueError("trunk geometry must be finite")
    if radius_m <= 0 or height_m <= 0:
        raise ValueError("trunk radius and height must be positive")
    x, y = origin[0] - center_east_m, origin[1] - center_north_m
    dx, dy, dz = direction
    candidates = []
    a = dx * dx + dy * dy
    if a > 1e-24:
        roots = _positive_roots(
            a,
            2 * (x * dx + y * dy),
            x * x + y * y - radius_m * radius_m,
            min_distance,
            1e-12,
        )
        for t in roots:
            z = origin[2] + t * dz
            if base_up_m <= z <= base_up_m + height_m:
                candidates.append(t)
    if abs(dz) > 1e-12:
        for cap in (base_up_m, base_up_m + height_m):
            t = (cap - origin[2]) / dz
            if (
                t > min_distance
                and (x + t * dx) ** 2 + (y + t * dy) ** 2 <= radius_m * radius_m + 1e-12
            ):
                candidates.append(t)
    return min(candidates) if candidates else None


def ray_triangle_distance(
    origin: Vec3,
    direction: Vec3,
    vertices: tuple[Vec3, Vec3, Vec3],
    *,
    min_distance: float = 1e-9,
    tolerance: float = 1e-12,
) -> float | None:
    """Double-sided ray/triangle hit; degenerate triangles have no blocking area."""
    _ray(origin, direction, min_distance)
    if len(vertices) != 3:
        raise ValueError("triangle needs three vertices")
    for vertex in vertices:
        _vec(vertex)
    if not isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be nonnegative and finite")

    def subtract(a: Vec3, b: Vec3) -> Vec3:
        return tuple(x - y for x, y in zip(a, b))

    def cross(a: Vec3, b: Vec3) -> Vec3:
        return (
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0],
        )

    def dot(a: Vec3, b: Vec3) -> float:
        return sum(x * y for x, y in zip(a, b))

    v0, v1, v2 = vertices
    edge1, edge2 = subtract(v1, v0), subtract(v2, v0)
    p = cross(direction, edge2)
    det = dot(edge1, p)
    if abs(det) <= tolerance:
        return None
    inv = 1 / det
    s = subtract(origin, v0)
    u = inv * dot(s, p)
    if u < -tolerance or u > 1 + tolerance:
        return None
    q = cross(s, edge1)
    v = inv * dot(direction, q)
    if v < -tolerance or u + v > 1 + tolerance:
        return None
    t = inv * dot(edge2, q)
    return t if t > min_distance else None
