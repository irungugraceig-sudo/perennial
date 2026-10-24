"""Live snow-pile model: mass over time, melt, insulation loss.

Boston has ~11 snow-farm sites. We model each as a pile that starts with a
collected mass and depletes two ways through the season:
  * cooling melt   - ice we deliberately melt to reject data-center heat (useful)
  * passive melt   - ambient losses despite insulation (wasted; the loss factor)

"Live tracking" in the app = these pile objects updated on a schedule (seeded
from snow/collection data), shown depleting in real time. Honest: it is a model,
not a physical sensor feed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .constants import COOLING_KWH_PER_TONNE_ICE, KJ_PER_KWH, LATENT_HEAT_FUSION_ICE_KJ_PER_KG


@dataclass
class SnowPile:
    """A single snow-farm pile."""

    site_name: str
    latitude: float
    longitude: float
    initial_mass_kg: float
    current_mass_kg: float = field(default=0.0)
    passive_loss_fraction: float = 0.25  # insulated pile loses ~20-30% to ambient melt

    def __post_init__(self) -> None:
        if self.initial_mass_kg < 0:
            raise ValueError("initial_mass_kg must be non-negative")
        if not (0.0 <= self.passive_loss_fraction <= 1.0):
            raise ValueError("passive_loss_fraction must be between 0 and 1")
        if self.current_mass_kg == 0.0:
            self.current_mass_kg = self.initial_mass_kg

    @property
    def usable_mass_kg(self) -> float:
        """Mass available for cooling after subtracting expected passive losses."""
        return self.current_mass_kg * (1.0 - self.passive_loss_fraction)

    @property
    def available_cooling_kwh(self) -> float:
        """Cold still deliverable from the usable mass."""
        return (self.usable_mass_kg / 1000.0) * COOLING_KWH_PER_TONNE_ICE

    def draw_cooling(self, cooling_kwh: float) -> float:
        """Melt ice to deliver `cooling_kwh` of cooling. Returns kWh actually delivered.

        Caps at what the pile can provide (never goes negative).
        """
        if cooling_kwh < 0:
            raise ValueError("cooling_kwh must be non-negative")
        deliverable = min(cooling_kwh, self.available_cooling_kwh)
        mass_melted_kg = (deliverable * KJ_PER_KWH) / LATENT_HEAT_FUSION_ICE_KJ_PER_KG
        self.current_mass_kg = max(0.0, self.current_mass_kg - mass_melted_kg)
        return deliverable


def total_available_cooling_kwh(piles: list[SnowPile]) -> float:
    """Sum of cold available across all live piles."""
    return sum(p.available_cooling_kwh for p in piles)
