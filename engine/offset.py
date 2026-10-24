"""Offset accounting: what snow cooling saves vs. conventional evaporative cooling.

Conventional path dumps heat via evaporative cooling towers:
  * evaporates fresh water (gone forever) -> WUE liters/kWh
  * runs chillers -> electricity -> grid CO2

Perennial path dumps the same heat into melting snow:
  * no evaporation (meltwater is spent coolant, not consumed product)
  * no chiller electricity for the offset fraction (the cold is free)

So for each kWh of cooling delivered by snow, we avoid both the tower water AND
the chiller electricity (and its CO2).
"""

from __future__ import annotations

from dataclasses import dataclass

from .constants import LITERS_PER_GALLON


@dataclass(frozen=True)
class OffsetResult:
    cooling_delivered_kwh: float
    fresh_water_saved_liters: float
    fresh_water_saved_gallons: float
    chiller_energy_avoided_kwh: float
    co2_avoided_kg: float


def compute_offset(
    cooling_delivered_kwh: float,
    wue_l_per_kwh: float,
    chiller_cop: float,
    grid_co2_kg_per_kwh: float,
) -> OffsetResult:
    """Translate delivered cooling into resources saved.

    Args:
        cooling_delivered_kwh: cooling (heat rejection) provided by snow.
        wue_l_per_kwh: baseline evaporative water use, liters per kWh of cooling.
        chiller_cop: coefficient of performance of the chiller we displace
            (kWh cooling per kWh electricity). Typical ~3-5.
        grid_co2_kg_per_kwh: carbon intensity of the displaced electricity.
    """
    if cooling_delivered_kwh < 0:
        raise ValueError("cooling_delivered_kwh must be non-negative")
    if wue_l_per_kwh < 0:
        raise ValueError("wue must be non-negative")
    if chiller_cop <= 0:
        raise ValueError("chiller_cop must be positive")
    if grid_co2_kg_per_kwh < 0:
        raise ValueError("grid_co2 must be non-negative")

    water_l = cooling_delivered_kwh * wue_l_per_kwh
    chiller_kwh = cooling_delivered_kwh / chiller_cop
    co2_kg = chiller_kwh * grid_co2_kg_per_kwh

    return OffsetResult(
        cooling_delivered_kwh=cooling_delivered_kwh,
        fresh_water_saved_liters=water_l,
        fresh_water_saved_gallons=water_l / LITERS_PER_GALLON,
        chiller_energy_avoided_kwh=chiller_kwh,
        co2_avoided_kg=co2_kg,
    )


def fraction_of_demand_offset(cooling_delivered_kwh: float, cooling_demand_kwh: float) -> float:
    """What share of the data center's cooling demand the snow covers (0-1, capped).

    HONEST: snow cooling is seasonal and finite. Report a fraction, never "100%".
    """
    if cooling_delivered_kwh < 0 or cooling_demand_kwh < 0:
        raise ValueError("inputs must be non-negative")
    if cooling_demand_kwh == 0:
        return 0.0
    return min(1.0, cooling_delivered_kwh / cooling_demand_kwh)
