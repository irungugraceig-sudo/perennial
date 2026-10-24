"""Boston-area data center facilities (the customers — anyone running GPUs).

We focus on Boston and switch between real facilities, each kept separate (not
combined) so a facility sees ITS OWN total consumption and savings for carbon
reporting. AWS appears as an example hyperscaler footprint from public figures.

Sources:
  * AWS global PUE 1.15 (2024), WUE 0.12-0.15 L/kWh — Amazon Sustainability.
  * Evaporative colo WUE ~1.8 L/kWh — DOE/LBNL baseline.
  * New England grid ~0.30 kg CO2/kWh (approx).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DataCenter:
    name: str
    operator: str
    city: str
    latitude: float
    longitude: float
    kind: str                      # "hyperscaler" | "colocation" | "hpc"
    gpu_heavy: bool
    it_load_kw: float
    pue: float
    wue_l_per_kwh: float
    cooling_fraction: float
    grid_co2_kg_per_kwh: float
    note: str = ""


# Boston-area facilities. Coordinates are real/approximate building locations.
DATA_CENTERS: list[DataCenter] = [
    DataCenter(
        name="Markley One Summer Street",
        operator="Markley Group",
        city="Boston, MA",
        latitude=42.3539, longitude=-71.0598,
        kind="colocation", gpu_heavy=True,
        it_load_kw=2000.0, pue=1.5, wue_l_per_kwh=1.8,
        cooling_fraction=0.33, grid_co2_kg_per_kwh=0.30,
        note="Boston's carrier hotel; colo with AI tenants. Evaporative cooling = big water savings.",
    ),
    DataCenter(
        name="Markley Lowell",
        operator="Markley Group",
        city="Lowell, MA",
        latitude=42.6334, longitude=-71.3162,
        kind="colocation", gpu_heavy=True,
        it_load_kw=3000.0, pue=1.45, wue_l_per_kwh=1.6,
        cooling_fraction=0.34, grid_co2_kg_per_kwh=0.30,
        note="Largest data center in Massachusetts.",
    ),
    DataCenter(
        name="TierPoint Marlborough",
        operator="TierPoint",
        city="Marlborough, MA",
        latitude=42.3459, longitude=-71.5523,
        kind="colocation", gpu_heavy=False,
        it_load_kw=1500.0, pue=1.5, wue_l_per_kwh=1.7,
        cooling_fraction=0.33, grid_co2_kg_per_kwh=0.30,
        note="Regional colocation west of Boston.",
    ),
    DataCenter(
        name="AWS-style hyperscaler (example)",
        operator="Hyperscaler profile",
        city="Greater Boston",
        latitude=42.4072, longitude=-71.1190,
        kind="hyperscaler", gpu_heavy=True,
        it_load_kw=20000.0, pue=1.15, wue_l_per_kwh=0.15,
        cooling_fraction=0.11, grid_co2_kg_per_kwh=0.30,
        note="Published AWS figures: PUE 1.15, WUE 0.15 L/kWh (2024). Already efficient — pitch is summer peak + carbon toward 2030 water goals.",
    ),
    DataCenter(
        name="Mass Green HPC Center",
        operator="Five-university consortium",
        city="Holyoke, MA",
        latitude=42.2043, longitude=-72.6162,
        kind="hpc", gpu_heavy=True,
        it_load_kw=10000.0, pue=1.3, wue_l_per_kwh=1.2,
        cooling_fraction=0.23, grid_co2_kg_per_kwh=0.30,
        note="University GPU/HPC; western MA gets more snow than Boston.",
    ),
]


def by_name(name: str) -> DataCenter:
    for dc in DATA_CENTERS:
        if dc.name == name:
            return dc
    return DATA_CENTERS[0]
