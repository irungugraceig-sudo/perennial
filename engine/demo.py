"""End-to-end smoke demo of the Perennial engine.

Run from the repo root:  python -m engine.demo

Uses a placeholder footprint so this half runs WITHOUT the partner's work done.
Replace `placeholder_footprint()` with footprint.markley.markley_footprint() once ready.
"""

from __future__ import annotations

from .constants import COOLING_KWH_PER_TONNE_ICE
from .cooling import HeatExchanger
from .interfaces import DataCenterFootprint
from .piles import SnowPile
from .snow import CollectionInputs, collected_mass_empirical, collected_mass_geometric
from .viability import assess


def placeholder_footprint() -> DataCenterFootprint:
    """Stand-in until the partner's footprint package is wired in."""
    return DataCenterFootprint(
        name="Markley - One Summer Street, Boston (PLACEHOLDER numbers)",
        it_load_kw=2000.0,        # 2 MW IT load
        pue=1.5,
        wue_l_per_kwh=1.8,        # evaporative baseline
        cooling_fraction=0.33,
        grid_co2_kg_per_kwh=0.30, # MA grid approx
    )


def main() -> None:
    # 1 tonne of ice ~ this many kWh of cooling
    print(f"Cooling per tonne of ice: {COOLING_KWH_PER_TONNE_ICE:.1f} kWh")

    # Estimate collected snow two ways (Boston, ~1.5 m seasonal snowfall example).
    geo_inputs = CollectionInputs(snowfall_m=1.5, collection_efficiency=0.4)
    mass_geo = collected_mass_geometric(geo_inputs)
    mass_emp = collected_mass_empirical(cubic_yards_per_storm=89_000, storms_per_season=6)
    print(f"Collected mass (geometric): {mass_geo/1000:,.0f} tonnes")
    print(f"Collected mass (empirical): {mass_emp/1000:,.0f} tonnes")

    # Build one live pile from the geometric estimate (split would be per site).
    pile = SnowPile(
        site_name="Seaport Snow Farm",
        latitude=42.345,
        longitude=-71.041,
        initial_mass_kg=mass_geo,
        passive_loss_fraction=0.25,
    )
    print(f"Pile available cooling: {pile.available_cooling_kwh/1000:,.0f} MWh")

    report = assess(
        footprint=placeholder_footprint(),
        piles=[pile],
        exchanger=HeatExchanger(effectiveness=0.85, fouling_factor=0.1),
        chiller_cop=4.0,
    )

    print("\n--- Viability report ---")
    print(f"Site: {report.footprint_name}")
    print(f"Annual cooling demand: {report.annual_cooling_demand_kwh/1000:,.0f} MWh")
    print(f"Cooling delivered by snow: {report.cooling_delivered_kwh/1000:,.0f} MWh")
    print(f"Fraction of demand offset: {report.fraction_offset*100:.1f}%")
    print(f"Fresh water saved: {report.offset.fresh_water_saved_gallons:,.0f} gallons")
    print(f"Chiller energy avoided: {report.offset.chiller_energy_avoided_kwh/1000:,.0f} MWh")
    print(f"CO2 avoided: {report.offset.co2_avoided_kg/1000:,.1f} tonnes")
    print(f"Verdict: {report.verdict}")


if __name__ == "__main__":
    main()
