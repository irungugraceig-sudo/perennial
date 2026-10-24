"""Boston-area data center facilities and the GPU tenants inside them.

Scoped to the Boston metro for realistic, local data. Each facility lists its
tenants (the customers running GPUs) so we can show per-tenant consumption and
savings, which is what each tenant needs for its own carbon reporting.

Sources:
  * AWS global PUE 1.15 (2024), WUE 0.12-0.15 L/kWh — Amazon Sustainability (tenant example).
  * Evaporative colo WUE ~1.8 L/kWh — DOE/LBNL baseline.
  * New England grid ~0.30 kg CO2/kWh (approx).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Tenant:
    name: str
    kind: str                 # "cloud" | "gpu-cloud" | "university" | "enterprise"
    it_load_kw: float         # this tenant's share of the building's IT load
    gpu_heavy: bool


@dataclass(frozen=True)
class DataCenter:
    name: str
    operator: str
    city: str
    latitude: float
    longitude: float
    kind: str
    gpu_heavy: bool
    it_load_kw: float
    pue: float
    wue_l_per_kwh: float
    cooling_fraction: float
    grid_co2_kg_per_kwh: float
    note: str = ""
    tenants: list[Tenant] = field(default_factory=list)


# Boston-area facilities only.
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
        tenants=[
            Tenant("AWS-style cloud tenant", "cloud", 800.0, True),
            Tenant("GPU-cloud startup", "gpu-cloud", 600.0, True),
            Tenant("University research cluster", "university", 350.0, True),
            Tenant("Enterprise colo", "enterprise", 250.0, False),
        ],
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
        tenants=[
            Tenant("Hyperscaler overflow", "cloud", 1400.0, True),
            Tenant("GPU-cloud (AI inference)", "gpu-cloud", 900.0, True),
            Tenant("Hospital/health data", "enterprise", 700.0, False),
        ],
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
        tenants=[
            Tenant("GPU-cloud tenant", "gpu-cloud", 500.0, True),
            Tenant("SaaS enterprise", "enterprise", 600.0, False),
            Tenant("University overflow", "university", 400.0, True),
        ],
    ),
]


def by_name(name: str) -> DataCenter:
    for dc in DATA_CENTERS:
        if dc.name == name:
            return dc
    return DATA_CENTERS[0]
