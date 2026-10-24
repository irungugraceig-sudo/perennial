"""Known data center locations for the demo map.

Real, publicly documented facilities. Coordinates are approximate building
locations. Default footprint figures are placeholders until the footprint
package (partner) supplies measured values.
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
    # Placeholder footprint defaults (partner refines these):
    it_load_kw: float
    pue: float
    wue_l_per_kwh: float
    cooling_fraction: float
    grid_co2_kg_per_kwh: float
    note: str = ""


DATA_CENTERS: list[DataCenter] = [
    DataCenter(
        name="One Summer Street",
        operator="Markley Group",
        city="Boston, MA",
        latitude=42.3539,
        longitude=-71.0598,
        it_load_kw=2000.0,
        pue=1.5,
        wue_l_per_kwh=1.8,
        cooling_fraction=0.33,
        grid_co2_kg_per_kwh=0.30,
        note="Boston's carrier hotel; largest multi-tenant DC in New England.",
    ),
    DataCenter(
        name="Lowell Data Center",
        operator="Markley Group",
        city="Lowell, MA",
        latitude=42.6334,
        longitude=-71.3162,
        it_load_kw=3000.0,
        pue=1.45,
        wue_l_per_kwh=1.6,
        cooling_fraction=0.34,
        grid_co2_kg_per_kwh=0.30,
        note="Largest data center in Massachusetts (former Prince Spaghetti factory).",
    ),
    DataCenter(
        name="TierPoint Marlborough",
        operator="TierPoint",
        city="Marlborough, MA",
        latitude=42.3459,
        longitude=-71.5523,
        it_load_kw=1500.0,
        pue=1.5,
        wue_l_per_kwh=1.7,
        cooling_fraction=0.33,
        grid_co2_kg_per_kwh=0.30,
        note="Regional colocation facility west of Boston.",
    ),
]


def by_name(name: str) -> DataCenter:
    for dc in DATA_CENTERS:
        if dc.name == name:
            return dc
    return DATA_CENTERS[0]
