"""Seasonal snowfall PREDICTION — the "how much can we expect this season" layer.

Perennial has three snowfall sources, each answering a different question:
  * noaa.py     — what ACTUALLY fell (observed history, ACIS/GHCN-Daily)
  * forecast.py — what will fall in the next ~7 days (NWS short-range)
  * predictor.py (this) — what we EXPECT a whole winter to deliver, learned from history

The planning question ("size the pile for next winter") is months beyond any weather
forecast, so a forecast cannot answer it. This module learns expected MONTHLY snowfall
from observed history with a scikit-learn gradient-boosted QUANTILE regression, and
reports a PROJECTION BAND (expected + low/high) — never a false single-number forecast.

Honesty (per HACKATHON_CONTEXT.md): the band IS the message. A climatology baseline
(30-yr-normal mean +/- std) is included and used automatically as a fallback for any
station/month the model was not trained on.

SI convention: snowfall is handled in METERS internally, consistent with noaa.py /
forecast.py (convert to inches/mm only at display edges).
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from .noaa import BOSTON_LOGAN_GHCND, INCH_TO_METER

# Snow-to-liquid ratio: ~10:1 (NWS rule of thumb). Depth -> water-equivalent.
DEFAULT_SNOW_TO_LIQUID_RATIO = 10.0

# Boston Logan station metadata (lat, elevation m), used as model features.
BOSTON_LOGAN_LATITUDE = 42.3606
BOSTON_LOGAN_ELEVATION_M = 6.0


@dataclass(frozen=True)
class MonthlySnow:
    """One month of observed snowfall at a station (a training row).

    `snow_m` is snowfall DEPTH in meters (SI). Build these from noaa.py pulls or
    an ACIS monthly query.
    """

    station: str
    year: int
    month: int                 # 1-12
    snow_m: float              # snowfall depth that month, meters
    latitude: float = BOSTON_LOGAN_LATITUDE
    elevation_m: float = BOSTON_LOGAN_ELEVATION_M

    def __post_init__(self) -> None:
        if not 1 <= self.month <= 12:
            raise ValueError("month must be in 1..12")
        if self.snow_m < 0:
            raise ValueError("snow_m must be >= 0")


@dataclass(frozen=True)
class SnowPrediction:
    """Predicted snowfall for one (station, month), as a band.

    All depths in METERS. `expected` is the central estimate; `low`/`high` bound
    the projection band (default ~80% interval).
    """

    station: str
    month: int
    expected_m: float
    low_m: float
    high_m: float
    model: str
    snow_to_liquid_ratio: float = DEFAULT_SNOW_TO_LIQUID_RATIO

    def _depth(self, which: str) -> float:
        return {"expected": self.expected_m, "low": self.low_m, "high": self.high_m}[which]

    def water_equivalent_m(self, which: str = "expected") -> float:
        """Liquid-water-equivalent depth (meters) of the predicted snow depth."""
        return self._depth(which) / self.snow_to_liquid_ratio

    def water_equivalent_mass_kg(
        self, collection_area_m2: float, which: str = "expected"
    ) -> float:
        """Collectible water-equivalent MASS over a collection area.

        mass = water_equiv_depth(m) * area(m^2) * density_water(1000 kg/m^3).
        This mass is what the engine's cooling math consumes (see snow.py).
        """
        if collection_area_m2 < 0:
            raise ValueError("collection_area_m2 must be >= 0")
        return self.water_equivalent_m(which) * collection_area_m2 * 1000.0


# ---------------------------------------------------------------------------
# Predictor interface
# ---------------------------------------------------------------------------


class SnowfallPredictor(ABC):
    """Given a station and months, predict monthly snowfall (meters)."""

    name: str = "abstract"

    @abstractmethod
    def predict_month(self, station: str, month: int) -> SnowPrediction: ...

    def predict_season(
        self, station: str, months: Sequence[int]
    ) -> list[SnowPrediction]:
        return [self.predict_month(station, m) for m in months]

    def predict_year(self, station: str) -> list[SnowPrediction]:
        return self.predict_season(station, range(1, 13))


# ---------------------------------------------------------------------------
# Climatology baseline (no ML) — trustworthy fallback / sanity anchor
# ---------------------------------------------------------------------------


@dataclass
class ClimatologyPredictor(SnowfallPredictor):
    """Each month = its historical mean, with a +/- k*std band (meters).

    `normals` maps station -> {month: (mean_m, std_m)}.
    """

    normals: dict[str, dict[int, tuple[float, float]]]
    band_sigma: float = 1.28155  # ~80% interval for a normal distribution
    name: str = field(default="climatology", init=False)

    def predict_month(self, station: str, month: int) -> SnowPrediction:
        # Graceful default: unknown station/month -> zero (honest "no evidence").
        if station not in self.normals or month not in self.normals.get(station, {}):
            return SnowPrediction(station, month, 0.0, 0.0, 0.0, self.name)
        mean, std = self.normals[station][month]
        half = self.band_sigma * std
        return SnowPrediction(
            station=station,
            month=month,
            expected_m=mean,
            low_m=max(0.0, mean - half),
            high_m=mean + half,
            model=self.name,
        )

    @classmethod
    def from_history(cls, records: Sequence[MonthlySnow], **kwargs) -> "ClimatologyPredictor":
        buckets: dict[str, dict[int, list[float]]] = {}
        for r in records:
            buckets.setdefault(r.station, {}).setdefault(r.month, []).append(r.snow_m)
        normals: dict[str, dict[int, tuple[float, float]]] = {}
        for station, months in buckets.items():
            normals[station] = {}
            for month, vals in months.items():
                mean = sum(vals) / len(vals)
                if len(vals) > 1:
                    var = sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)
                    std = math.sqrt(var)
                else:
                    std = 0.0
                normals[station][month] = (mean, std)
        return cls(normals=normals, **kwargs)


# ---------------------------------------------------------------------------
# ML predictor — the "AI model"
# ---------------------------------------------------------------------------


def _features(month: int, latitude: float, elevation_m: float) -> list[float]:
    """Cyclical month encoding + geography, so the model learns seasonality smoothly."""
    angle = 2.0 * math.pi * (month - 1) / 12.0
    return [math.sin(angle), math.cos(angle), float(month), latitude, elevation_m]


@dataclass
class MLSnowfallPredictor(SnowfallPredictor):
    """Gradient-boosted QUANTILE regression predicting monthly snowfall (meters).

    Trains three models (low / median / high quantile) so output is an honest band.
    Falls back to climatology for stations the model never saw. Requires scikit-learn.
    """

    model_median: object
    model_low: object
    model_high: object
    station_meta: dict[str, tuple[float, float]]   # station -> (lat, elev)
    fallback: ClimatologyPredictor | None = None
    name: str = field(default="ml-hgb-mean+quantile-band", init=False)

    @classmethod
    def train(
        cls,
        records: Sequence[MonthlySnow],
        low_quantile: float = 0.1,
        high_quantile: float = 0.9,
        random_state: int = 0,
    ) -> "MLSnowfallPredictor":
        from sklearn.ensemble import HistGradientBoostingRegressor

        X = [_features(r.month, r.latitude, r.elevation_m) for r in records]
        y = [r.snow_m for r in records]

        def _fit_quantile(quantile: float):
            m = HistGradientBoostingRegressor(
                loss="quantile",
                quantile=quantile,
                random_state=random_state,
                max_iter=300,
                learning_rate=0.05,
            )
            m.fit(X, y)
            return m

        # Central "expected" estimate uses the MEAN (squared-error loss), not the
        # median. Monthly snowfall is heavily right-skewed with many low months,
        # so a 0.5-quantile median collapses toward zero even in winter. The mean
        # is the meaningful planning number ("how much snow on an average year").
        model_mean = HistGradientBoostingRegressor(
            loss="squared_error",
            random_state=random_state,
            max_iter=300,
            learning_rate=0.05,
        )
        model_mean.fit(X, y)

        return cls(
            model_median=model_mean,                 # "expected" = mean
            model_low=_fit_quantile(low_quantile),
            model_high=_fit_quantile(high_quantile),
            station_meta={r.station: (r.latitude, r.elevation_m) for r in records},
            fallback=ClimatologyPredictor.from_history(records),
        )

    def predict_month(self, station: str, month: int) -> SnowPrediction:
        if not 1 <= month <= 12:
            raise ValueError("month must be in 1..12")
        if station not in self.station_meta:
            if self.fallback is not None:
                return self.fallback.predict_month(station, month)
            raise KeyError(f"unknown station {station!r} and no fallback set")

        lat, elev = self.station_meta[station]
        feats = [_features(month, lat, elev)]
        expected = max(0.0, float(self.model_median.predict(feats)[0]))
        low = float(self.model_low.predict(feats)[0])
        high = float(self.model_high.predict(feats)[0])
        # Snow depth cannot be negative; keep the band ordered.
        low = max(0.0, min(low, expected))
        high = max(expected, high)
        return SnowPrediction(station, month, expected, low, high, self.name)

    # -- persistence --------------------------------------------------------
    def save(self, path: str | Path) -> None:
        import joblib

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "model_median": self.model_median,
                "model_low": self.model_low,
                "model_high": self.model_high,
                "station_meta": self.station_meta,
                "fallback_normals": self.fallback.normals if self.fallback else None,
            },
            path,
        )

    @classmethod
    def load(cls, path: str | Path) -> "MLSnowfallPredictor":
        import joblib

        blob = joblib.load(path)
        fallback = (
            ClimatologyPredictor(normals=blob["fallback_normals"])
            if blob.get("fallback_normals")
            else None
        )
        return cls(
            model_median=blob["model_median"],
            model_low=blob["model_low"],
            model_high=blob["model_high"],
            station_meta=blob["station_meta"],
            fallback=fallback,
        )


# ---------------------------------------------------------------------------
# Seed history (realistic stand-in) so the model trains without live NOAA access
# ---------------------------------------------------------------------------

# Boston Logan monthly snowfall normals (INCHES, ~1991-2020). Summer ~0.
_BOSTON_NORMALS_INCHES = {
    1: 14.2, 2: 12.6, 3: 8.1, 4: 1.2, 5: 0.0, 6: 0.0,
    7: 0.0, 8: 0.0, 9: 0.0, 10: 0.1, 11: 1.3, 12: 9.0,
}


def history_from_acis(
    station: str = BOSTON_LOGAN_GHCND,
    start_month: str = "1991-07",
    end_month: str = "2024-06",
) -> list[MonthlySnow]:
    """Fetch REAL observed monthly snowfall from ACIS and return training rows.

    This is the production training data path: live NOAA GHCN-Daily monthly
    totals via noaa.py, converted into MonthlySnow (meters, with real station
    latitude/elevation). Requires network access to data.rcc-acis.org.
    """
    from .noaa import fetch_monthly_snowfall

    records = fetch_monthly_snowfall(start_month, end_month, station=station)
    return [
        MonthlySnow(
            station=r.station,
            year=r.year,
            month=r.month,
            snow_m=round(r.snow_meters, 4),
            latitude=r.latitude,
            elevation_m=r.elevation_m,
        )
        for r in records
    ]


def seed_history(
    station: str = BOSTON_LOGAN_GHCND,
    start_year: int = 1991,
    end_year: int = 2023,
    seed: int = 42,
    cv: float = 0.55,
) -> list[MonthlySnow]:
    """Generate a realistic SEED monthly history (meters) for a station.

    Anchored to Boston Logan's published normals with log-normal year-to-year
    variability (Boston snowfall swings hard). Replace with real ACIS monthly
    pulls (via noaa.py / MCP) and retrain — same MonthlySnow shape, no code change.
    """
    import random

    rng = random.Random(seed)
    sigma = math.sqrt(math.log(1.0 + cv * cv))
    out: list[MonthlySnow] = []
    for year in range(start_year, end_year + 1):
        for month, normal_in in _BOSTON_NORMALS_INCHES.items():
            mean_m = normal_in * INCH_TO_METER
            if mean_m <= 0:
                depth = 0.0
            else:
                mu = math.log(mean_m) - 0.5 * sigma * sigma
                depth = max(0.0, math.exp(rng.gauss(mu, sigma)))
            out.append(MonthlySnow(station, year, month, round(depth, 4)))
    return out


# ---------------------------------------------------------------------------
# Shared accessor — one trained predictor for the API / MCP server to reuse
# ---------------------------------------------------------------------------

# Default on-disk location for a trained model (optional; gitignored *.joblib).
DEFAULT_MODEL_PATH = Path(__file__).with_name("snowfall_model.joblib")

_CACHED_PREDICTOR: SnowfallPredictor | None = None


def get_predictor(model_path: str | Path | None = None) -> SnowfallPredictor:
    """Return a ready-to-use snowfall predictor, trained/loaded once and cached.

    Resolution order:
      1. A saved model at `model_path` (or DEFAULT_MODEL_PATH) if it exists.
      2. Otherwise train an MLSnowfallPredictor on the seed history (fast, ~2s)
         and cache it in-process.

    Used by api/main.py and mcp_server so they share a single model instance.
    """
    global _CACHED_PREDICTOR
    if _CACHED_PREDICTOR is not None:
        return _CACHED_PREDICTOR

    path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
    if path.exists():
        _CACHED_PREDICTOR = MLSnowfallPredictor.load(path)
    else:
        _CACHED_PREDICTOR = MLSnowfallPredictor.train(seed_history())
    return _CACHED_PREDICTOR


def season_total_water_equivalent_m(
    predictor: SnowfallPredictor,
    station: str,
    collection_months: Sequence[int],
    which: str = "expected",
) -> float:
    """Sum predicted water-equivalent snowfall DEPTH (meters) over given months.

    This is the bridge into the engine's collection math: the result is a
    liquid-water-equivalent depth that snow.py / seasonal.py can turn into mass.
    """
    return sum(
        p.water_equivalent_m(which)
        for p in predictor.predict_season(station, collection_months)
    )
