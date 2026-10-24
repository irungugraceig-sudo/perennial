"""Daily ice availability and the water it saves.

For a chosen day, given how much usable ice the stored pile holds, compute:
  * how much of that ice we can draw in one day (limited by the facility's daily
    cooling demand), and
  * the fresh water that one day of snow cooling saves (vs. evaporative towers).

This answers "when we get the ice, how much can we use today, and how much water
does that save?"
"""

from __future__ import annotations

from dataclasses import dataclass

from .constants import COOLING_KWH_PER_TONNE_ICE, KJ_PER_KWH, LATENT_HEAT_FUSION_ICE_KJ_PER_KG, LITERS_PER_GALLON


@dataclass(frozen=True)
class DailyIce:
    usable_ice_tonnes: float            # ice available in the pile
    daily_cooling_demand_kwh: float     # facility's heat to reject in a day
    ice_used_today_tonnes: float        # ice melted today to meet demand
    cooling_delivered_kwh: float        # cooling that ice provided today
    water_saved_gallons_today: float    # fresh water not evaporated today
    days_of_cooling_remaining: float    # how long the pile lasts at this draw


def daily_ice_use(
    usable_ice_tonnes: float,
    cooling_power_kw: float,
    wue_l_per_kwh: float,
    delivery_ratio: float = 0.765,
) -> DailyIce:
    if usable_ice_tonnes < 0 or cooling_power_kw < 0 or wue_l_per_kwh < 0:
        raise ValueError("inputs must be non-negative")

    daily_demand_kwh = cooling_power_kw * 24.0
    pile_cooling_kwh = usable_ice_tonnes * COOLING_KWH_PER_TONNE_ICE * delivery_ratio

    delivered = min(daily_demand_kwh, pile_cooling_kwh)
    # Ice melted to deliver that cooling (back out the delivery ratio).
    ice_kg = (delivered / delivery_ratio) * KJ_PER_KWH / LATENT_HEAT_FUSION_ICE_KJ_PER_KG if delivery_ratio else 0.0
    water_l = delivered * wue_l_per_kwh
    days_remaining = (pile_cooling_kwh / daily_demand_kwh) if daily_demand_kwh else 0.0

    return DailyIce(
        usable_ice_tonnes=usable_ice_tonnes,
        daily_cooling_demand_kwh=daily_demand_kwh,
        ice_used_today_tonnes=ice_kg / 1000.0,
        cooling_delivered_kwh=delivered,
        water_saved_gallons_today=water_l / LITERS_PER_GALLON,
        days_of_cooling_remaining=days_remaining,
    )
