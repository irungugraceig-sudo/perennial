# Perennial — Requirements

## Introduction
Perennial is a viability calculator (in the spirit of Schneider Electric's TradeOff Tools) that
quantifies how much of a data center's cooling can be offset by harvesting a city's discarded
snow. It moves cooling from an open loop (evaporative towers that consume fresh water) to a
closed loop (a shell-and-tube heat exchanger that borrows winter's cold from stored snow piles).
Demo region: Boston, MA. Track: Energy & Climate Tech (Hackachusetts 2026).

## Requirements

### Requirement 1 — Snow supply from real data
**User story:** As a city planner, I want the tool to use real snowfall for my city, so the
numbers reflect actual winters.
#### Acceptance criteria
1. WHEN a season is selected THEN the system SHALL fetch observed daily snowfall for the station
   (default Boston Logan) from NOAA GHCN-Daily via the ACIS API.
2. WHEN snowfall is totaled THEN the system SHALL handle missing (M), trace (T), and null values
   without error.
3. The system SHALL convert all snowfall to SI (meters) internally.

### Requirement 2 — Collected-snow estimation (honest)
**User story:** As a skeptical judge, I want to see that the tool distinguishes snow that falls
from snow that is actually collected.
#### Acceptance criteria
1. The system SHALL estimate collected mass by two independent methods (geometric and empirical)
   and present both for cross-check.
2. The system SHALL expose collection efficiency as an adjustable input, never a hidden constant.
3. Collected mass SHALL be non-negative and linear in collection area.

### Requirement 3 — Live pile tracking
**User story:** As an operator, I want to see snow piles deplete over time, so I can plan the season.
#### Acceptance criteria
1. The system SHALL model each snow-farm site as a pile with mass, location, and passive-loss factor.
2. A pile SHALL never deliver more cooling than its usable mass holds (energy conservation).
3. Drawing cooling SHALL reduce pile mass and never drive it negative.

### Requirement 4 — Heat-exchanger model
**User story:** As an engineer, I want the dirty snow and clean coolant kept separate, so the
ultrapure loop is never contaminated.
#### Acceptance criteria
1. The system SHALL model a shell-and-tube exchanger with effectiveness and a fouling factor.
2. Delivered cooling SHALL never exceed the pile's available cooling.

### Requirement 5 — Offset accounting
**User story:** As a sustainability lead, I want to know water, energy, and CO2 saved.
#### Acceptance criteria
1. The system SHALL compute fresh water saved (gallons/liters), chiller energy avoided (kWh),
   and CO2 avoided (kg), using the data center's WUE and grid carbon intensity.
2. The system SHALL report the FRACTION of cooling demand offset, capped at 100%.
3. All offset outputs SHALL be non-negative; more cooling SHALL never reduce savings.

### Requirement 6 — Partner boundary (footprint)
**User story:** As a two-person team, we want to build the footprint half and the engine half in
parallel without collisions.
#### Acceptance criteria
1. The engine SHALL consume the data center footprint through a stable typed interface
   (DataCenterFootprint) and SHALL NOT depend on how those numbers are produced.
2. The engine SHALL run end-to-end with placeholder footprint values before the footprint package
   is complete.

### Requirement 7 — API + UI
**User story:** As a user, I want an interactive map and calculator in the browser.
#### Acceptance criteria
1. The system SHALL expose the engine via an HTTP API (snowfall, piles, viability assessment).
2. The UI SHALL show Boston's snow-farm sites on a map and a viability panel with adjustable
   inputs and the offset results.

### Requirement 8 — Quality gates
#### Acceptance criteria
1. Core engine invariants SHALL be covered by property-based tests (Hypothesis).
2. The test suite SHALL run automatically on save via a Kiro hook.
