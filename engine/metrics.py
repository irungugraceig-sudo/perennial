"""Dashboard metrics for the Perennial UI.

Compiles the headline numbers the app surfaces for a Boston data center:

  1. Water usage                 - fresh water consumed for cooling (per day / year)
  2. Heat dissipated (daily)     - heat the facility rejects each day (the cooling load)
  3. Daily water usage           - liters & gallons per day (a called-out subset of #1)
  4. AI-driven water increase    - projected rise in water use as AI load grows
  5. Snow required               - via COOLING-EQUIVALENCE: how much ice/snow is needed
                                   to reject the same heat the evaporated water rejects.

Metric 5 uses "Interpretation A" (cooling equivalence), the project's real thesis:
the snow does not substitute for the water as a substance - it removes the need for
the EVAPORATIVE cooling that consumes the water. We relate them through the heat each
mechanism moves:

    evaporating 1 kg (1 L) of water rejects ~2260 kJ  (latent heat of vaporisation)
    melting     1 kg of ice   absorbs    ~334  kJ     (latent heat of fusion)
    => 1 L of cooling water avoided  ~=  2260 / 334  ~=  6.77 kg of ice melted

Everything is SI internally; display units (gallons, m^3) are derived at the edge.
"""

from __future__ import annotations

from dataclasses import dataclass

from .constants import (
    DENSITY_FRESH_SNOW,
    DENSITY_ICE,
    DENSITY_PACKED_PILE,
    LATENT_HEAT_FUSION_ICE_KJ_PER_KG,
    LATENT_HEAT_VAPORISATION_WATER_KJ_PER_KG,
    LITERS_PER_GALLON,
)
from .interfaces import DataCenterFootprint

HOURS_PER_DAY = 24.0
DAYS_PER_YEAR = 365.0


# ---------------------------------------------------------------------------
# Metric 5 building block: the cooling-equivalence factor (shared constant)
# ---------------------------------------------------------------------------

# kg of ice that must MELT to reject the same heat one litre of evaporated
# cooling water rejects. ~2260 / 334 ~= 6.766 kg ice per litre of water.
ICE_KG_PER_LITER_WATER: float = (
    LATENT_HEAT_VAPORISATION_WATER_KJ_PER_KG / LATENT_HEAT_FUSION_ICE_KJ_PER_KG
)


def snow_volume_m3_for_ice_kg(ice_kg: float, snow_density_kg_m3: float) -> float:
    """Volume of snow (at a given density) holding `ice_kg` of water-equivalent mass."""
    if ice_kg < 0:
        raise ValueError("ice_kg must be non-negative")
    if snow_density_kg_m3 <= 0:
        raise ValueError("snow_density must be positive")
    return ice_kg / snow_density_kg_m3


@dataclass(frozen=True)
class SnowEquivalence:
    """Snow required to cooling-match a given volume of evaporated water."""

    water_liters: float
    ice_kg: float                       # ice to melt for equivalent cooling
    ice_tonnes: float
    snow_m3_fresh: float                # as fresh snow (~100 kg/m^3)
    snow_m3_packed: float               # as a packed pile (~600 kg/m^3)
    ice_m3_solid: float                 # as solid ice (~917 kg/m^3)
    # secondary, clearly-labeled: literal water-content volume (NOT cooling)
    snow_m3_water_content_fresh: float


def snow_required_for_water(
    water_liters: float,
    fresh_density: float = DENSITY_FRESH_SNOW,
    packed_density: float = DENSITY_PACKED_PILE,
) -> SnowEquivalence:
    """Metric 5: snow needed (cooling-equivalence) to offset `water_liters` of
    evaporative cooling water.

    Primary numbers are cooling-equivalent (the project's thesis). A secondary
    `snow_m3_water_content_fresh` is included only to answer the literal "same
    water content" question, and must be labeled as such in the UI - it is NOT
    a cooling claim.
    """
    if water_liters < 0:
        raise ValueError("water_liters must be non-negative")

    ice_kg = water_liters * ICE_KG_PER_LITER_WATER
    # Literal water content: 1 L water == 1 kg; as fresh snow that's volume = mass/density.
    water_content_kg = water_liters * 1.0
    return SnowEquivalence(
        water_liters=water_liters,
        ice_kg=ice_kg,
        ice_tonnes=ice_kg / 1000.0,
        snow_m3_fresh=snow_volume_m3_for_ice_kg(ice_kg, fresh_density),
        snow_m3_packed=snow_volume_m3_for_ice_kg(ice_kg, packed_density),
        ice_m3_solid=snow_volume_m3_for_ice_kg(ice_kg, DENSITY_ICE),
        snow_m3_water_content_fresh=snow_volume_m3_for_ice_kg(water_content_kg, fresh_density),
    )


# ---------------------------------------------------------------------------
# The full dashboard metric set
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DashboardMetrics:
    site: str

    # (2) heat dissipated / cooling load
    heat_rejected_kwh_per_day: float
    heat_rejected_mwh_per_day: float
    cooling_power_kw: float

    # (1) + (3) water usage
    water_liters_per_day: float
    water_gallons_per_day: float
    water_liters_per_year: float
    water_gallons_per_year: float

    # (4) projected AI-driven increase
    ai_growth_factor: float             # e.g. 1.8 == +80%
    projected_water_gallons_per_year: float
    projected_water_gallons_per_day: float
    extra_water_gallons_per_year: float  # increase vs. today

    # (5) snow required (cooling-equivalence) for today's and projected water
    snow_today: SnowEquivalence
    snow_projected: SnowEquivalence


def compute_dashboard(
    footprint: DataCenterFootprint,
    ai_growth_factor: float = 1.8,
) -> DashboardMetrics:
    """Compile all dashboard metrics for one data center footprint.

    Args:
        footprint: the data center (IT load, PUE, WUE, cooling fraction, ...).
        ai_growth_factor: multiplier for projected AI-driven demand growth.
            1.0 = no growth; 1.8 = +80%. Anchored to LBNL/DOE projections that
            data-center water use roughly doubles by ~2028 (keep it a slider in UI).
    """
    if ai_growth_factor < 1.0:
        raise ValueError("ai_growth_factor must be >= 1.0")

    # (2) Heat dissipated = cooling load. cooling_power_kw is the rate of heat
    # the facility rejects; over a day that is the daily heat dissipated.
    cooling_kw = footprint.cooling_power_kw
    heat_kwh_day = cooling_kw * HOURS_PER_DAY

    # (1)/(3) Water usage. WUE is liters per kWh of IT energy.
    it_kwh_day = footprint.it_load_kw * HOURS_PER_DAY
    water_l_day = it_kwh_day * footprint.wue_l_per_kwh
    water_l_year = water_l_day * DAYS_PER_YEAR

    # (4) AI-driven projection.
    projected_l_year = water_l_year * ai_growth_factor
    projected_l_day = water_l_day * ai_growth_factor
    extra_l_year = projected_l_year - water_l_year

    return DashboardMetrics(
        site=footprint.name,
        heat_rejected_kwh_per_day=heat_kwh_day,
        heat_rejected_mwh_per_day=heat_kwh_day / 1000.0,
        cooling_power_kw=cooling_kw,
        water_liters_per_day=water_l_day,
        water_gallons_per_day=water_l_day / LITERS_PER_GALLON,
        water_liters_per_year=water_l_year,
        water_gallons_per_year=water_l_year / LITERS_PER_GALLON,
        ai_growth_factor=ai_growth_factor,
        projected_water_gallons_per_year=projected_l_year / LITERS_PER_GALLON,
        projected_water_gallons_per_day=projected_l_day / LITERS_PER_GALLON,
        extra_water_gallons_per_year=extra_l_year / LITERS_PER_GALLON,
        snow_today=snow_required_for_water(water_l_year),
        snow_projected=snow_required_for_water(projected_l_year),
    )
