"""Snow Persistence Score: rank candidate sites for snow-cooling viability.

A transparent, weighted score (0-1) combining real factors. Weights are explicit
inputs, never hidden. Higher score = better place to collect/store snow and site a
snow-cooled data center.

Factors (each normalized 0-1):
  * snowfall        - more seasonal snow (supply)            [from NOAA normals]
  * elevation       - higher = colder, slower melt           [from USGS 3DEP]
  * northness       - north-facing slopes survive longer     [from USGS aspect]
  * slope_gentle    - gentle slopes hold a pile; steep sheds  [from USGS slope]
  * demand_proximity- closer to a data center = usable cold   [computed]
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .terrain import northness


@dataclass(frozen=True)
class ScoreWeights:
    snowfall: float = 0.35
    elevation: float = 0.15
    northness: float = 0.20
    slope_gentle: float = 0.10
    demand_proximity: float = 0.20


@dataclass(frozen=True)
class Candidate:
    name: str
    lat: float
    lon: float
    snowfall_m: float
    elevation_m: float
    slope_deg: float
    aspect_deg: float
    distance_km_to_demand: float


@dataclass(frozen=True)
class ScoredCandidate:
    name: str
    lat: float
    lon: float
    score: float
    factors: dict[str, float] = field(default_factory=dict)


def _norm(value: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def score_candidate(c: Candidate, w: ScoreWeights | None = None) -> ScoredCandidate:
    w = w or ScoreWeights()

    f_snow = _norm(c.snowfall_m, 0.0, 3.0)          # 0..3 m seasonal
    f_elev = _norm(c.elevation_m, 0.0, 500.0)       # 0..500 m
    f_north = northness(c.aspect_deg)               # 0..1
    f_slope = 1.0 - _norm(c.slope_deg, 0.0, 30.0)   # gentle better than steep
    f_prox = 1.0 - _norm(c.distance_km_to_demand, 0.0, 50.0)  # closer better

    total_w = (
        w.snowfall + w.elevation + w.northness + w.slope_gentle + w.demand_proximity
    )
    raw = (
        w.snowfall * f_snow
        + w.elevation * f_elev
        + w.northness * f_north
        + w.slope_gentle * f_slope
        + w.demand_proximity * f_prox
    )
    score = raw / total_w if total_w else 0.0

    return ScoredCandidate(
        name=c.name,
        lat=c.lat,
        lon=c.lon,
        score=round(score, 3),
        factors={
            "snowfall": round(f_snow, 3),
            "elevation": round(f_elev, 3),
            "northness": round(f_north, 3),
            "slope_gentle": round(f_slope, 3),
            "demand_proximity": round(f_prox, 3),
        },
    )
