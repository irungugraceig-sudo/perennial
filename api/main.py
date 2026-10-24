"""FastAPI layer exposing the Perennial engine to the frontend.

Run:  uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import math

from engine.cooling import HeatExchanger
from engine.datacenters import DATA_CENTERS, by_name
from engine.forecast import fetch_snow_forecast
from engine.hotspots import Candidate, ScoreWeights, score_candidate
from engine.interfaces import DataCenterFootprint
from engine.metrics import ICE_KG_PER_LITER_WATER, compute_dashboard
from engine.noaa import BOSTON_LOGAN_GHCND, fetch_seasonal_snowfall
from engine.piles import SnowPile
from engine.predictor import get_predictor, season_total_water_equivalent_m
from engine.projection import plan_expansion, project_impact
from engine.seasonal import COLLECTION_MONTHS, build_season
from engine.sites import BOSTON_SNOW_FARMS
from engine.snow import CollectionInputs, collected_mass_empirical, collected_mass_geometric
from engine.terrain import fetch_terrain
from engine.viability import assess

app = FastAPI(title="Perennial API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- schemas ----------
class FootprintIn(BaseModel):
    name: str = "Markley - One Summer Street, Boston"
    it_load_kw: float = 2000.0
    pue: float = 1.5
    wue_l_per_kwh: float = 1.8
    cooling_fraction: float = 0.33
    grid_co2_kg_per_kwh: float = 0.30


class AssessIn(BaseModel):
    datacenter: str | None = None          # name from /datacenters; overrides footprint if set
    footprint: FootprintIn = Field(default_factory=FootprintIn)
    snowfall_m: float = 2.809              # default: 2014-15 Boston record
    # If set, derive snowfall_m from the ML predictor instead of the fixed value
    # above. This answers "how much can we EXPECT next winter" rather than
    # replaying one historical season.
    use_prediction: bool = False
    predict_station: str = BOSTON_LOGAN_GHCND
    collection_efficiency: float = 0.12
    effective_lane_width_m: float = 11.0
    storms_per_season: float = 6.0
    passive_loss_fraction: float = 0.25
    hx_effectiveness: float = 0.85
    hx_fouling_factor: float = 0.1
    chiller_cop: float = 4.0


# ---------- routes ----------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/sites")
def sites():
    return [
        {"name": s.name, "lat": s.latitude, "lon": s.longitude, "note": s.note}
        for s in BOSTON_SNOW_FARMS
    ]


@app.get("/datacenters")
def datacenters():
    return [
        {
            "name": d.name, "operator": d.operator, "city": d.city,
            "lat": d.latitude, "lon": d.longitude, "note": d.note,
            "kind": d.kind, "gpu_heavy": d.gpu_heavy,
            "it_load_kw": d.it_load_kw, "pue": d.pue,
            "wue_l_per_kwh": d.wue_l_per_kwh, "cooling_fraction": d.cooling_fraction,
            "grid_co2_kg_per_kwh": d.grid_co2_kg_per_kwh,
        }
        for d in DATA_CENTERS
    ]


class ExpansionIn(BaseModel):
    datacenter: str = "One Summer Street"
    added_it_kw: float = 5000.0
    snow_cooling_mwh_available: float = 3000.0


@app.post("/expansion")
def expansion(body: ExpansionIn):
    dc = by_name(body.datacenter)
    r = plan_expansion(
        base_it_kw=dc.it_load_kw,
        added_it_kw=body.added_it_kw,
        pue=dc.pue,
        cooling_fraction=dc.cooling_fraction,
        wue_l_per_kwh=dc.wue_l_per_kwh,
        snow_cooling_kwh_available=body.snow_cooling_mwh_available * 1000,
    )
    return {
        "base_it_kw": r.base_it_kw,
        "target_it_kw": r.target_it_kw,
        "added_it_kw": r.added_it_kw,
        "added_cooling_mwh_yr": round(r.added_cooling_mwh_yr, 0),
        "added_water_gallons_yr": round(r.added_water_gallons_yr, 0),
        "snow_coverable_pct": r.snow_coverable_pct,
    }


class ImpactIn(BaseModel):
    base_year: int = 2025
    end_year: int = 2030
    base_water_gallons: float = 17_000_000_000  # US DC direct water ~17B gal (2023)
    cagr_pct: float = 22.0                        # DC capacity CAGR
    snow_offset_gallons: float = 2_000_000_000


@app.post("/impact")
def impact(body: ImpactIn):
    years = project_impact(
        base_year=body.base_year,
        end_year=body.end_year,
        base_water_gallons=body.base_water_gallons,
        cagr_pct=body.cagr_pct,
        snow_offset_gallons=body.snow_offset_gallons,
    )
    return [
        {"year": y.year, "water_gallons": y.water_gallons,
         "snow_offset_gallons": y.snow_offset_gallons, "offset_pct": y.offset_pct}
        for y in years
    ]


@app.get("/forecast")
def forecast(lat: float = 42.3601, lon: float = -71.0589, range: str = "week"):
    """Snow outlook. range = 'day' | 'week' (live NWS) or 'month' (NOAA historical same month)."""
    days = {"day": 1, "week": 7, "month": 14}.get(range, 7)

    # Live NWS forecast (always try — gives temps/conditions and near-term snow).
    try:
        f = fetch_snow_forecast(lat=lat, lon=lon, days=days)
        periods = [
            {"name": p.name, "temp_f": p.temperature_f, "short": p.short_forecast, "day": p.is_daytime}
            for p in f.periods
        ]
        forecast_mm = f.upcoming_snow_mm
    except Exception:
        periods, forecast_mm = [], 0.0

    result = {
        "range": range,
        "lat": lat, "lon": lon,
        "forecast_snow_mm": forecast_mm,
        "periods": periods,
        "historical": None,
    }

    # For a month view (or when there's no live snow), add a NOAA historical figure
    # for the same calendar month from the most recent full winter on record.
    if range == "month" or forecast_mm == 0.0:
        import datetime
        today = datetime.date.today()
        # Use the same month last year as a representative historical window.
        y = today.year - 1
        m = today.month
        start = f"{y}-{m:02d}-01"
        end_m = m + 1
        end_y = y
        if end_m > 12:
            end_m, end_y = 1, y + 1
        end = f"{end_y}-{end_m:02d}-01"
        try:
            s = fetch_seasonal_snowfall(start=start, end=end)
            result["historical"] = {
                "label": f"{start} to {end} (NOAA Boston Logan)",
                "snow_inches": round(s.total_inches, 1),
                "snow_mm": round(s.total_meters * 1000, 1),
            }
        except Exception:
            result["historical"] = None

    return result


def _haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class HotspotIn(BaseModel):
    # candidate points to score: list of {name, lat, lon, snowfall_m}
    candidates: list[dict]
    demand_lat: float = 42.3539
    demand_lon: float = -71.0598
    weights: dict | None = None


@app.post("/hotspots")
def hotspots(body: HotspotIn):
    w = ScoreWeights(**body.weights) if body.weights else ScoreWeights()
    results = []
    for cand in body.candidates:
        lat = float(cand["lat"])
        lon = float(cand["lon"])
        try:
            t = fetch_terrain(lat, lon)
        except Exception:
            t = None
        dist = _haversine_km(lat, lon, body.demand_lat, body.demand_lon)
        c = Candidate(
            name=cand.get("name", "candidate"),
            lat=lat,
            lon=lon,
            snowfall_m=float(cand.get("snowfall_m", 1.5)),
            elevation_m=(t.elevation_m if t else 0.0),
            slope_deg=(t.slope_deg if t else 0.0),
            aspect_deg=(t.aspect_deg if t else 0.0),
            distance_km_to_demand=dist,
        )
        s = score_candidate(c, w)
        results.append({
            "name": s.name, "lat": s.lat, "lon": s.lon,
            "score": s.score, "factors": s.factors,
            "elevation_m": round(c.elevation_m, 1),
            "slope_deg": round(c.slope_deg, 1),
            "aspect_deg": round(c.aspect_deg, 1),
            "distance_km": round(dist, 1),
        })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


@app.get("/snowfall")
def snowfall(start: str, end: str, station: str = "USW00014739"):
    s = fetch_seasonal_snowfall(start=start, end=end, station=station)
    return {
        "station": s.station,
        "start": s.start,
        "end": s.end,
        "total_inches": round(s.total_inches, 2),
        "total_meters": round(s.total_meters, 4),
        "days_counted": s.days_counted,
    }


@app.get("/predict-snowfall")
def predict_snowfall(station: str = BOSTON_LOGAN_GHCND):
    """ML-predicted monthly snowfall for a station, as an expected +/- band.

    Answers the planning question ("how much snow can we expect this winter")
    that observed history (/snowfall) and the 7-day forecast (/forecast) cannot.
    Depths in meters; also returns the season-total water-equivalent depth over
    the collection months, which /assess can consume with use_prediction=true.
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


def _footprint_for(name: str | None) -> DataCenterFootprint:
    """Build a DataCenterFootprint from a known DC name (or the default)."""
    dc = by_name(name) if name else DATA_CENTERS[0]
    return DataCenterFootprint(
        name=f"{dc.operator} - {dc.name}, {dc.city}",
        it_load_kw=dc.it_load_kw,
        pue=dc.pue,
        wue_l_per_kwh=dc.wue_l_per_kwh,
        cooling_fraction=dc.cooling_fraction,
        grid_co2_kg_per_kwh=dc.grid_co2_kg_per_kwh,
    )


@app.get("/metrics")
def metrics(datacenter: str | None = None, ai_growth_factor: float = 1.8):
    """Dashboard headline metrics for a data center.

    - Water usage (daily + yearly, liters + gallons)
    - Heat dissipated per day (the cooling load)
    - Projected AI-driven water increase (ai_growth_factor: 1.0 = flat, 1.8 = +80%)
    - Snow required (COOLING-EQUIVALENCE) to offset today's and projected water
    """
    fp = _footprint_for(datacenter)
    m = compute_dashboard(fp, ai_growth_factor=ai_growth_factor)

    def snow(s):
        return {
            "water_liters": round(s.water_liters, 0),
            "ice_tonnes": round(s.ice_tonnes, 0),
            "snow_m3_fresh": round(s.snow_m3_fresh, 0),
            "snow_m3_packed": round(s.snow_m3_packed, 0),
            "ice_m3_solid": round(s.ice_m3_solid, 0),
            "snow_m3_water_content_fresh": round(s.snow_m3_water_content_fresh, 0),
        }

    return {
        "site": m.site,
        "heat_dissipated_mwh_per_day": round(m.heat_rejected_mwh_per_day, 1),
        "heat_dissipated_kwh_per_day": round(m.heat_rejected_kwh_per_day, 0),
        "cooling_power_kw": round(m.cooling_power_kw, 0),
        "water_liters_per_day": round(m.water_liters_per_day, 0),
        "water_gallons_per_day": round(m.water_gallons_per_day, 0),
        "water_liters_per_year": round(m.water_liters_per_year, 0),
        "water_gallons_per_year": round(m.water_gallons_per_year, 0),
        "ai_growth_factor": m.ai_growth_factor,
        "projected_water_gallons_per_year": round(m.projected_water_gallons_per_year, 0),
        "projected_water_gallons_per_day": round(m.projected_water_gallons_per_day, 0),
        "extra_water_gallons_per_year": round(m.extra_water_gallons_per_year, 0),
        "ice_kg_per_liter_water": round(ICE_KG_PER_LITER_WATER, 3),
        "snow_today": snow(m.snow_today),
        "snow_projected": snow(m.snow_projected),
    }


@app.post("/assess")
def do_assess(body: AssessIn):
    if body.datacenter:
        dc = by_name(body.datacenter)
        footprint = DataCenterFootprint(
            name=f"{dc.operator} - {dc.name}, {dc.city}",
            it_load_kw=dc.it_load_kw,
            pue=dc.pue,
            wue_l_per_kwh=dc.wue_l_per_kwh,
            cooling_fraction=dc.cooling_fraction,
            grid_co2_kg_per_kwh=dc.grid_co2_kg_per_kwh,
        )
        dc_coords = {"lat": dc.latitude, "lon": dc.longitude}
    else:
        fp = body.footprint
        footprint = DataCenterFootprint(
            name=fp.name,
            it_load_kw=fp.it_load_kw,
            pue=fp.pue,
            wue_l_per_kwh=fp.wue_l_per_kwh,
            cooling_fraction=fp.cooling_fraction,
            grid_co2_kg_per_kwh=fp.grid_co2_kg_per_kwh,
        )
        dc_coords = {"lat": 42.3539, "lon": -71.0598}

    # Snowfall depth: either the fixed input, or derived from the ML prediction.
    snowfall_m = body.snowfall_m
    prediction_info = None
    if body.use_prediction:
        predictor = get_predictor()
        we_m = season_total_water_equivalent_m(
            predictor, body.predict_station, sorted(COLLECTION_MONTHS)
        )
        # CollectionInputs expects raw SNOW depth (it applies fresh-snow density);
        # convert the water-equivalent depth back to snow depth via the ratio.
        from engine.predictor import DEFAULT_SNOW_TO_LIQUID_RATIO

        snowfall_m = we_m * DEFAULT_SNOW_TO_LIQUID_RATIO
        prediction_info = {
            "station": body.predict_station,
            "model": predictor.name,
            "season_water_equivalent_m": round(we_m, 4),
            "derived_snowfall_m": round(snowfall_m, 4),
        }

    geo = CollectionInputs(
        snowfall_m=snowfall_m,
        collection_efficiency=body.collection_efficiency,
        effective_lane_width_m=body.effective_lane_width_m,
    )
    mass_geo = collected_mass_geometric(geo)
    mass_emp = collected_mass_empirical(
        cubic_yards_per_storm=89_000, storms_per_season=body.storms_per_season
    )

    # Distribute geometric mass across the known farm sites.
    n = len(BOSTON_SNOW_FARMS)
    per_site = mass_geo / n if n else 0.0
    piles = [
        SnowPile(
            site_name=s.name,
            latitude=s.latitude,
            longitude=s.longitude,
            initial_mass_kg=per_site,
            passive_loss_fraction=body.passive_loss_fraction,
        )
        for s in BOSTON_SNOW_FARMS
    ]

    report = assess(
        footprint=footprint,
        piles=piles,
        exchanger=HeatExchanger(
            effectiveness=body.hx_effectiveness,
            fouling_factor=body.hx_fouling_factor,
        ),
        chiller_cop=body.chiller_cop,
    )

    # Seasonal model for the peak-shaving story + timeline slider.
    season = build_season(
        annual_demand_kwh=report.annual_cooling_demand_kwh,
        collected_mass_kg=mass_geo,
        passive_loss_fraction=body.passive_loss_fraction,
        delivery_ratio=body.hx_effectiveness * (1.0 - body.hx_fouling_factor),
    )

    # Per-facility TOTAL consumption (the baseline for its carbon footprint).
    annual_it_kwh = footprint.it_load_kw * 24 * 365
    total_energy_mwh = footprint.total_power_kw * 24 * 365 / 1000
    total_water_gal = footprint.annual_water_liters / 3.78541
    total_co2_tonnes = (footprint.total_power_kw * 24 * 365) * footprint.grid_co2_kg_per_kwh / 1000

    return {
        "site": report.footprint_name,
        "datacenter_coords": dc_coords,
        "consumption": {
            "total_energy_mwh_yr": round(total_energy_mwh, 0),
            "total_water_gal_yr": round(total_water_gal, 0),
            "total_co2_tonnes_yr": round(total_co2_tonnes, 0),
            "annual_cooling_demand_mwh": round(report.annual_cooling_demand_kwh / 1000, 0),
        },
        "snowfall_m_used": round(snowfall_m, 4),
        "prediction": prediction_info,     # non-null when use_prediction=true
        "peak_month_offset_pct": season.peak_month_offset_pct,
        "season": [
            {"month": p.month, "demand_mwh": round(p.demand_kwh / 1000, 1),
             "snow_mwh": round(p.snow_supply_kwh / 1000, 1),
             "pile_tonnes": round(p.pile_mass_tonnes, 0),
             "offset_pct": p.offset_pct}
            for p in season.months
        ],
        "collected_tonnes_geometric": round(mass_geo / 1000, 0),
        "collected_tonnes_empirical": round(mass_emp / 1000, 0),
        "annual_cooling_demand_mwh": round(report.annual_cooling_demand_kwh / 1000, 0),
        "cooling_delivered_mwh": round(report.cooling_delivered_kwh / 1000, 0),
        "fraction_offset_pct": round(report.fraction_offset * 100, 1),
        "fresh_water_saved_gallons": round(report.offset.fresh_water_saved_gallons, 0),
        "chiller_energy_avoided_mwh": round(report.offset.chiller_energy_avoided_kwh / 1000, 0),
        "co2_avoided_tonnes": round(report.offset.co2_avoided_kg / 1000, 1),
        "verdict": report.verdict,
        "piles": [
            {"name": p.site_name, "lat": p.latitude, "lon": p.longitude,
             "tonnes": round(p.current_mass_kg / 1000, 0)}
            for p in piles
        ],
    }
