"""Property-based tests for the seasonal snowfall predictor."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from engine.noaa import BOSTON_LOGAN_GHCND
from engine.predictor import (
    ClimatologyPredictor,
    MLSnowfallPredictor,
    MonthlySnow,
    SnowPrediction,
    seed_history,
)

months = st.integers(min_value=1, max_value=12)
areas = st.floats(min_value=0.0, max_value=5_000_000.0, allow_nan=False, allow_infinity=False)


# ---- water-equivalent conversion -----------------------------------------


def test_water_equivalent_mass():
    p = SnowPrediction(BOSTON_LOGAN_GHCND, 1, expected_m=1.0, low_m=0.5, high_m=1.5,
                       model="test", snow_to_liquid_ratio=10.0)
    # 1.0 m snow / 10 = 0.1 m water-equiv depth
    assert p.water_equivalent_m() == pytest.approx(0.1)
    # over 1,000,000 m^2: 0.1 m * 1e6 m^2 * 1000 kg/m^3 = 1e8 kg
    assert p.water_equivalent_mass_kg(1_000_000) == pytest.approx(1e8)


@given(area=areas)
def test_water_equivalent_mass_nonnegative(area):
    p = SnowPrediction(BOSTON_LOGAN_GHCND, 1, 0.8, 0.4, 1.2, "test")
    assert p.water_equivalent_mass_kg(area) >= 0.0


# ---- climatology ----------------------------------------------------------


def test_climatology_band_ordered_and_summer_zero():
    clim = ClimatologyPredictor.from_history(seed_history(end_year=2005))
    for m in range(1, 13):
        p = clim.predict_month(BOSTON_LOGAN_GHCND, m)
        assert 0.0 <= p.low_m <= p.expected_m <= p.high_m
    assert clim.predict_month(BOSTON_LOGAN_GHCND, 7).expected_m == pytest.approx(0.0)


def test_climatology_unknown_station_is_zero_not_crash():
    clim = ClimatologyPredictor.from_history(seed_history(end_year=2000))
    p = clim.predict_month("USW00099999", 1)
    assert p.expected_m == 0.0


# ---- ML model -------------------------------------------------------------


@pytest.fixture(scope="module")
def ml_model() -> MLSnowfallPredictor:
    return MLSnowfallPredictor.train(seed_history(end_year=2020))


def test_ml_seasonal_shape(ml_model):
    """Winter out-predicts summer."""
    jan = ml_model.predict_month(BOSTON_LOGAN_GHCND, 1)
    jul = ml_model.predict_month(BOSTON_LOGAN_GHCND, 7)
    assert jan.expected_m > jul.expected_m


@settings(max_examples=60, deadline=None)
@given(month=months)
def test_ml_band_invariant(ml_model, month):
    p = ml_model.predict_month(BOSTON_LOGAN_GHCND, month)
    assert 0.0 <= p.low_m <= p.expected_m <= p.high_m


def test_ml_unknown_station_falls_back(ml_model):
    p = ml_model.predict_month("USW00099999", 1)
    assert p.model == "climatology"       # degraded gracefully, no crash


def test_ml_save_load_roundtrip(ml_model, tmp_path):
    path = tmp_path / "model.joblib"
    ml_model.save(path)
    loaded = MLSnowfallPredictor.load(path)
    a = ml_model.predict_month(BOSTON_LOGAN_GHCND, 1)
    b = loaded.predict_month(BOSTON_LOGAN_GHCND, 1)
    assert a.expected_m == pytest.approx(b.expected_m)


# ---- training-row validation ----------------------------------------------


def test_monthly_snow_rejects_bad_input():
    with pytest.raises(ValueError):
        MonthlySnow(BOSTON_LOGAN_GHCND, 2000, 13, 0.5)
    with pytest.raises(ValueError):
        MonthlySnow(BOSTON_LOGAN_GHCND, 2000, 1, -0.1)
