# Footprint (Partner: heat usage & current footprint)

**Owner:** @WendellR3

This package is YOUR space. It produces the data center's current heat usage and resource
footprint. The engine half consumes your output through a small, stable contract so we can build
in parallel without stepping on each other.

## What this package must produce
A `DataCenterFootprint` object (see `../engine/interfaces.py` for the exact fields). In short:
- `name` — the facility (e.g. Markley, One Summer Street, Boston)
- `it_load_kw` — IT electrical load in kW
- `pue` — Power Usage Effectiveness
- `wue_l_per_kwh` — Water Usage Effectiveness (liters water per kWh IT)
- `cooling_fraction` — fraction of facility power used for cooling
- `grid_co2_kg_per_kwh` — grid carbon intensity for the site's utility

Optional (nice to have): a monthly cooling-demand curve (`MonthlyCoolingDemand` list).

## Where to put your work
- Code: anywhere in this `footprint/` folder.
- Raw data you download (BERDO rows, PUE/WUE references, grid-intensity figures, your
  calculations/spreadsheets): drop into `footprint/uploads/`. See that folder's README.

## How to hand off to the engine
Expose a function that returns a `DataCenterFootprint`, e.g.:

```python
# footprint/markley.py
from engine.interfaces import DataCenterFootprint

def markley_footprint() -> DataCenterFootprint:
    return DataCenterFootprint(
        name="Markley - One Summer Street, Boston",
        it_load_kw=...,      # your number
        pue=...,             # your number
        wue_l_per_kwh=...,   # your number
        cooling_fraction=...,
        grid_co2_kg_per_kwh=...,
    )
```

The engine imports that and runs the offset/viability math on it. As long as you return the
right shape, how you get the numbers is entirely up to you.

## Git tip
Work on your own branch (e.g. `footprint`) and open a PR into `main`. Keeps us from clashing.
