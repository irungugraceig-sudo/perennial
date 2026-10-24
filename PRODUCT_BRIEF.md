# Perennial — One-Page Product Brief

The agreed shape of the product. This is the basis for the Kiro spec. Keep it to one page.

## What Perennial is
Perennial connects the people who **have snow** with the people who **need cold**.
- The **city** has the snow. It wants to know where the most snow is and what it's worth.
- The **GPU data center** has the heat. It wants to know how much it can save, now and as it grows.
- Perennial sits in the middle and does the math for both, and brokers the deal.

## Who it's for (the customer = anyone running GPUs)
GPU-heavy data centers are the target: hottest machines, fastest-growing water problem, and many
already run liquid cooling (a warm-water loop a shell-and-tube exchanger plugs into easily). Types:
- Big cloud (AWS, Google, Microsoft) — used here as example footprints from published PUE/WUE.
- GPU cloud providers renting AI compute.
- Colocation centers (e.g. Markley, Boston) renting to AI tenants — often evaporative cooling, big water savings.
- University/research HPC (e.g. Mass Green HPC Center, Holyoke — and western MA gets more snow).
One-liner: "Perennial is built for GPU-heavy data centers — the hottest machines with the
fastest-growing water problem."

## The decision each user makes
- City: "Where is my snow, and what is it worth?"
- Data center: "How much can I save now, and as I expand?"

## The app = three views
1. **City view — "Where is the snow?"**
   Live snowfall this season (NOAA), the coming week (NWS forecast), and terrain-predicted hotspots
   where the most snow collects and lasts (USGS). Tracking, no trucks. Shows how much snow Boston has
   and where. Two hotspot layers: city snow-farms + terrain-predicted high-snow spots.
2. **Data center view — "How much can I save?"**
   The Schneider-style calculator. Pick/type a facility (example footprints incl. AWS-style
   hyperscaler and Markley-style colo) -> water saved, money saved, % of summer PEAK covered,
   payback years. Plus an **Expansion planner**: "add 5 MW by 2028 -> extra cooling/water needed and
   how much snow can cover" (ties to AI growth projections). Hosts the **Jan->Aug melt timeline** —
   the memorable moment: piles shrinking while they cool the servers.
3. **Impact view — "Why it matters"**
   AI water use rising to 2030 vs. what snow could offset across Boston, then other snowy cities.
   The pitch slide, built into the app.

## Money model (believable, not perfect)
- Data centers pay a **subscription** for the calculator + expansion planner (main revenue; they
  have budgets and a water problem, and public 2030 water/carbon pledges to hit).
- City uses the tracker free/low-cost; in return gets a new **revenue stream**: sell stored cold
  instead of paying to dump snow.
- Perennial takes a **small fee on each cold-as-a-service contract** between city and data center.
- Pitch line: "Boston pays $47M a year to get rid of snow. Perennial helps Boston sell it instead."

## Positioning / honesty guardrails
- Don't claim "AWS wastes water" (their WUE ~0.12-0.15 L/kWh is excellent). Pitch hyperscalers on
  summer peak energy/carbon savings + a new sustainable-cooling source toward their 2030 water goals.
  Pitch older/colo facilities (evaporative, ~1.8 L/kWh) on big water savings.
- Complementary to cold-climate siting AWS already uses (Ireland/Sweden: no cooling water >95% of
  year). Perennial = "you use winter's cold AIR; we store winter's cold for summer."
- Snow cooling is seasonal/finite: report FRACTION of demand + peak-month offset, never 100%.

## The demo moment
Scrub the Jan->Aug slider: pile builds in winter, then shaves the July/August cooling peak.

## Build mapping (reuse what exists)
- Forecast tab -> City view. Calculator -> Data center view. Hotspots -> City map (farms + terrain).
- NEW: expansion planner, impact view, money numbers, AWS-style example footprint.

## Hackathon cautions
- Rules: no financial/preferential support from a Sponsor (AWS is a backer) before submission ends.
  Naming AWS as an example customer in the pitch is fine; do NOT solicit AWS investment/support pre-submission.
- Amazon co-op: check the co-op agreement / manager on outside projects touching Amazon's business;
  use NO internal info. Perennial uses only public data.
