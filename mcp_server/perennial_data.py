"""Perennial Data MCP server.

Wraps the three public data sources Perennial depends on — NOAA (snowfall),
NWS (forecast), and USGS 3DEP (terrain) — as Model Context Protocol tools so
Kiro (and any MCP client) can explore and validate data during development.

This is the MCP layer behind the "we extended Kiro to pull NOAA/NWS/USGS data"
story: the same engine functions the app uses are exposed here as agent tools.

Run (stdio):  python -m mcp_server.perennial_data
Register in .kiro/settings/mcp.json (see repo docs).
"""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from engine.forecast import fetch_snow_forecast
from engine.noaa import BOSTON_LOGAN_GHCND, fetch_seasonal_snowfall
from engine.predictor import get_predictor, season_total_water_equivalent_m
from engine.seasonal import COLLECTION_MONTHS
from engine.terrain import fetch_terrain

mcp = MCPServer("perennial-data")


@mcp.tool()
def noaa_seasonal_snowfall(start: str, end: str, station: str = "USW00014739") -> dict:
    """Total observed snowfall for a station between two dates (NOAA GHCN-Daily via ACIS).

    Args:
        start: start date YYYY-MM-DD
        end: end date YYYY-MM-DD
        station: GHCN station id (default Boston Logan)
    """
    s = fetch_seasonal_snowfall(start=start, end=end, station=station)
    return {
        "station": s.station,
        "start": s.start,
        "end": s.end,
        "total_inches": round(s.total_inches, 2),
        "total_meters": round(s.total_meters, 4),
        "days_counted": s.days_counted,
    }


@mcp.tool()
def nws_snow_forecast(lat: float, lon: float) -> dict:
    """Upcoming snowfall + day/night periods for a location (US National Weather Service)."""
    f = fetch_snow_forecast(lat=lat, lon=lon)
    return {
        "upcoming_snow_mm": f.upcoming_snow_mm,
        "upcoming_snow_meters": f.upcoming_snow_meters,
        "periods": [
            {"name": p.name, "temp_f": p.temperature_f, "short": p.short_forecast}
            for p in f.periods
        ],
    }


@mcp.tool()
def predict_seasonal_snowfall(station: str = BOSTON_LOGAN_GHCND) -> dict:
    """ML-predicted monthly snowfall for a station, as an expected +/- band (meters).

    This is the seasonal PREDICTION layer (quantile gradient-boosted model trained
    on NOAA history) — the planning answer that observed history and the 7-day
    forecast cannot give. Also returns the season-total water-equivalent depth
    over the winter collection months.

    Args:
        station: GHCN station id (default Boston Logan).
    """
    predictor = get_predictor()
    year = predictor.predict_year(station)
    season_we_m = season_total_water_equivalent_m(
        predictor, station, sorted(COLLECTION_MONTHS)
    )
    return {
        "station": station,
        "model": predictor.name,
        "collection_months": sorted(COLLECTION_MONTHS),
        "season_water_equivalent_m": round(season_we_m, 4),
        "months": [
            {
                "month": p.month,
                "expected_m": round(p.expected_m, 4),
                "low_m": round(p.low_m, 4),
                "high_m": round(p.high_m, 4),
            }
            for p in year
        ],
    }


@mcp.tool()
def usgs_terrain(lat: float, lon: float) -> dict:
    """Elevation, slope, and aspect for a point (USGS 3DEP). Drives snow-persistence scoring."""
    t = fetch_terrain(lat=lat, lon=lon)
    return {
        "elevation_m": round(t.elevation_m, 1),
        "slope_deg": round(t.slope_deg, 1),
        "aspect_deg": round(t.aspect_deg, 1),
    }


if __name__ == "__main__":
    mcp.run()
