"""Property-based tests for the seasonal peak-shaving model."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from engine.seasonal import COOLING_DEMAND_SHAPE, build_season

demand = st.floats(min_value=1.0, max_value=1e9, allow_nan=False, allow_infinity=False)
mass = st.floats(min_value=0.0, max_value=1e9, allow_nan=False, allow_infinity=False)
frac = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)


@given(d=demand, m=mass, loss=frac, ratio=frac)
def test_twelve_months_and_bounded_offsets(d, m, loss, ratio):
    s = build_season(d, m, passive_loss_fraction=loss, delivery_ratio=ratio)
    assert len(s.months) == 12
    for p in s.months:
        assert 0.0 <= p.offset_pct <= 100.0 + 1e-6
        assert p.snow_supply_kwh >= 0.0
        assert p.pile_mass_tonnes >= -1e-6       # pile never negative
        assert p.snow_supply_kwh <= p.demand_kwh + 1e-3  # never deliver beyond demand


@given(d=demand, m=mass, loss=frac, ratio=frac)
def test_snow_never_exceeds_demand_total(d, m, loss, ratio):
    s = build_season(d, m, passive_loss_fraction=loss, delivery_ratio=ratio)
    assert s.annual_snow_kwh <= s.annual_demand_kwh + 1e-3


@given(d=demand, extra=mass)
def test_more_snow_never_less_peak_offset(d, extra):
    base = build_season(d, 10_000_000.0).peak_month_offset_pct
    more = build_season(d, 10_000_000.0 + extra).peak_month_offset_pct
    assert more >= base - 1e-6


def test_demand_shape_peaks_in_summer():
    # Jul (index 6) and Aug (index 7) are the max of the 12-month shape.
    peak = max(COOLING_DEMAND_SHAPE)
    assert COOLING_DEMAND_SHAPE[6] == peak or COOLING_DEMAND_SHAPE[7] == peak
