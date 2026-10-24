"""Contract between the footprint half (partner) and the engine half.

The engine does NOT care how the footprint numbers are produced. It only needs
this shape. Partner fills footprint/ to produce a DataCenterFootprint; engine
consumes it. Keeping this contract stable lets both halves be built in parallel.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DataCenterFootprint:
    """Current heat usage + resource footprint of a data center.

    Produced by the footprint package (partner). All values are SI / standard.
    """

    name: str                     # e.g. "Markley - One Summer Street, Boston"
    it_load_kw: float             # IT equipment electrical load (kW)
    pue: float                    # Power Usage Effectiveness (total / IT), e.g. 1.5
    wue_l_per_kwh: float          # Water Usage Effectiveness (liters water / kWh IT)
    cooling_fraction: float       # fraction of total facility power spent on cooling (0-1)
    grid_co2_kg_per_kwh: float    # grid carbon intensity for the site's utility

    @property
    def total_power_kw(self) -> float:
        return self.it_load_kw * self.pue

    @property
    def cooling_power_kw(self) -> float:
        return self.total_power_kw * self.cooling_fraction

    @property
    def annual_water_liters(self) -> float:
        # WUE is per kWh of IT energy; annualize the IT load.
        annual_it_kwh = self.it_load_kw * 24.0 * 365.0
        return annual_it_kwh * self.wue_l_per_kwh


@dataclass(frozen=True)
class MonthlyCoolingDemand:
    """Optional finer input: cooling demand per month (kWh of heat to reject).

    If the partner can produce this, the engine draws the demand curve directly.
    If not, the engine derives a seasonal shape from temperature normals.
    """

    month: int        # 1-12
    cooling_kwh: float
