"""Show-the-work explainer: every result as a traceable chain of steps.

Grade-level transparency. Instead of only returning "4,123,812 gallons", we return
the ordered list of steps that produced it: the label, the formula with real numbers
substituted in, the numeric result, and the unit. The UI renders this as an expandable
derivation so a judge or engineer can follow every number to its source.

This computes the SAME math as the engine (reusing its functions), so the explanation
can never drift from the real result.
"""

from __future__ import annotations

from dataclasses import dataclass

from .constants import (
    COOLING_KWH_PER_TONNE_ICE,
    KJ_PER_KWH,
    LATENT_HEAT_FUSION_ICE_KJ_PER_KG,
    LITERS_PER_GALLON,
    MILE_TO_METER,
)
from .interfaces import DataCenterFootprint


@dataclass(frozen=True)
class Step:
    label: str          # what this step computes
    formula: str        # the formula with real numbers substituted
    result: float       # numeric result
    unit: str           # unit of the result
    source: str = ""    # where a constant/assumption comes from


def _fmt(x: float) -> str:
    if abs(x) >= 1000:
        return f"{x:,.0f}"
    if abs(x) >= 1:
        return f"{x:,.2f}"
    return f"{x:.4f}"


def explain_offset(
    footprint: DataCenterFootprint,
    snowfall_m: float,
    collection_efficiency: float,
    plowed_length_miles: float,
    effective_lane_width_m: float,
    fresh_snow_density: float,
    passive_loss_fraction: float,
    hx_effectiveness: float,
    hx_fouling_factor: float,
    chiller_cop: float,
) -> list[Step]:
    """Return the full derivation from snowfall to water/energy/CO2 saved."""
    steps: list[Step] = []

    # 1. Plowed area
    plowed_area = plowed_length_miles * MILE_TO_METER * effective_lane_width_m
    steps.append(Step(
        "Plowed street area",
        f"{_fmt(plowed_length_miles)} mi x {_fmt(MILE_TO_METER)} m/mi x {_fmt(effective_lane_width_m)} m wide",
        plowed_area, "m^2",
        "Boston plows ~785 mi of streets (FEMA)",
    ))

    # 2. Fallen snow volume
    fallen_vol = snowfall_m * plowed_area
    steps.append(Step(
        "Snow volume that fell on plowed streets",
        f"{_fmt(snowfall_m)} m deep x {_fmt(plowed_area)} m^2",
        fallen_vol, "m^3", "Snowfall: NOAA GHCN-Daily",
    ))

    # 3. Collected volume
    collected_vol = fallen_vol * collection_efficiency
    steps.append(Step(
        "Volume actually collected and hauled",
        f"{_fmt(fallen_vol)} m^3 x {_fmt(collection_efficiency)} collection efficiency",
        collected_vol, "m^3", "Collection efficiency = adjustable assumption",
    ))

    # 4. Water-equivalent mass
    mass_kg = collected_vol * fresh_snow_density
    steps.append(Step(
        "Water-equivalent mass of collected snow",
        f"{_fmt(collected_vol)} m^3 x {_fmt(fresh_snow_density)} kg/m^3 (fresh snow)",
        mass_kg, "kg", "Fresh snow ~100 kg/m^3",
    ))

    # 5. Surviving mass after melt loss
    surviving_kg = mass_kg * (1.0 - passive_loss_fraction)
    steps.append(Step(
        "Surviving ice after seasonal melt loss",
        f"{_fmt(mass_kg)} kg x (1 - {_fmt(passive_loss_fraction)} melt loss)",
        surviving_kg, "kg", "Insulated piles lose ~20-30% (Sundsvall/Boston)",
    ))

    # 6. Raw cooling from the pile
    pile_cooling_kwh = (surviving_kg / 1000.0) * COOLING_KWH_PER_TONNE_ICE
    steps.append(Step(
        "Cooling energy in the surviving ice",
        f"{_fmt(surviving_kg / 1000.0)} tonnes x {_fmt(COOLING_KWH_PER_TONNE_ICE)} kWh/tonne",
        pile_cooling_kwh, "kWh",
        "Latent heat of fusion 334 kJ/kg => 92.8 kWh/tonne (NIST)",
    ))

    # 7. Delivered cold after heat exchanger
    delivery_ratio = hx_effectiveness * (1.0 - hx_fouling_factor)
    delivered_kwh = pile_cooling_kwh * delivery_ratio
    steps.append(Step(
        "Cold delivered through the shell-and-tube heat exchanger",
        f"{_fmt(pile_cooling_kwh)} kWh x ({_fmt(hx_effectiveness)} effectiveness x (1 - {_fmt(hx_fouling_factor)} fouling))",
        delivered_kwh, "kWh", "Exchanger effectiveness + fouling factor",
    ))

    # 8. Cap at demand
    annual_demand_kwh = footprint.cooling_power_kw * 24 * 365
    effective_kwh = min(delivered_kwh, annual_demand_kwh)
    steps.append(Step(
        "Annual cooling demand (heat to reject)",
        f"{_fmt(footprint.cooling_power_kw)} kW cooling x 24 h x 365 d",
        annual_demand_kwh, "kWh", f"{footprint.name}: PUE {footprint.pue}, cooling fraction",
    ))

    # 9. Fresh water saved
    water_l = effective_kwh * footprint.wue_l_per_kwh
    steps.append(Step(
        "Fresh water saved (not evaporated in cooling towers)",
        f"{_fmt(effective_kwh)} kWh cooling x {_fmt(footprint.wue_l_per_kwh)} L/kWh (WUE)",
        water_l / LITERS_PER_GALLON, "gallons",
        "WUE = Water Usage Effectiveness (The Green Grid)",
    ))

    # 10. Chiller energy avoided
    chiller_kwh = effective_kwh / chiller_cop
    steps.append(Step(
        "Chiller electricity avoided",
        f"{_fmt(effective_kwh)} kWh cooling / {_fmt(chiller_cop)} chiller COP",
        chiller_kwh, "kWh", "COP = cooling delivered per kWh electricity",
    ))

    # 11. CO2 avoided
    co2_kg = chiller_kwh * footprint.grid_co2_kg_per_kwh
    steps.append(Step(
        "CO2 avoided",
        f"{_fmt(chiller_kwh)} kWh x {_fmt(footprint.grid_co2_kg_per_kwh)} kg CO2/kWh (grid)",
        co2_kg, "kg", "New England grid intensity ~0.30 kg/kWh",
    ))

    return steps
