"""Tests for the dashboard metrics (water, heat, AI projection, snow-equivalence)."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from engine.interfaces import DataCenterFootprint
from engine.metrics import (
    ICE_KG_PER_LITER_WATER,
    compute_dashboard,
    snow_required_for_water,
)

loads = st.floats(min_value=1.0, max_value=100_000.0, allow_nan=False, allow_infinity=False)
pues = st.floats(min_value=1.0, max_value=3.0, allow_nan=False, allow_infinity=False)
wues = st.floats(min_value=0.0, max_value=3.0, allow_nan=False, allow_infinity=False)
cfracs = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
growth = st.floats(min_value=1.0, max_value=5.0, allow_nan=False, allow_infinity=False)
liters = st.floats(min_value=0.0, max_value=1e10, allow_nan=False, allow_infinity=False)


def _fp(it_kw=2000.0, pue=1.5, wue=1.8, cfrac=0.33):
    return DataCenterFootprint(
        name="Test DC", it_load_kw=it_kw, pue=pue,
        wue_l_per_kwh=wue, cooling_fraction=cfrac, grid_co2_kg_per_kwh=0.3,
    )


# ---- cooling-equivalence factor -------------------------------------------


def test_cooling_equivalence_factor_is_about_6_8():
    # 2260 / 334 ~= 6.77 kg ice per litre of evaporated water
    assert ICE_KG_PER_LITER_WATER == pytest.approx(6.766, abs=0.02)


def test_snow_equivalence_known_values():
    s = snow_required_for_water(1000.0)  # 1000 L
    assert s.ice_kg == pytest.approx(1000.0 * ICE_KG_PER_LITER_WATER)
    # fresh snow ~100 kg/m^3 => volume = ice_kg / 100
    assert s.snow_m3_fresh == pytest.approx(s.ice_kg / 100.0)
    # packed pile denser => smaller volume than fresh
    assert s.snow_m3_packed < s.snow_m3_fresh
    # cooling-equivalent ice mass is ~6.8x the literal water-content mass,
    # so the cooling snow volume dwarfs the water-content volume
    assert s.snow_m3_fresh > s.snow_m3_water_content_fresh


@settings(max_examples=200)
@given(liters)
def test_snow_equivalence_scales_and_nonnegative(l):
    s = snow_required_for_water(l)
    assert s.ice_kg >= 0 and s.snow_m3_fresh >= 0
    assert s.ice_kg == pytest.approx(l * ICE_KG_PER_LITER_WATER)


# ---- full dashboard --------------------------------------------------------


def test_dashboard_known_markley_like():
    m = compute_dashboard(_fp(), ai_growth_factor=1.8)
    # IT 2000 kW * 24 h * 1.8 L/kWh = 86,400 L/day
    assert m.water_liters_per_day == pytest.approx(2000 * 24 * 1.8)
    # heat dissipated/day = cooling_power_kw * 24; cooling_power = 2000*1.5*0.33
    assert m.cooling_power_kw == pytest.approx(2000 * 1.5 * 0.33)
    assert m.heat_rejected_kwh_per_day == pytest.approx(m.cooling_power_kw * 24)
    # projection: +80%
    assert m.projected_water_gallons_per_year == pytest.approx(
        m.water_gallons_per_year * 1.8
    )
    assert m.extra_water_gallons_per_year == pytest.approx(
        m.water_gallons_per_year * 0.8
    )


def test_dashboard_rejects_shrinking_growth():
    with pytest.raises(ValueError):
        compute_dashboard(_fp(), ai_growth_factor=0.9)


@settings(max_examples=200)
@given(it=loads, pue=pues, wue=wues, cf=cfracs, g=growth)
def test_dashboard_invariants(it, pue, wue, cf, g):
    m = compute_dashboard(_fp(it, pue, wue, cf), ai_growth_factor=g)
    # all outputs non-negative
    assert m.water_liters_per_day >= 0
    assert m.heat_rejected_kwh_per_day >= 0
    # projection never below today
    assert m.projected_water_gallons_per_year >= m.water_gallons_per_year - 1e-6
    assert m.extra_water_gallons_per_year >= -1e-6
    # yearly == daily * 365
    assert m.water_liters_per_year == pytest.approx(m.water_liters_per_day * 365.0)
    # more projected water => more snow needed (monotonic)
    assert m.snow_projected.ice_kg >= m.snow_today.ice_kg - 1e-6
