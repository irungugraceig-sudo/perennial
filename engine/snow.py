"""Snowfall -> collected snow -> water-equivalent mass.

Two things must never be conflated:
  * snowfall  = what fell (from NOAA), low-density fresh snow
  * collected = what the city plowed and hauled to a farm (always less), a PACKED pile

Key physics: cooling depends on the MASS of frozen water, which is conserved as snow compacts.
Fresh snow (~100 kg/m3) plowed into a pile (~450 kg/m3) occupies less volume but holds the SAME
water mass. So we always track water-equivalent mass, and only use density to go between a measured
VOLUME and that mass.

Collection efficiency is an EXPLICIT, adjustable input, never a hidden constant.
"""

from __future__ import annotations

from dataclasses import dataclass

from .constants import (
    CUBIC_YARD_TO_CUBIC_METER,
    DENSITY_FRESH_SNOW,
    DENSITY_PACKED_PILE,
    MILE_TO_METER,
)


@dataclass(frozen=True)
class CollectionInputs:
    """Inputs for estimating how much snow a city collects (geometric method).

    Defaults are calibrated so the geometric estimate lands in the same range as
    Boston's real hauled-volume figure (see collected_mass_empirical).
    """

    snowfall_m: float                       # total seasonal snowfall depth (meters)
    plowed_length_miles: float = 785        # Boston Public Works plows ~785 mi of streets
    effective_lane_width_m: float = 11.0    # cleared width pushed toward collection (~1.5 lanes)
    collection_efficiency: float = 0.12     # fraction of fallen street-snow actually hauled (ADJUSTABLE)
    fresh_snow_density: float = DENSITY_FRESH_SNOW  # density of snow AS IT FELL (kg/m^3)


def water_equivalent_mass_kg(volume_m3: float, density: float) -> float:
    """Water-equivalent mass of a snow/ice volume. mass = volume * density.

    Cooling depends on this mass, not on how densely it is packed.
    """
    if volume_m3 < 0:
        raise ValueError("volume must be non-negative")
    if density <= 0:
        raise ValueError("density must be positive")
    return volume_m3 * density


def collected_mass_geometric(inp: CollectionInputs) -> float:
    """Method A (geometric): collected water-equivalent mass from snowfall depth.

    fallen_volume (as it fell) = snowfall_depth * plowed_area
    collected_volume = fallen_volume * collection_efficiency
    mass = collected_volume * fresh_snow_density   (water mass, conserved on compaction)
    """
    if not (0.0 <= inp.collection_efficiency <= 1.0):
        raise ValueError("collection_efficiency must be between 0 and 1")
    if inp.snowfall_m < 0:
        raise ValueError("snowfall must be non-negative")

    plowed_area_m2 = inp.plowed_length_miles * MILE_TO_METER * inp.effective_lane_width_m
    fallen_volume_m3 = inp.snowfall_m * plowed_area_m2
    collected_volume_m3 = fallen_volume_m3 * inp.collection_efficiency
    return water_equivalent_mass_kg(collected_volume_m3, inp.fresh_snow_density)


def collected_mass_empirical(
    cubic_yards_per_storm: float = 89_000,
    storms_per_season: float = 6.0,
    packed_density: float = DENSITY_PACKED_PILE,
) -> float:
    """Method B (empirical): anchor to Boston's real ~89,000 cu yd hauled per major storm.

    That volume is the PACKED pile at the snow farm, so we use packed density to get its
    water-equivalent mass. Cross-check against Method A; agreement validates the geometric
    assumptions.
    """
    if cubic_yards_per_storm < 0 or storms_per_season < 0:
        raise ValueError("inputs must be non-negative")
    season_volume_m3 = cubic_yards_per_storm * storms_per_season * CUBIC_YARD_TO_CUBIC_METER
    return water_equivalent_mass_kg(season_volume_m3, packed_density)
