"""Train the seasonal snowfall predictor on REAL NOAA data (via ACIS).

Pulls observed monthly snowfall for a station (default Boston Logan) over a
long history, trains the quantile gradient-boosted model, and saves it to
engine/snowfall_model.joblib. The API / MCP server load that saved model
automatically (see engine.predictor.get_predictor); if it is absent they fall
back to the seed history, so this script is how you "go live" on real data.

Usage:
    python -m scripts.train_snowfall_model
    python -m scripts.train_snowfall_model --station USW00014739 \
        --start 1991-07 --end 2024-06
    python -m scripts.train_snowfall_model --offline   # train on seed (no network)
"""

from __future__ import annotations

import argparse

from engine.noaa import BOSTON_LOGAN_GHCND
from engine.predictor import (
    DEFAULT_MODEL_PATH,
    MLSnowfallPredictor,
    history_from_acis,
    seed_history,
)


def main() -> None:
    ap = argparse.ArgumentParser(description="Train Perennial snowfall model on real NOAA data")
    ap.add_argument("--station", default=BOSTON_LOGAN_GHCND)
    ap.add_argument("--start", default="1991-07", help="first month YYYY-MM")
    ap.add_argument("--end", default="2024-06", help="last month YYYY-MM")
    ap.add_argument("--out", default=str(DEFAULT_MODEL_PATH))
    ap.add_argument("--offline", action="store_true",
                    help="train on the seed history instead of fetching ACIS")
    args = ap.parse_args()

    if args.offline:
        print("[data] OFFLINE: using seed history (no network)")
        records = seed_history(station=args.station)
    else:
        print(f"[data] fetching real NOAA snowfall for {args.station} {args.start}..{args.end} (ACIS)")
        records = history_from_acis(args.station, args.start, args.end)

    if not records:
        raise SystemExit("no training records obtained; aborting")

    years = sorted({r.year for r in records})
    print(f"[data] {len(records)} monthly records across {len(years)} years "
          f"({years[0]}-{years[-1]}), lat={records[0].latitude:.3f}, "
          f"elev={records[0].elevation_m:.1f} m")

    model = MLSnowfallPredictor.train(records)
    model.save(args.out)
    print(f"[model] trained on real data and saved -> {args.out}")

    print("\nPredicted monthly snowfall (m): expected [low, high]")
    for p in model.predict_year(args.station):
        print(f"  month {p.month:2d}: {p.expected_m:.3f} [{p.low_m:.3f}, {p.high_m:.3f}]")


if __name__ == "__main__":
    main()
