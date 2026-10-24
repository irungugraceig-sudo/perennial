"""Property-based tests for the expansion planner and impact projection."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from engine.projection import plan_expansion, project_impact

kw = st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False)
pos = st.floats(min_value=0.01, max_value=10.0, allow_nan=False, allow_infinity=False)
frac = st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False)
nonneg = st.floats(min_value=0.0, max_value=1e12, allow_nan=False, allow_infinity=False)


@given(base=kw, add=kw, pue=pos, cf=frac, wue=nonneg, snow=nonneg)
def test_expansion_sane(base, add, pue, cf, wue, snow):
    r = plan_expansion(base, add, pue, cf, wue, snow)
    assert r.target_it_kw >= r.base_it_kw                 # expansion never shrinks
    assert r.added_cooling_mwh_yr >= 0.0
    assert r.added_water_gallons_yr >= 0.0
    assert 0.0 <= r.snow_coverable_pct <= 100.0 + 1e-6    # coverage bounded


@given(add1=kw, add2=kw, pue=pos, cf=frac, wue=nonneg, snow=nonneg)
def test_more_expansion_more_cooling(add1, add2, pue, cf, wue, snow):
    lo, hi = sorted((add1, add2))
    r_lo = plan_expansion(1000, lo, pue, cf, wue, snow)
    r_hi = plan_expansion(1000, hi, pue, cf, wue, snow)
    assert r_hi.added_cooling_mwh_yr >= r_lo.added_cooling_mwh_yr - 1e-6


@given(
    base_water=st.floats(1e6, 1e12, allow_nan=False),
    cagr=st.floats(0.0, 60.0, allow_nan=False),
    offset=nonneg,
)
def test_projection_grows_and_offset_bounded(base_water, cagr, offset):
    years = project_impact(2025, 2030, base_water, cagr, offset)
    assert len(years) == 6
    # water is rounded to whole gallons, so allow a 1-gallon slack in comparisons.
    for i, y in enumerate(years):
        assert y.water_gallons >= base_water - 1.0           # never below base (cagr>=0)
        assert 0.0 <= y.offset_pct <= 100.0 + 1e-6
        assert y.snow_offset_gallons <= y.water_gallons + 1.0
        if i > 0:
            assert y.water_gallons >= years[i - 1].water_gallons - 1.0  # monotone non-decreasing
