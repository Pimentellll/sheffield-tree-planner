"""Analytic ENU intersections, derived from PR43's ray equations.

Repairs: intersections return positive interior path lengths for volumetric
occluders; tangent contact is not attenuation. Scale-normalised coefficients
avoid a fixed discriminant tolerance that changes meaning with metre scale.
"""

from math import isfinite, sqrt, ulp

Vec3 = tuple[float, float, float]


def _vec(v):
    if len(v) != 3 or not all(isfinite(x) for x in v):
        raise ValueError("expected three finite ENU components")


def _ray(origin, direction):
    _vec(origin)
    _vec(direction)
    if abs(sum(x * x for x in direction) - 1) > 1e-9:
        raise ValueError("direction must be a unit vector")


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def ellipsoid_path_length(origin, direction, center, radii):
    """Forward interior length in metres; inside origin clips entry to zero."""
    _ray(origin, direction)
    _vec(center)
    _vec(radii)
    if any(r <= 0 for r in radii):
        raise ValueError("radii must be positive")
    p = tuple((o - c) / r for o, c, r in zip(origin, center, radii))
    v = tuple(d / r for d, r in zip(direction, radii))
    speed = sqrt(_dot(v, v))
    unit = tuple(x / speed for x in v)
    middle = -_dot(p, unit)
    nearest = tuple(x + middle * d for x, d in zip(p, unit))
    radial = 1 - _dot(nearest, nearest)
    if radial <= 0:
        return 0.0
    half = sqrt(radial)
    return max(0.0, (middle + half - max(0.0, middle - half)) / speed)


def trunk_path_length(
    origin, direction, center_east_m, center_north_m, base_up_m, radius_m, height_m
):
    """Forward interior length in a finite vertical closed cylinder."""
    _ray(origin, direction)
    if (
        not all(isfinite(x) for x in (center_east_m, center_north_m, base_up_m, radius_m, height_m))
        or radius_m <= 0
        or height_m <= 0
    ):
        raise ValueError("trunk dimensions must be finite and positive")
    x, y = (origin[0] - center_east_m) / radius_m, (origin[1] - center_north_m) / radius_m
    dx, dy, dz = direction
    speed = sqrt(dx * dx + dy * dy)
    lo, hi = 0.0, float("inf")
    if speed == 0:
        if x * x + y * y >= 1:
            return 0.0
    else:
        ux, uy = dx / speed, dy / speed
        middle = -(x * ux + y * uy)
        radial = 1 - (x + middle * ux) ** 2 - (y + middle * uy) ** 2
        if radial <= 0:
            return 0.0
        half = sqrt(radial)
        lo = max(lo, (middle - half) * radius_m / speed)
        hi = min(hi, (middle + half) * radius_m / speed)
    if dz == 0:
        if not base_up_m < origin[2] < base_up_m + height_m:
            return 0.0
    else:
        a, b = sorted(((base_up_m - origin[2]) / dz, (base_up_m + height_m - origin[2]) / dz))
        lo = max(lo, a)
        hi = min(hi, b)
    return max(0.0, hi - lo)


def ray_triangle_distance(origin, direction, vertices, *, min_distance=0.0, tolerance=None):
    """Double-sided Moller-Trumbore, with dimensionless roundoff tolerance.

    No metric origin displacement: an originating triangle is excluded by identity
    in the evaluator. Thus a separate thin surface is never skipped by ray_offset.
    """
    _ray(origin, direction)
    if len(vertices) != 3 or not isfinite(min_distance) or min_distance < 0:
        raise ValueError("invalid triangle or min_distance")
    for v in vertices:
        _vec(v)
    e1, e2 = _sub(vertices[1], vertices[0]), _sub(vertices[2], vertices[0])
    scale = max(*(abs(x) for x in e1), *(abs(x) for x in e2))
    if scale == 0:
        return None
    e1, e2 = tuple(x / scale for x in e1), tuple(x / scale for x in e2)
    p = _cross(direction, e2)
    det = _dot(e1, p)
    eps = 32 * ulp(1.0) if tolerance is None else tolerance
    if not isfinite(eps) or eps < 0:
        raise ValueError("invalid triangle tolerance")
    if abs(det) <= eps:
        return None
    delta = tuple(x / scale for x in _sub(origin, vertices[0]))
    u = _dot(delta, p) / det
    q = _cross(delta, e1)
    v = _dot(direction, q) / det
    if u < -eps or v < -eps or u + v > 1 + eps:
        return None
    t = scale * _dot(e2, q) / det
    return t if t > min_distance else None


def point_on_triangle(point, vertices):
    """Strict roundoff-scale originating-triangle membership, not user offset."""
    e1, e2 = _sub(vertices[1], vertices[0]), _sub(vertices[2], vertices[0])
    n = _cross(e1, e2)
    norm = sqrt(_dot(n, n))
    if norm == 0:
        return False
    unit = tuple(x / norm for x in n)
    scale = max(1.0, *(abs(x) for v in vertices for x in v), *(abs(x) for x in point))
    eps = 32 * ulp(scale)
    if abs(_dot(_sub(point, vertices[0]), unit)) > eps:
        return False
    # Barycentric projection independently verifies finite triangle membership.
    p = _sub(point, vertices[0])
    a, b, c = _dot(e1, e1), _dot(e1, e2), _dot(e2, e2)
    denom = a * c - b * b
    if denom <= 0:
        return False
    u = (c * _dot(p, e1) - b * _dot(p, e2)) / denom
    v = (a * _dot(p, e2) - b * _dot(p, e1)) / denom
    return u >= -32 * ulp(1.0) and v >= -32 * ulp(1.0) and u + v <= 1 + 32 * ulp(1.0)
