# Perennial — Design

## Overview
A Python calculation engine (pure, SI units) exposed over a FastAPI HTTP layer, with a
React + TypeScript + map frontend. Snow data comes from NOAA via ACIS. The data center's
footprint is produced by a separate `footprint/` package (partner) behind a typed interface.

## Architecture
```
NOAA ACIS (snowfall) ──► engine.noaa ──► engine.snow ──► engine.piles ──┐
                                                                         ├─► engine.viability ──► FastAPI ──► React UI
footprint/ (partner) ──► engine.interfaces.DataCenterFootprint ─────────┘
                           engine.cooling (shell-and-tube) ─┘
```

## Components
- **engine.constants** — fixed thermodynamic constants (latent heat 334 kJ/kg, specific heats, densities).
- **engine.noaa** — ACIS client; observed daily snowfall -> seasonal total (SI).
- **engine.snow** — snowfall -> collected mass (geometric + empirical), adjustable collection efficiency.
- **engine.piles** — SnowPile: mass, passive-loss, available cooling, draw_cooling (energy-conserving).
- **engine.cooling** — HeatExchanger: effectiveness x (1 - fouling) = delivery ratio.
- **engine.offset** — water/energy/CO2 saved; fraction of demand offset (capped at 1.0).
- **engine.interfaces** — DataCenterFootprint, MonthlyCoolingDemand (partner contract).
- **engine.viability** — assess(): one report + verdict.
- **api** — FastAPI app wrapping the engine for the UI.
- **web** — React + TS + MapLibre: Boston snow-farm map + viability calculator panel.
- **footprint/** (partner) — produces DataCenterFootprint; uploads/ drop zone.

## Data models
- `DataCenterFootprint(name, it_load_kw, pue, wue_l_per_kwh, cooling_fraction, grid_co2_kg_per_kwh)`
- `SnowPile(site_name, lat, lon, initial_mass_kg, passive_loss_fraction)`
- `ViabilityReport(footprint_name, annual_cooling_demand_kwh, cooling_delivered_kwh, fraction_offset, offset, verdict)`

## Key decisions
- SI internally, convert at edges. No hidden constants; every assumption is an input with a default.
- Pure functions => property-based tests (Hypothesis) prove invariants.
- Partner boundary via a frozen dataclass so the two halves build in parallel.
- "Live" piles are a model updated on a schedule, not a hardware sensor feed (stated honestly).

## Testing strategy
- Property-based tests for engine invariants (non-negativity, monotonicity, linearity, conservation).
- Offline mock tests for the ACIS parser (markers M/T/None).
- Kiro PostFileSave hook runs the suite on every engine/test edit.
