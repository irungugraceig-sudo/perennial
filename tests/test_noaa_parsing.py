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
