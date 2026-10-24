# Perennial Engine

The calculation core. Pure Python, no UI. Turns a data center + a location + snow data into a
viability verdict and an offset report.

## Modules
- `constants.py` — fixed physical constants (latent heat, specific heats, densities, unit conversions).
- `snow.py` — snowfall -> collected snow -> water-equivalent mass (two estimation methods).
- `piles.py` — live pile model: mass over time, melt/depletion, insulation loss.
- `cooling.py` — cold available from a pile; shell-and-tube heat-exchanger effectiveness + fouling.
- `offset.py` — fresh water saved, chiller energy avoided, CO2 avoided, % of cooling demand offset.
- `viability.py` — ties it together into a single verdict + report.
- `noaa.py` — real OBSERVED seasonal snowfall via ACIS (NOAA GHCN-Daily), no API key.
- `forecast.py` — short-range (~7 day) snowfall forecast via NWS api.weather.gov.
- `seasonal.py` — monthly supply-vs-demand peak-shaving model (collect cold in winter, spend in summer).
- `predictor.py` — ML seasonal snowfall prediction: learns EXPECTED monthly snowfall (with an
  uncertainty band) from NOAA history. Fills the gap between observed history (`noaa.py`) and the
  7-day forecast (`forecast.py`) — the "how much snow can we expect this season" question.

## The snowfall predictor (`predictor.py`)
A scikit-learn gradient-boosted **quantile** regression (median + low/high models) trained on
observed monthly snowfall. Output is a PROJECTION BAND (expected + low/high), never a false point
forecast. A climatology (30-yr-normal mean ± std) baseline is included as a trustworthy fallback and
is used automatically for stations/months with no learned model.

- Primary station: Boston Logan, GHCN `USW00014739` (code accepts any station).
- Features: cyclical month encoding (sin/cos), month, station latitude, elevation.
- SI internally: snowfall handled in meters; convert at the edges for display.
- Trains on monthly records; swap in the real NOAA GHCN monthly totals (via ACIS/MCP) and retrain
  with no code changes.

## Partner boundary
The data center's heat usage / current footprint is produced by the **footprint** package
(see `../footprint/`). This engine CONSUMES that output through a small typed interface
(`engine/interfaces.py`) so the two halves can be built independently. See that file for the contract.

## Principles
- SI units internally; convert at the edges for display.
- Every assumption is an explicit, documented input with a sensible default — no hidden magic numbers.
- Pure functions where possible => clean property-based tests (Hypothesis).
