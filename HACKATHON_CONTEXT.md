# Hackachusetts — Project Context

This document is the source of truth for our hackathon submission. Everything we build
should trace back to these rules and judging criteria.

## Tracks (choose ONE)
- Healthcare & Biotech
- Robotics & Hardware
- ClimateTech & Clean Energy
- Civic Services

## Hard Submission Requirements
- Team: up to 4 members; appoint one authorized **Representative**.
- **Must genuinely use Kiro to build the project.** Insufficient use = disqualification (judges' discretion).
- Must fit one of the four challenge tracks (and explicitly identify which).
- **Text description** explaining features and functionality.
- **Demo video**:
  - < 3 minutes (judges may stop watching at 3:00).
  - Must show the project actually functioning on its target device.
  - Publicly visible on YouTube, Vimeo, Facebook Video, or Youku; link provided on submission form.
  - No third-party trademarks or copyrighted music/material without permission.
- **Public GitHub repo** with all source code, assets, and setup/run instructions.
- **`.kiro/` folder MUST be committed at the repo root. Never add `/.kiro` (or subfolders) to `.gitignore` — doing so can disqualify the submission.**
- **Kiro write-up** — show depth across:
  - Kiro tools used (IDE, CLI, Web, Crew) and how they differed.
  - Spec-driven development: how the spec was structured; how it improved the process vs. vibe coding.
  - Agent hooks: which workflows were automated and the benefit.
  - Steering docs: how steering shaped Kiro's responses; the highest-impact strategy.
  - MCP: how extending Kiro enabled otherwise-hard/impossible features.
  - Property-based testing (PBT): issues caught that unit tests missed; which requirements got PBT.
  - Kiro powers: which powers/bundled expertise or third-party integrations were used.
- Original work, solely owned, no IP violations. Open source allowed if licenses respected AND we build meaningfully on top.
- English (or provide English translations of video, description, testing instructions, all materials).
- **Testing access**: judges must be able to test for free, unrestricted, until judging ends (include credentials if private).
- No changes after the Submission Period ends (limited exceptions for IP/PII/inappropriate content).
- No financial/preferential support from Sponsor/Administrator.

## Judging Criteria (3 axes)
1. **Potential Value** — Solves a real, clearly defined problem in a scalable, realistic way.
   - Market uniqueness vs. saturation.
   - Genuine consideration for accessibility, equity, adoption.
   - Compelling pitch: who benefits, how it scales beyond the hackathon.
2. **Implementation** — How effectively and creatively Kiro was used.
   - Variety of Kiro tools (IDE, CLI, Web, Crew), features, capabilities.
   - Depth of understanding/benefit from each feature.
   - Experimentation and strategic decisions in the dev workflow.
3. **Quality & Design** — Creativity, originality, polished/intentional design.
   - Unique public resources/datasets.
   - Surprising combinations of tech.
   - Intuitive UI that elevates functionality.

## Prizes
- Each track: 1st $3,500 / 2nd $1,000 / 3rd $500 (split across team).
- **Best Use of Kiro** (bonus): 1-Year Kiro Pro Max (~$1,200). Awarded to the highest **Implementation** score that is also in the top 10% of projects.
- **Top 50 Finalists**: WHOOP straps.
- A project can win one (1) overall track prize AND up to two (2) bonus prizes.
- Top winners meeting eligibility (18+, 1 general-purpose language, enrolled in a CS/STEM Bachelor's+) earn an AWS interview.

## Strategy Notes (ours)
- Win **Implementation / Best Use of Kiro** by deliberately using and documenting: specs, hooks, steering, MCP, PBT, and powers — not just one of them.
- Commit `.kiro/` early and correctly; verify it is NOT gitignored before every push.
- Target a real, specific user with a believable scaling story (Potential Value).
- Invest in a polished, intuitive UI and a unique dataset (Quality & Design).
- Keep the demo tight: show it running, hit the problem→solution story in under 3 minutes.

## Decisions (locked)
- **Name: Perennial** — evokes snow that survives the melt season ("perennial snow" is the real
  glaciological term). Meaning: winter's cold, kept alive into summer.
- **Track: Energy & Climate Tech**
- **Core idea:** Turn a city's discarded snow into clean cooling for data centers. Calculate
  snowfall, plan collection/storage, and quantify the fresh water + energy + CO2 offset when
  stored snow cools a data center through summer. Grounded in the proven Sundsvall (Sweden)
  snow-storage plant, operating since 2000.
- **Demo region:** Massachusetts / Boston (ties to Hackachusetts + their open data portal).
- Team / Representative: _TBD_
- Repo URL: _TBD_
- Tech stack: _proposed_ React + TypeScript + map lib (Leaflet/MapLibre) front end; Python
  (FastAPI) engine for physics/offset (clean Hypothesis PBT story). _Confirm._

## The Core Mechanism (stated correctly — judges will check)
Perennial is NOT about turning snow into water for water's sake. It's about **harvesting cold.**
- Melting ice does not generate heat — it **ABSORBS** heat (334 kJ/kg) while staying at 0 C.
- We circulate the data center's warm coolant through a heat exchanger at an insulated ice pile.
  The melting ice absorbs the data center's waste heat; the coolant returns cold to the servers.
- **The cold is the product. The meltwater is just spent coolant** (return to storm drain / reuse).
  That is a stronger story than "use snow instead of water" — we consume no fresh water at all.

### The Boston proof (local hook)
- The 2015 "Boston snow farm" in the Seaport: city plowed record 110+ inch winter snow into a
  ~75 ft pile. It survived until **July 14** because a coating of dirt/debris insulated it near
  32 F and blocked the sun. Boston already creates summer-surviving ice piles by accident —
  Perennial harvests that wasted cold instead of letting it melt in a parking lot.

### Physics constants
- Latent heat of fusion of ice ~= 334 kJ/kg => 1 tonne of ice melting absorbs ~334 MJ ~= 93 kWh
  of cooling ("cold").
- **Snow is mostly air; ice is mostly water.** Fresh snow ~50-100 kg/m3 (5-10% water);
  settled snow ~200-400 kg/m3; compacted/old pile ~500-700 kg/m3; solid ice 917 kg/m3.
- Cooling depends on **water-equivalent MASS, not density**. Density only matters for logistics.
- Insulated piles (dirt in Boston 2015, wood chips in Sundsvall) keep melt losses to ~20-30%.

### Engine pipeline (three stages)
1. **Collection accounting:** snow cleared (depth x area x fresh-snow density) -> water-equivalent mass piled.
2. **Preservation/losses:** insulation limits summer melt; apply melt-loss factor (~20-30%) -> surviving ice mass by summer.
3. **Cooling delivery + offset:** surviving mass x 334 kJ/kg -> cold delivered to data center ->
   chiller kWh avoided + fresh water (evaporation) avoided + CO2 avoided.

## Data Layer (Hackachusetts open-data portal + MCP)
Judges reward using unique public datasets. Use the portal's own data where possible.
- **Offset target — Boston BERDO 2021** (data.boston.gov): 2,472 large buildings; energy use,
  area, GHG. Model a data-center-class load against real Boston buildings. (No street address.)
  URL: https://data.boston.gov/api/3/action/datastore_search?resource_id=43e4abc9-1fae-40d9-a02e-ff950bd0e732&fields=Property_Type,Zip,Year_Built,Gross_Area_sf,Site_EUI_kBtuft2,ENERGY_STAR_Score,GHG_Emissions_MTCO2e,GHG_Intensity_kgCO2sf,per_Electricity,per_Gas&limit=100
- **Grid context — Electric utility by town** (MassGIS, 351 rows): who delivers the electrons.
  URL: https://arcgisserver.digital.mass.gov/arcgisserver/rest/services/AGOL/ElectricityProviders/MapServer/0/query?where=1%3D1&outFields=TOWN,ELEC,ELEC_LABEL&returnGeometry=false&f=json
- **Clean capacity — Renewables at MA landfills** (MassGIS, 116 rows): nearby solar on "empty" land.
  URL: https://arcgisserver.digital.mass.gov/arcgisserver/rest/services/DEP/RenewablesAtMaLandfills/MapServer/0/query?where=1%3D1&outFields=MUNICIPALITY,FACILITY,TYPE_,MW_PERMITTED,MW_OPERATING,STATUS_1,OPERATING_SINCE&returnGeometry=false&f=json
- **Equity — MassGIS Environmental Justice block groups** (2,604 rows): who bears cost / benefits.
  URL: https://arcgisserver.digital.mass.gov/arcgisserver/rest/services/AGOL/EJ2020/MapServer/0/query?where=EJ%3D%27Yes%27&outFields=MUNICIPALITY,TOTAL_POP,PCT_MINORITY,LIMENGHHPCT,BG_MHHI,EJ,EJ_CRIT_DESC&returnGeometry=false&resultRecordCount=100&f=json
- **Optional watershed stress — USGS Charles River flow** (366 rows).
  URL: https://waterservices.usgs.gov/nwis/dv/?format=json&sites=01104500&parameterCd=00060&startDT=2024-01-01&endDT=2024-12-31
- **Snowfall (the gap) — NOAA climate data via MCP.** Portal has no snow dataset, so pull MA
  snowfall from NOAA (NWS/NCEI) through an MCP server. Doubles as the MCP write-up story.
- Citation rule: cite the agency/program for every dataset; link official pages, don't rehost.

## Platform = Three Layers
Thesis: **move data-center cooling from an OPEN loop (bleeds fresh water via evaporative towers)
to a CLOSED loop (borrows winter's cold from stored snow). The meltwater is spent coolant, not
consumed product.**

### Layer 1 — Logistics ("follow the snow")
- Forecast + snowfall (NOAA via MCP) -> estimate snow volume the city clears.
- Replace random roadside dumping with **organized pile sites** near the data center => smoother
  roads AND a usable cold asset. The city already clears; Perennial routes it with purpose.
- Honest framing: clearing happens regardless; Perennial makes WHERE it goes productive.

### Layer 2 — Grounds (real Boston site)
- **Markley Group, One Summer Street, Boston** — Boston's "carrier hotel," largest multi-tenant
  data center in New England, ~99,189 sq ft, 1 Summer Street, downtown. (datacenterjournal / baxtel;
  also appears in a Mass.gov doc.) Use as the concrete demo site.
- Model its cooling load, nearest viable pile sites, closed-loop vs. evaporative comparison.
- Overlay Hackachusetts data: BERDO (building-energy baseline), utility-by-town (grid supplier),
  EJ block groups (who is affected).

### "Why AI?" — make this explicit in app + pitch
- AI heat is huge and growing fastest in regions that throw away free winter cold.
- Cooling is the biggest water sink; dense GPU racks run hot and need constant heat rejection.
- The cold is free and already created (Boston's accidental snow farm).
- Cold-climate siting is already a DC trend (free ambient cooling); Perennial extends it by
  STORING winter cold for the warm months when ambient cooling fails.
- One-liner: "AI's cooling demand is exploding in exactly the regions that discard free cold
  every winter. We match the two."

### Decision features (siting + seasonal matching)
- **Siting map ("where's the snow")**: rank locations by a snow-cooling-potential score =
  snowfall normals + proximity to cooling demand + available pile land (landfill dataset).
  Uses NOAA 30-year CLIMATE NORMALS, not a weather forecast. Label it honestly.
- **Months-of-offset curve**: plot monthly COOLING DEMAND (red, peaks summer, from temperature
  normals) vs. monthly COLD SUPPLY (blue, collected in winter, depletes through summer). Overlap
  = months offset. The phase shift (collect cold in winter, spend in summer) is the whole point
  and is exactly what Sundsvall proves.
- Forward-looking flavor = projection BAND (expected ± variability), never a false point forecast.

### Data source for snow/climate (confirmed available)
- **NOAA NCEI U.S. Climate Normals** — 30-yr averages (latest 1991-2020) of temperature,
  precipitation, AND snowfall for 15,000+ US stations; annual/seasonal/monthly/daily.
  NCEI explicitly frames normals as the basis for decisions beyond forecast range. Pull via MCP.
  - Product: https://www.ncei.noaa.gov/products/land-based-station/us-climate-normals
  - Quick Access: https://www.ncei.noaa.gov/access/us-climate-normals/
  - Access Data Service API: https://www.ncei.noaa.gov/support/access-data-service-api-user-documentation

### Layer 3 — Scaling (the centerpiece / money shot)
- Projection dashboard: AI electricity + heat + water demand rising to 2030 (adjustable sliders
  anchored to real figures below). Overlay the snow-cooling **offset ceiling** at site -> city ->
  region scale. Output e.g. "By 2030 Boston DCs projected to use X gallons; Perennial could offset Y."
- **Report "% of cooling demand offset," NOT "eliminates all water."** Snow cooling is seasonal and
  finite (big in summer, like Sundsvall covering most of a hospital's summer load, not 24/7 hyperscale).
  Showing fractions + open assumptions is what makes every other number credible.

### Scaling figures (citable, authoritative)
- Data centers could reach ~11.8% of US electricity by 2030 (prior est. 6.7-12% by 2028) — LBNL/DOE.
- US DC direct water: ~17B gal (2023) -> LBNL projects 38-73B gal by 2028; hyperscale alone
  16-33B gal/yr by 2028 (DOE/LBNL via Forbes).
- Global DC capacity demand ~22% CAGR; generative-AI workloads alone ~39% CAGR (industry analysis).

## Verified Facts for the Pitch (safe to say on camera)
- US data centers used ~17 billion gallons of water directly for cooling in 2023 (LBNL / DOE).
- A single large data center can use up to ~5 million gallons/day (~a town of 50,000) (Brookings).
- Sundsvall, Sweden hospital has cooled with stored winter snow since 2000; wood-chip insulation
  cuts melt losses to ~20-30%.

## Elevator Pitch (current)
Perennial — turning wasted snow into clean cooling for data centers.
AI data centers consumed ~17 billion gallons of fresh water last year just for cooling; one large
facility can drink as much as a town of 50,000. Meanwhile snowy cities spend millions trucking
snow away as waste. Perennial connects the two: it calculates a city's snowfall, plans collection
and storage, and quantifies the fresh water, energy, and CO2 offset when that stored snow cools a
data center through summer. Proven since 2000 by a Swedish hospital, now with the software to plan
and scale it. Cities cut disposal costs, data centers slash their water footprint, watersheds keep
their water.
