# Perennial Data — MCP server

Exposes Perennial's three public data sources as Model Context Protocol tools so Kiro (or any
MCP client) can explore and validate the data during development. The tools call the same engine
functions the app uses, so "how we built it" and "what it does" share one data layer.

## Tools
- `noaa_seasonal_snowfall(start, end, station)` — observed snowfall totals (NOAA GHCN-Daily via ACIS).
- `nws_snow_forecast(lat, lon)` — upcoming snowfall + periods (US National Weather Service).
- `usgs_terrain(lat, lon)` — elevation, slope, aspect (USGS 3DEP) for snow-persistence scoring.

## Run standalone (stdio)
```
python -m mcp_server.perennial_data
```

## Register with Kiro
Copy `mcp.config.example.json` into your workspace MCP settings at
`.kiro/settings/mcp.json` (or merge the `perennial-data` entry into an existing file).
Reconnect the server from the Kiro MCP panel. Then Kiro can call the tools directly, e.g.
"use noaa_seasonal_snowfall for Boston Logan, Nov 2014 to Apr 2015" to verify the record winter.

Requires the `mcp` package (see repo `requirements.txt`).
