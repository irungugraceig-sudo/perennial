"""Real snowfall data for Perennial via the ACIS API (NOAA GHCN-Daily).

ACIS (Applied Climate Information System, https://www.rcc-acis.org/) serves
NOAA GHCN-Daily records for free with no API key. We pull seasonal snowfall for
a station (default: Boston Logan, GHCND:USW00014739).

Snowfall in GHCN is element "snow" (SNOW), reported in inches by default here;
we convert to meters for the engine (SI internally).

Honest note: this is OBSERVED historical snowfall. Climate NORMALS (30-yr averages)
are a separate ACIS/NCEI product used for siting/projection; this module is the
"what actually fell" source that seeds live piles.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests

ACIS_URL = "https://data.rcc-acis.org/StnData"
BOSTON_LOGAN_GHCND = "USW00014739"
INCH_TO_METER = 0.0254


@dataclass(frozen=True)
class SeasonSnowfall:
    station: str
    start: str          # YYYY-MM-DD
    end: str            # YYYY-MM-DD
    total_inches: float
    total_meters: float
    days_counted: int


@dataclass(frozen=True)
class MonthlySnowfall:
    """One month's observed snowfall total for a station (meters, SI)."""

    station: str
    year: int
    month: int          # 1-12
    snow_inches: float
    snow_meters: float
    latitude: float
    elevation_m: float


def fetch_monthly_snowfall(
    start_month: str,
    end_month: str,
    station: str = BOSTON_LOGAN_GHCND,
    timeout: float = 60.0,
) -> list[MonthlySnowfall]:
    """Fetch monthly snowfall totals for a station over a range (NOAA GHCN via ACIS).

    Args:
        start_month, end_month: "YYYY-MM" (inclusive).
        station: GHCN station id (default Boston Logan).

    Returns one MonthlySnowfall per month. Station latitude/elevation come from
    the ACIS metadata so the predictor's geographic features are real, not guessed.
    "T" (trace) counts as ~0; "M"/"S"/missing months are skipped.
    """
    payload = {
        "sid": station,
        "sdate": start_month,
        "edate": end_month,
        "elems": [{"name": "snow", "interval": "mly", "duration": "mly", "reduce": "sum"}],
    }
    resp = requests.post(ACIS_URL, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    meta = data.get("meta", {})
    ll = meta.get("ll", [None, None])
    latitude = float(ll[1]) if ll and ll[1] is not None else 42.3606
    elevation_ft = meta.get("elev")
    # ACIS elevation is in feet; convert to meters. Fall back to Logan's ~3-6 m.
    elevation_m = float(elevation_ft) * 0.3048 if elevation_ft is not None else 3.4

    out: list[MonthlySnowfall] = []
    for ym, value in data.get("data", []):
        try:
            year_s, month_s = ym.split("-")
            year, month = int(year_s), int(month_s)
        except (ValueError, AttributeError):
            continue
        if value in ("M", "S", None):
            continue          # missing month: skip entirely
        inches = 0.0 if value == "T" else _safe_float(value)
        if inches is None:
            continue
        out.append(
            MonthlySnowfall(
                station=station,
                year=year,
                month=month,
                snow_inches=inches,
                snow_meters=inches * INCH_TO_METER,
                latitude=latitude,
                elevation_m=elevation_m,
            )
        )
    return out


def _safe_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_seasonal_snowfall(
    start: str,
    end: str,
    station: str = BOSTON_LOGAN_GHCND,
    timeout: float = 30.0,
) -> SeasonSnowfall:
    """Fetch total snowfall between two dates (inclusive) for a GHCN station.

    Args:
        start, end: "YYYY-MM-DD".
        station: GHCN station id (default Boston Logan).

    Returns SeasonSnowfall with totals in inches and meters.
    """
    payload = {
        "sid": station,
        "sdate": start,
        "edate": end,
        "elems": [{"name": "snow", "interval": "dly"}],
    }
    resp = requests.post(ACIS_URL, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    total_in = 0.0
    counted = 0
    for _date, value in data.get("data", []):
        # ACIS uses "M" (missing) and "T" (trace) markers.
        if value in ("M", "S", None):
            continue
        if value == "T":
            counted += 1  # trace counts as a day, adds ~0
            continue
        try:
            total_in += float(value)
            counted += 1
        except (TypeError, ValueError):
            continue

    return SeasonSnowfall(
        station=station,
        start=start,
        end=end,
        total_inches=total_in,
        total_meters=total_in * INCH_TO_METER,
        days_counted=counted,
    )
