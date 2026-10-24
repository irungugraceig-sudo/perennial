"""Snowfall -> collected snow -> water-equivalent mass.

Two things must never be conflated:
  * snowfall  = what fell (from NOAA)
  * collected = what the city plowed and hauled to a farm (always less)

Collection efficiency is an EXPLICIT, adjustable input, never a hidden constant.
"""

from __future__ import annotations

from dataclasses import dataclass

from .constants import (
    CUBIC_YARD_TO_CUBIC_METER,
    DENSITY_FRESH_SNOW,
    MILE_TO_METER,
)


@dataclass(frozen=True)
class CollectionInputs:
    """Inputs for estimating how much snow a city collects."""

    snowfall_m: float                 # total seasonal snowfall depth (meters)
    plowed_length_miles: float = 785  # Boston Public Works plows ~785 mi of streets
    effective_lane_width_m: float = 7.0   # ~2 lanes cleared curb-to-curb
    collection_efficiency: float = 0.4    # fraction of fallen snow actually hauled (ADJUSTABLE)
    snow_density: float = DENSITY_FRESH_SNOW  # density of snow as collected (kg/m^3)


def water_equivalent_mass_kg(volume_m3: float, snow_density: float) -> float:
    """Convert a snow volume to the mass of frozen water it contains.

    Cooling depends on MASS, not density. Density only sets how much volume that
    mass occupies. mass = volume * density.
    """
    if volume_m3 < 0:
        raise ValueError("volume must be non-negative")
    if snow_density <= 0:
        raise ValueError("snow density must be positive")
    return volume_m3 * snow_density


def collected_mass_geometric(inp: CollectionInputs) -> float:
    """Method A (geometric): estimate collected frozen-water mass from snowfall.

    collected_volume = snowfall_depth * plowed_area * collection_efficiency
    mass = collected_volume * snow_density
    """
    if not (0.0 <= inp.collection_efficiency <= 1.0):
        raise ValueError("collection_efficiency must be between 0 and 1")
    if inp.snowfall_m < 0:
        raise ValueError("snowfall must be non-negative")

    plowed_area_m2 = inp.plowed_length_miles * MILE_TO_METER * inp.effective_lane_width_m
    fallen_volume_m3 = inp.snowfall_m * plowed_area_m2
    collected_volume_m3 = fallen_volume_m3 * inp.collection_efficiency
    return water_equivalent_mass_kg(collected_volume_m3, inp.snow_density)


def collected_mass_empirical(
    cubic_yards_per_storm: float = 89_000,
    storms_per_season: float = 1.0,
    snow_density: float = DENSITY_FRESH_SNOW,
) -> float:
    """Method B (empirical): anchor to Boston's real ~89,000 cu yd / major storm.

    Cross-check against Method A; if they land in the same ballpark, the
    collection-efficiency assumption is defensible.
    """
    if cubic_yards_per_storm < 0 or storms_per_season < 0:
        raise ValueError("inputs must be non-negative")
    season_volume_m3 = cubic_yards_per_storm * storms_per_season * CUBIC_YARD_TO_CUBIC_METER
    return water_equivalent_mass_kg(season_volume_m3, snow_density)
