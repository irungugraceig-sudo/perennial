"""Snowfall forecast via the US National Weather Service (api.weather.gov).

NWS is free, no API key, requires a User-Agent header. Flow:
  1. /points/{lat},{lon}      -> resolves the forecast grid for a location
  2. /gridpoints/{wfo}/{x},{y} -> raw grid data incl. `snowfallAmount` (mm, time-series)
  3. /gridpoints/.../forecast  -> human-readable day/night periods (temp + conditions)

Honest note: NWS forecasts extend ~7 days. This is true short-range PREDICTION (what you asked
for). For long-range "how much will a whole season give us," use climate normals (siting view) —
a forecast cannot see months ahead.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests

USER_AGENT = "Perennial/0.1 (Hackachusetts hackathon; contact: team)"
MM_TO_METER = 0.001


@dataclass(frozen=True)
class ForecastDay:
    name: str
    temperature_f: float
    short_forecast: str
    is_daytime: bool


@dataclass(frozen=True)
class SnowForecast:
    lat: float
    lon: float
    upcoming_snow_mm: float          # total forecast snowfall over the window
    upcoming_snow_meters: float
    periods: list[ForecastDay]


def _get(url: str, timeout: float) -> dict:
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def fetch_snow_forecast(lat: float, lon: float, days: int = 7, timeout: float = 30.0) -> SnowForecast:
    """Fetch upcoming snowfall + day/night periods for a location.

    `days` trims how many forecast periods (day/night) are returned: ~2 periods per day.
    """
    points = _get(f"https://api.weather.gov/points/{lat},{lon}", timeout)
    props = points["properties"]
    grid_url = f"https://api.weather.gov/gridpoints/{props['gridId']}/{props['gridX']},{props['gridY']}"

    # Raw grid: sum the snowfallAmount series (mm).
    grid = _get(grid_url, timeout)
    snow_mm = 0.0
    sa = grid["properties"].get("snowfallAmount")
    if sa and sa.get("values"):
        for v in sa["values"]:
            val = v.get("value")
            if val is not None:
                snow_mm += float(val)

    # Human-readable periods (~2 per day). Trim to the requested window.
    fc = _get(props["forecast"], timeout)
    n_periods = max(2, min(14, days * 2))
    periods = [
        ForecastDay(
            name=p["name"],
            temperature_f=float(p["temperature"]),
            short_forecast=p["shortForecast"],
            is_daytime=bool(p["isDaytime"]),
        )
        for p in fc["properties"]["periods"][:n_periods]
    ]

    return SnowForecast(
        lat=lat,
        lon=lon,
        upcoming_snow_mm=round(snow_mm, 1),
        upcoming_snow_meters=round(snow_mm * MM_TO_METER, 4),
        periods=periods,
    )
