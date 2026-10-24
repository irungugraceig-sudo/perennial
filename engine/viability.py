"""Viability verdict: ties snow supply + heat exchanger + footprint into one report.

This is the Schneider-TradeOff-Tools-style answer: given a data center and a
location's snow, is snow cooling viable, and what does it offset?
"""

from __future__ import annotations

from dataclasses import dataclass

from .cooling import HeatExchanger
from .interfaces import DataCenterFootprint
from .offset import OffsetResult, compute_offset, fraction_of_demand_offset
from .piles import SnowPile, total_available_cooling_kwh


@dataclass(frozen=True)
class ViabilityReport:
    footprint_name: str
    annual_cooling_demand_kwh: float
    cooling_delivered_kwh: float
    fraction_offset: float
    offset: OffsetResult
    verdict: str


def _verdict(fraction: float) -> str:
    if fraction >= 0.5:
        return "Strong: snow cooling can offset a major share of cooling demand."
    if fraction >= 0.2:
        return "Viable: meaningful seasonal offset; pairs with conventional cooling."
    if fraction > 0.0:
        return "Marginal: modest offset; best as a supplement during peak-snow months."
    return "Not viable with current inputs."


def assess(
    footprint: DataCenterFootprint,
    piles: list[SnowPile],
    exchanger: HeatExchanger | None = None,
    chiller_cop: float = 4.0,
) -> ViabilityReport:
    exchanger = exchanger or HeatExchanger()

    pile_cold_kwh = total_available_cooling_kwh(piles)
    delivered_kwh = exchanger.deliverable_cooling_kwh(pile_cold_kwh)

    # Annual cooling demand (heat to reject) from the footprint.
    annual_cooling_demand_kwh = footprint.cooling_power_kw * 24.0 * 365.0

    fraction = fraction_of_demand_offset(delivered_kwh, annual_cooling_demand_kwh)
    # Only the offset portion counts toward savings.
    effective_cooling = min(delivered_kwh, annual_cooling_demand_kwh)

    offset = compute_offset(
        cooling_delivered_kwh=effective_cooling,
        wue_l_per_kwh=footprint.wue_l_per_kwh,
        chiller_cop=chiller_cop,
        grid_co2_kg_per_kwh=footprint.grid_co2_kg_per_kwh,
    )

    return ViabilityReport(
        footprint_name=footprint.name,
        annual_cooling_demand_kwh=annual_cooling_demand_kwh,
        cooling_delivered_kwh=effective_cooling,
        fraction_offset=fraction,
        offset=offset,
        verdict=_verdict(fraction),
    )
