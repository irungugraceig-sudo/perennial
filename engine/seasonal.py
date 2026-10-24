"""Monthly supply-vs-demand model: the peak-shaving story.

The point of Perennial is NOT "snow replaces all cooling." It is "snow shaves the
summer PEAK" -- the hot weeks (July/Aug) when evaporative towers drink the most
fresh water and the grid is most stressed (cf. ISO New England summer peak and the
portal's C3 challenge: clean power still has to show up at the peak).

Phase shift: cold is COLLECTED in winter (when you don't need it) and SPENT in
summer (when demand peaks). This module produces the two monthly curves and the
pile trajectory so the UI can show a timeline slider from January to August.
"""

from __future__ import annotations

from dataclasses import dataclass

from .constants import COOLING_KWH_PER_TONNE_ICE

# Relative cooling-demand shape by month (1=Jan .. 12=Dec). Peaks in summer.
# Normalized so the 12 values average ~1.0; scaled by annual demand.
COOLING_DEMAND_SHAPE: list[float] = [
    0.55, 0.55, 0.65, 0.80, 1.05, 1.35,  # Jan..Jun
    1.55, 1.55, 1.20, 0.90, 0.70, 0.60,  # Jul..Dec
]

# Months when snow is collected into the pile (Dec..Mar in Boston).
COLLECTION_MONTHS = {12, 1, 2, 3}


@dataclass(frozen=True)
class MonthPoint:
    month: int                 # 1-12
    demand_kwh: float          # cooling demand that month
    snow_supply_kwh: float     # cold delivered from the pile that month
    pile_mass_tonnes: float    # pile remaining at month end
    offset_pct: float          # share of that month's demand covered by snow


@dataclass(frozen=True)
class SeasonModel:
    months: list[MonthPoint]
    annual_demand_kwh: float
    annual_snow_kwh: float
    peak_month_offset_pct: float   # offset in the single peak-demand month (the hero number)


def _monthly_demand(annual_demand_kwh: float) -> list[float]:
    total_shape = sum(COOLING_DEMAND_SHAPE)
    return [annual_demand_kwh * s / total_shape for s in COOLING_DEMAND_SHAPE]


def build_season(
    annual_demand_kwh: float,
    collected_mass_kg: float,
    passive_loss_fraction: float = 0.25,
    delivery_ratio: float = 0.765,   # heat-exchanger effectiveness * (1 - fouling)
) -> SeasonModel:
    """Walk the year month by month, filling the pile in winter and drawing in summer."""
    demand = _monthly_demand(annual_demand_kwh)
    usable_mass = collected_mass_kg * (1.0 - passive_loss_fraction)

    pile_kwh = 0.0
    total_collect_kwh = (usable_mass / 1000.0) * COOLING_KWH_PER_TONNE_ICE
    per_collection_month = total_collect_kwh / len(COLLECTION_MONTHS)

    points: list[MonthPoint] = []
    peak_offset = 0.0
    peak_demand = max(demand)

    for m in range(1, 13):
        d = demand[m - 1]
        # Collect in winter months.
        if m in COLLECTION_MONTHS:
            pile_kwh += per_collection_month
        # Draw cold to meet this month's demand (capped by what's in the pile).
        drawn = min(pile_kwh, d * delivery_ratio)
        pile_kwh -= drawn
        offset = (drawn / d * 100.0) if d > 0 else 0.0
        if abs(d - peak_demand) < 1e-9:
            peak_offset = offset
        points.append(
            MonthPoint(
                month=m,
                demand_kwh=d,
                snow_supply_kwh=drawn,
                pile_mass_tonnes=(pile_kwh / COOLING_KWH_PER_TONNE_ICE),
                offset_pct=round(offset, 1),
            )
        )

    return SeasonModel(
        months=points,
        annual_demand_kwh=annual_demand_kwh,
        annual_snow_kwh=sum(p.snow_supply_kwh for p in points),
        peak_month_offset_pct=round(peak_offset, 1),
    )
