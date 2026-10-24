"""Terrain lookup via USGS 3DEP (free, no key) for snow-persistence scoring.

USGS 3DEP ImageServer computes elevation, slope, and aspect as server-side
functions, so we don't have to do DEM math ourselves:
  https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer

Why terrain matters for snow PERSISTENCE (how long snow survives, not just falls):
  * elevation  - higher = more snowfall, colder, slower melt
  * slope+aspect - north-facing shaded slopes (N hemisphere) get less sun => survive longer
These are real, defensible effects. For a flat urban pile (e.g. Boston Seaport) terrain matters
little and INSULATION dominates; terrain scoring is for REGIONAL site selection.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass

import requests

_IMG = (
    "https://elevation.nationalmap.gov/arcgis/rest/services/"
    "3DEPElevation/ImageServer/identify"
)


@dataclass(frozen=True)
class Terrain:
    lat: float
    lon: float
    elevation_m: float
    slope_deg: float
    aspect_deg: float  # 0=N, 90=E, 180=S, 270=W


def _identify(lat: float, lon: float, render_rule: str | None, timeout: float) -> float | None:
    geometry = (
        '{"x":%s,"y":%s,"spatialReference":{"wkid":4326}}' % (lon, lat)
    )
    params = {
        "geometry": geometry,
        "geometryType": "esriGeometryPoint",
        "returnGeometry": "false",
        "f": "json",
    }
    if render_rule:
        params["renderingRule"] = render_rule

    last_exc: Exception | None = None
    for _ in range(3):  # USGS occasionally returns a transient 502
        try:
            r = requests.get(_IMG, params=params, timeout=timeout)
            r.raise_for_status()
            val = r.json().get("value")
            try:
                return float(val)
            except (TypeError, ValueError):
                return None  # "NoData" etc.
        except requests.HTTPError as exc:
            last_exc = exc
            if exc.response is not None and exc.response.status_code in (429, 502, 503):
                time.sleep(0.6)
                continue
            raise
    if last_exc:
        raise last_exc
    return None


def fetch_terrain(lat: float, lon: float, timeout: float = 30.0) -> Terrain:
    """Query elevation, slope, and aspect for a point from USGS 3DEP."""
    elevation = _identify(lat, lon, None, timeout) or 0.0
    slope = _identify(lat, lon, '{"rasterFunction":"Slope Degrees"}', timeout)
    aspect = _identify(lat, lon, '{"rasterFunction":"Aspect Degrees"}', timeout)
    return Terrain(
        lat=lat,
        lon=lon,
        elevation_m=elevation,
        slope_deg=slope if slope is not None else 0.0,
        aspect_deg=aspect if aspect is not None else 0.0,
    )


def northness(aspect_deg: float) -> float:
    """1.0 for due north, 0.0 for due south. North-facing slopes hold snow longer.

    cos(aspect) is +1 at N (0 deg) and -1 at S (180 deg); map to 0..1.
    """
    return (math.cos(math.radians(aspect_deg)) + 1.0) / 2.0
