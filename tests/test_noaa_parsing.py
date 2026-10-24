"""Offline tests for ACIS/NOAA snowfall parsing (no network).

We don't hit the network in tests. Instead we verify the parsing logic handles
the markers ACIS actually returns: numbers, "M" (missing), "T" (trace), None.
"""

from __future__ import annotations

from unittest.mock import patch

from engine.noaa import INCH_TO_METER, fetch_seasonal_snowfall


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_parsing_sums_numbers_and_handles_markers():
    fake = _FakeResp(
        {
            "data": [
                ["2015-01-27", "24.0"],  # blizzard day
                ["2015-01-28", "M"],     # missing -> skipped
                ["2015-01-29", "T"],     # trace -> counts as day, ~0 inches
                ["2015-01-30", "6.0"],
                ["2015-01-31", None],    # None -> skipped
            ]
        }
    )
    with patch("engine.noaa.requests.post", return_value=fake):
        s = fetch_seasonal_snowfall("2015-01-27", "2015-01-31")

    assert s.total_inches == 30.0                 # 24 + 6; M/None skipped
    assert s.total_meters == 30.0 * INCH_TO_METER
    assert s.days_counted == 3                     # two numbers + one trace


def test_empty_data_is_zero():
    with patch("engine.noaa.requests.post", return_value=_FakeResp({"data": []})):
        s = fetch_seasonal_snowfall("2020-01-01", "2020-01-02")
    assert s.total_inches == 0.0
    assert s.days_counted == 0


# --- monthly snowfall parsing (feeds the ML predictor) ---------------------

from engine.noaa import fetch_monthly_snowfall  # noqa: E402


def _fake_monthly():
    return _FakeResp(
        {
            "meta": {"ll": [-71.0, 42.3606], "elev": 11.0, "name": "BOSTON LOGAN"},
            "data": [
                ["2015-01", "34.3"],   # record January
                ["2015-02", "64.8"],
                ["2015-07", "0.0"],    # summer
                ["2015-11", "T"],      # trace -> 0 inches, still a row
                ["2015-12", "M"],      # missing -> skipped
            ],
        }
    )


def test_monthly_parsing_uses_meta_and_handles_markers():
    with patch("engine.noaa.requests.post", return_value=_fake_monthly()):
        rows = fetch_monthly_snowfall("2015-01", "2015-12")

    # 5 rows in, 1 missing ("M") dropped -> 4 rows
    assert len(rows) == 4
    jan = next(r for r in rows if r.month == 1)
    assert jan.year == 2015
    assert jan.snow_inches == 34.3
    assert jan.snow_meters == round(34.3 * INCH_TO_METER, 10) or abs(
        jan.snow_meters - 34.3 * INCH_TO_METER
    ) < 1e-9
    # latitude from meta, elevation converted feet->meters (11 ft * 0.3048)
    assert abs(jan.latitude - 42.3606) < 1e-9
    assert abs(jan.elevation_m - 11.0 * 0.3048) < 1e-6
    # trace month present as ~0
    nov = next(r for r in rows if r.month == 11)
    assert nov.snow_inches == 0.0


def test_monthly_empty_is_empty_list():
    with patch("engine.noaa.requests.post", return_value=_FakeResp({"meta": {}, "data": []})):
        rows = fetch_monthly_snowfall("2020-01", "2020-03")
    assert rows == []
