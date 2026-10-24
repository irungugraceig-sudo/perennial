"""Heat-exchanger model: how much of a pile's cold actually reaches the servers.

The dirty snow meltwater and the ultrapure coolant never mix. They meet in a
shell-and-tube heat exchanger: coolant in the tubes, dirty meltwater in the shell.
Only heat crosses the tube walls.

Real exchangers lose some performance to:
  * effectiveness  - no exchanger transfers 100% of available cold
  * fouling        - salt/sediment/biofilm on the shell side degrades transfer over time
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HeatExchanger:
    """Shell-and-tube heat exchanger parameters."""

    effectiveness: float = 0.85   # fraction of available cold transferred (0-1)
    fouling_factor: float = 0.1   # fractional performance lost to fouling (0-1)

    def __post_init__(self) -> None:
        if not (0.0 <= self.effectiveness <= 1.0):
            raise ValueError("effectiveness must be between 0 and 1")
        if not (0.0 <= self.fouling_factor <= 1.0):
            raise ValueError("fouling_factor must be between 0 and 1")

    @property
    def delivery_ratio(self) -> float:
        """Net fraction of a pile's cold that reaches the coolant loop."""
        return self.effectiveness * (1.0 - self.fouling_factor)

    def deliverable_cooling_kwh(self, pile_cooling_kwh: float) -> float:
        if pile_cooling_kwh < 0:
            raise ValueError("pile_cooling_kwh must be non-negative")
        return pile_cooling_kwh * self.delivery_ratio
