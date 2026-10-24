"""Catch silent number drift in the engine.

Computes a few key viability outputs with fixed inputs and compares them to a
stored baseline (scripts/demo_baseline.json). If a change moves a number beyond
tolerance, it prints the diff and exits non-zero so a hook can flag it. If the
change is intended, re-run with --update to refresh the baseline.

Usage:
    python -m scripts.check_demo_drift            # check
    python -m scripts.check_demo_drift --update   # accept current values
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from engine.cooling import HeatExchanger
from engine.interfaces import DataCenterFootprint
from engine.piles import SnowPile
from engine.seasonal import build_season
from engine.snow import CollectionInputs, collected_mass_geometric
from engine.viability import assess

BASELINE = Path(__file__).parent / "demo_baseline.json"
TOL = 0.02  # 2% relative tolerance


def current_metrics() -> dict:
    footprint = DataCenterFootprint(
        name="drift-check",
        it_load_kw=2000.0, pue=1.5, wue_l_per_kwh=1.8,
        cooling_fraction=0.33, grid_co2_kg_per_kwh=0.30,
    )
    mass = collected_mass_geometric(CollectionInputs(snowfall_m=1.1, collection_efficiency=0.12))
    pile = SnowPile("x", 42.3, -71.0, initial_mass_kg=mass, passive_loss_fraction=0.25)
    report = assess(footprint, [pile], HeatExchanger(0.85, 0.1), chiller_cop=4.0)
    season = build_season(report.annual_cooling_demand_kwh, mass, 0.25, 0.765)
    return {
        "collected_tonnes": round(mass / 1000, 1),
        "annual_demand_mwh": round(report.annual_cooling_demand_kwh / 1000, 1),
        "water_gallons": round(report.offset.fresh_water_saved_gallons, 0),
        "co2_tonnes": round(report.offset.co2_avoided_kg / 1000, 2),
        "peak_offset_pct": season.peak_month_offset_pct,
    }


def main() -> int:
    metrics = current_metrics()

    if "--update" in sys.argv or not BASELINE.exists():
        BASELINE.write_text(json.dumps(metrics, indent=2))
        print("baseline updated:", metrics)
        return 0

    baseline = json.loads(BASELINE.read_text())
    drift = []
    for k, v in metrics.items():
        b = baseline.get(k)
        if b in (None, 0):
            if v != b:
                drift.append(f"  {k}: {b} -> {v}")
            continue
        if abs(v - b) / abs(b) > TOL:
            drift.append(f"  {k}: {b} -> {v}")

    if drift:
        print("Engine output drift detected (beyond 2%):")
        print("\n".join(drift))
        print("If intended, run: python -m scripts.check_demo_drift --update")
        return 1
    print("No significant drift. Key metrics stable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
