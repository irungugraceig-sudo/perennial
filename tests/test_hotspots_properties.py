"""Property-based tests for the Snow Persistence Score and terrain helpers."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from engine.hotspots import Candidate, ScoreWeights, score_candidate
from engine.terrain import northness

finite = st.floats(min_value=0.0, max_value=1e4, allow_nan=False, allow_infinity=False)
aspect = st.floats(min_value=0.0, max_value=360.0, allow_nan=False, allow_infinity=False)


@given(a=aspect)
def test_northness_bounded(a):
    n = northness(a)
    assert 0.0 <= n <= 1.0


def test_northness_poles():
    assert northness(0.0) > 0.99      # due north ~ 1
    assert northness(180.0) < 0.01    # due south ~ 0


@given(
    snow=finite, elev=finite, slope=finite, asp=aspect, dist=finite,
)
def test_score_bounded(snow, elev, slope, asp, dist):
    c = Candidate(
        name="x", lat=42.0, lon=-71.0,
        snowfall_m=snow, elevation_m=elev, slope_deg=slope,
        aspect_deg=asp, distance_km_to_demand=dist,
    )
    s = score_candidate(c)
    assert 0.0 <= s.score <= 1.0
    for v in s.factors.values():
        assert 0.0 <= v <= 1.0


@given(snow_lo=st.floats(0, 2, allow_nan=False), extra=st.floats(0.01, 1, allow_nan=False))
def test_more_snow_never_lowers_score(snow_lo, extra):
    base = Candidate("x", 42.0, -71.0, snow_lo, 100, 5, 0, 10)
    more = Candidate("x", 42.0, -71.0, snow_lo + extra, 100, 5, 0, 10)
    assert score_candidate(more).score >= score_candidate(base).score - 1e-9


@given(dist_lo=st.floats(0, 40, allow_nan=False), extra=st.floats(0.01, 10, allow_nan=False))
def test_closer_never_lowers_score(dist_lo, extra):
    near = Candidate("x", 42.0, -71.0, 1.5, 100, 5, 0, dist_lo)
    far = Candidate("x", 42.0, -71.0, 1.5, 100, 5, 0, dist_lo + extra)
    assert score_candidate(near).score >= score_candidate(far).score - 1e-9


def test_weights_normalized_regardless_of_magnitude():
    c = Candidate("x", 42.0, -71.0, 1.5, 100, 5, 0, 10)
    s1 = score_candidate(c, ScoreWeights(1, 1, 1, 1, 1))
    s2 = score_candidate(c, ScoreWeights(2, 2, 2, 2, 2))
    assert abs(s1.score - s2.score) < 1e-9  # scaling all weights doesn't change score
