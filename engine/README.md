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

## Partner boundary
The data center's heat usage / current footprint is produced by the **footprint** package
(see `../footprint/`). This engine CONSUMES that output through a small typed interface
(`engine/interfaces.py`) so the two halves can be built independently. See that file for the contract.

## Principles
- SI units internally; convert at the edges for display.
- Every assumption is an explicit, documented input with a sensible default — no hidden magic numbers.
- Pure functions where possible => clean property-based tests (Hypothesis).
