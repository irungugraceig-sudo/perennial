"""Impact view + expansion planner: AI growth and what snow could offset.

Two forward-looking calculations:
  * expansion planner - a single facility adds load by a target year; how much extra cooling and
    water, and how much snow could cover.
  * impact projection  - AI data-center water demand rising to 2030 vs. a snow-offset ceiling.

Growth figures are adjustable and anchored to real sources (see HACKATHON_CONTEXT.md):
  * DC electricity could reach ~11.8% of US by 2030 (LBNL/DOE).
  * Global DC capacity ~22% CAGR; generative-AI workloads ~39% CAGR (industry).
"""

from __future__ import annotations

from dataclasses import dataclass

from .constants import LITERS_PER_GALLON


@dataclass(frozen=True)
class ExpansionResult:
    base_it_kw: float
    target_it_kw: float
    added_it_kw: float
    added_cooling_mwh_yr: float
    added_water_gallons_yr: float
    snow_coverable_pct: float   # share of the ADDED cooling snow could cover


def plan_expansion(
    base_it_kw: float,
    added_it_kw: float,
    pue: float,
    cooling_fraction: float,
    wue_l_per_kwh: float,
    snow_cooling_kwh_available: float,
) -> ExpansionResult:
    if base_it_kw < 0 or added_it_kw < 0:
        raise ValueError("loads must be non-negative")
    target = base_it_kw + added_it_kw
    added_cooling_kw = added_it_kw * pue * cooling_fraction
    added_cooling_kwh = added_cooling_kw * 24 * 365
    added_it_kwh = added_it_kw * 24 * 365
    added_water_l = added_it_kwh * wue_l_per_kwh
    cover = 0.0
    if added_cooling_kwh > 0:
        cover = min(1.0, snow_cooling_kwh_available / added_cooling_kwh)
    return ExpansionResult(
        base_it_kw=base_it_kw,
        target_it_kw=target,
        added_it_kw=added_it_kw,
        added_cooling_mwh_yr=added_cooling_kwh / 1000,
        added_water_gallons_yr=added_water_l / LITERS_PER_GALLON,
        snow_coverable_pct=round(cover * 100, 1),
    )


@dataclass(frozen=True)
class ProjectionYear:
    year: int
    demand_index: float          # relative AI cooling-water demand (base year = 1.0)
    water_gallons: float
    snow_offset_gallons: float
    offset_pct: float


def project_impact(
    base_year: int,
    end_year: int,
    base_water_gallons: float,
    cagr_pct: float,
    snow_offset_gallons: float,
) -> list[ProjectionYear]:
    """Project water demand forward at a growth rate; overlay a fixed snow-offset ceiling."""
    out: list[ProjectionYear] = []
    g = cagr_pct / 100.0
    for y in range(base_year, end_year + 1):
        n = y - base_year
        water = base_water_gallons * ((1 + g) ** n)
        offset = min(snow_offset_gallons, water)
        out.append(ProjectionYear(
            year=y,
            demand_index=round((1 + g) ** n, 3),
            water_gallons=round(water, 0),
            snow_offset_gallons=round(offset, 0),
            offset_pct=round((offset / water * 100) if water else 0.0, 1),
        ))
    return out
