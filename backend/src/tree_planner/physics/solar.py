"""Solar/time utilities reused from PR37 a80745d; explicit elevation repair."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import cos, isfinite, radians, sin, sqrt
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class SolarDirection:
    azimuth_deg: float
    elevation_deg: float
    enu: tuple[float, float, float]
    above_horizon: bool


@dataclass(frozen=True)
class DraftTimeBin:
    """Provisional midpoint-centred interval, pending STP-002 serialization."""

    midpoint_utc: datetime
    duration_h: float


def _require_utc(instant: datetime) -> None:
    if (
        not isinstance(instant, datetime)
        or instant.tzinfo is None
        or instant.utcoffset() != timedelta(0)
    ):
        raise ValueError("timestamp must be timezone-aware UTC")


def local_to_utc(local: datetime, zone_name: str = "Europe/London") -> datetime:
    """Resolve a wall time only when it identifies exactly one real instant."""
    if not isinstance(local, datetime) or local.tzinfo is not None:
        raise ValueError("local timestamp must be naive wall time")
    zone = ZoneInfo(zone_name)
    candidates = set()
    for fold in (0, 1):
        aware = local.replace(tzinfo=zone, fold=fold)
        utc = aware.astimezone(UTC)
        if utc.astimezone(zone).replace(tzinfo=None) == local:
            candidates.add(utc)
    if len(candidates) != 1:
        raise ValueError("local timestamp is ambiguous or nonexistent")
    return candidates.pop()


def validate_time_bins(bins: tuple[DraftTimeBin, ...] | list[DraftTimeBin]) -> None:
    """Check sorted, non-overlapping midpoint-centred draft intervals."""
    previous_end = None
    for item in bins:
        _require_utc(item.midpoint_utc)
        if not isfinite(item.duration_h) or item.duration_h <= 0:
            raise ValueError("duration_h must be finite and positive")
        half = timedelta(hours=item.duration_h / 2)
        start, end = item.midpoint_utc - half, item.midpoint_utc + half
        if previous_end is not None and start < previous_end:
            raise ValueError("time bins overlap or are not sorted")
        previous_end = end


def direction_from_angles(azimuth_deg: float, elevation_deg: float) -> SolarDirection:
    """Convert true-north clockwise azimuth and horizon elevation to ENU."""
    if not all(isfinite(v) for v in (azimuth_deg, elevation_deg)):
        raise ValueError("solar angles must be finite")
    if not 0 <= azimuth_deg < 360 or not -90 <= elevation_deg <= 90:
        raise ValueError("solar angles out of range")
    azimuth, elevation = radians(azimuth_deg), radians(elevation_deg)
    vector = (
        cos(elevation) * sin(azimuth),
        cos(elevation) * cos(azimuth),
        sin(elevation),
    )
    norm = sqrt(sum(v * v for v in vector))
    return SolarDirection(
        azimuth_deg, elevation_deg, tuple(v / norm for v in vector), elevation_deg > 0
    )


def solar_direction_enu(
    latitude_deg: float, longitude_deg: float, instant_utc: datetime, *, altitude_m: float = 0.0
) -> SolarDirection:
    """Geometric SPA rays; altitude explicit, delta-T fixed 67s assumption.

    Atmospheric refraction is deliberately not applied to direct geometric rays.
    Use solar_position for explicit geometric/apparent reference comparison.
    """
    position = solar_position(latitude_deg, longitude_deg, instant_utc, altitude_m=altitude_m)
    return direction_from_angles(position.azimuth_deg, position.geometric_elevation_deg)


def direct_incidence(
    direction: SolarDirection, outward_normal_enu: tuple[float, float, float]
) -> float:
    """Return nonnegative cosine of incidence, with night and back faces at zero."""
    if len(outward_normal_enu) != 3 or not all(isfinite(v) for v in outward_normal_enu):
        raise ValueError("normal must contain three finite ENU components")
    norm = sqrt(sum(v * v for v in outward_normal_enu))
    if abs(norm - 1) > 1e-9:
        raise ValueError("normal must be a unit vector")
    if not direction.above_horizon:
        return 0.0
    return max(0.0, sum(a * b for a, b in zip(direction.enu, outward_normal_enu)))


@dataclass(frozen=True)
class SolarPosition:
    """Both elevation conventions, never compared as if identical."""

    azimuth_deg: float
    geometric_elevation_deg: float
    apparent_elevation_deg: float


def solar_position(
    latitude_deg,
    longitude_deg,
    instant_utc,
    *,
    altitude_m=0.0,
    pressure_pa=101325.0,
    temperature_c=12.0,
    delta_t_s=67.0,
):
    _require_utc(instant_utc)
    if not all(
        isfinite(x)
        for x in (latitude_deg, longitude_deg, altitude_m, pressure_pa, temperature_c, delta_t_s)
    ):
        raise ValueError("solar parameters must be finite")
    if (
        not -90 <= latitude_deg <= 90
        or not -180 <= longitude_deg <= 180
        or pressure_pa < 0
        or temperature_c <= -273.15
    ):
        raise ValueError("invalid solar parameters")
    import pandas as pd
    from pvlib.solarposition import spa_python

    result = spa_python(
        pd.DatetimeIndex([instant_utc]),
        latitude_deg,
        longitude_deg,
        altitude=altitude_m,
        pressure=pressure_pa,
        temperature=temperature_c,
        delta_t=delta_t_s,
        how="numpy",
    ).iloc[0]
    return SolarPosition(
        float(result["azimuth"]), float(result["elevation"]), float(result["apparent_elevation"])
    )
