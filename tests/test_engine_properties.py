"""Property-based tests for the Perennial engine (Hypothesis).

These assert invariants that must hold for ALL valid inputs, not just hand-picked
examples. They are the kind of checks that catch the assumption bugs unit tests miss.

Requirements covered (see HACKATHON_CONTEXT.md):
  * Offset is never negative and never claims >100% of demand.
  * More snow never produces less cooling (monotonicity).
  * Doubling collection area doubles collected mass (linearity).
  * A pile can never deliver more cold than it physically holds (energy conservation).
  * Heat-exchanger losses only ever reduce delivered cold.
"""

from __future__ import annotations

import math

from hypothesis import assume, given
from hypothesis import strategies as st

from engine.constants import COOLING_KWH_PER_TONNE_ICE
from engine.cooling import HeatExchanger
from engine.offset import compute_offset, fraction_of_demand_offset
from engine.piles import SnowPile
from engine.snow import CollectionInputs, collected_mass_geometric

# ---- reusable strategies ----
nonneg = st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False)
positive = st.floats(min_value=1e-3, max_value=1e6, allow_nan=False, allow_infinity=False)
fraction = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)


# ---------- snow / collection ----------
@given(snowfall=nonneg, eff=fraction, density=positive)
def test_collected_mass_non_negative(snowfall, eff, density):
    mass = collected_mass_geometric(
        CollectionInputs(snowfall_m=snowfall, collection_efficiency=eff, fresh_snow_density=density)
    )
    assert mass >= 0.0


@given(
    snowfall=st.floats(min_value=0.0, max_value=100.0, allow_nan=False),
    extra=st.floats(min_value=0.0, max_value=100.0, allow_nan=False),
    eff=st.floats(min_value=0.01, max_value=1.0, allow_nan=False),
    density=positive,
)
def test_more_snow_never_less_mass(snowfall, extra, eff, density):
    """Monotonic: more snowfall => at least as much collected mass."""
    base = collected_mass_geometric(
        CollectionInputs(snowfall_m=snowfall, collection_efficiency=eff, fresh_snow_density=density)
    )
    more = collected_mass_geometric(
        CollectionInputs(snowfall_m=snowfall + extra, collection_efficiency=eff, fresh_snow_density=density)
    )
    assert more >= base - 1e-6


@given(
    snowfall=st.floats(min_value=0.01, max_value=50.0, allow_nan=False),
    eff=st.floats(min_value=0.01, max_value=1.0, allow_nan=False),
    density=positive,
    width=st.floats(min_value=0.1, max_value=50.0, allow_nan=False),
)
def test_collection_linear_in_area(snowfall, eff, density, width):
    """Doubling effective lane width doubles collected mass (linearity)."""
    single = collected_mass_geometric(
        CollectionInputs(
            snowfall_m=snowfall, collection_efficiency=eff,
            fresh_snow_density=density, effective_lane_width_m=width,
        )
    )
    double = collected_mass_geometric(
        CollectionInputs(
            snowfall_m=snowfall, collection_efficiency=eff,
            fresh_snow_density=density, effective_lane_width_m=width * 2,
        )
    )
    assert math.isclose(double, single * 2, rel_tol=1e-6)


# ---------- piles / energy conservation ----------
@given(mass=nonneg, loss=fraction)
def test_pile_cooling_matches_usable_mass(mass, loss):
    pile = SnowPile("t", 42.0, -71.0, initial_mass_kg=mass, passive_loss_fraction=loss)
    expected = (mass * (1.0 - loss) / 1000.0) * COOLING_KWH_PER_TONNE_ICE
    assert math.isclose(pile.available_cooling_kwh, expected, rel_tol=1e-9, abs_tol=1e-9)


@given(mass=positive, loss=fraction, request_kwh=nonneg)
def test_pile_never_overdraws(mass, loss, request_kwh):
    """A pile can never deliver more cold than it holds, and mass never goes negative."""
    pile = SnowPile("t", 42.0, -71.0, initial_mass_kg=mass, passive_loss_fraction=loss)
    available_before = pile.available_cooling_kwh
    delivered = pile.draw_cooling(request_kwh)
    assert delivered <= available_before + 1e-6
    assert delivered <= request_kwh + 1e-6
    assert pile.current_mass_kg >= -1e-6


# ---------- heat exchanger ----------
@given(pile_kwh=nonneg, eff=fraction, foul=fraction)
def test_exchanger_only_reduces(pile_kwh, eff, foul):
    hx = HeatExchanger(effectiveness=eff, fouling_factor=foul)
    delivered = hx.deliverable_cooling_kwh(pile_kwh)
    assert 0.0 <= delivered <= pile_kwh + 1e-6


# ---------- offset ----------
@given(
    cooling=nonneg,
    wue=nonneg,
    cop=positive,
    co2=nonneg,
)
def test_offset_non_negative(cooling, wue, cop, co2):
    r = compute_offset(cooling, wue, cop, co2)
    assert r.fresh_water_saved_liters >= 0.0
    assert r.fresh_water_saved_gallons >= 0.0
    assert r.chiller_energy_avoided_kwh >= 0.0
    assert r.co2_avoided_kg >= 0.0


@given(delivered=nonneg, demand=nonneg)
def test_fraction_offset_bounded(delivered, demand):
    f = fraction_of_demand_offset(delivered, demand)
    assert 0.0 <= f <= 1.0


@given(
    cooling=positive,
    wue=positive,
    cop=positive,
    co2=positive,
    extra=positive,
)
def test_more_cooling_saves_more_water(cooling, wue, cop, co2, extra):
    """Monotonic: more cooling delivered => at least as much water saved."""
    base = compute_offset(cooling, wue, cop, co2).fresh_water_saved_liters
    more = compute_offset(cooling + extra, wue, cop, co2).fresh_water_saved_liters
    assert more >= base - 1e-6
