# Perennial — 3-Minute Demo Video Script

Target under 3:00. Record screen with OBS / Windows Game Bar (Win+G) / Loom, narrate over it,
upload to YouTube (public). Live app: https://perennial-murex.vercel.app

Tip: do a dry run first and pick a snowy date (2015-02-10) before recording so no screen shows "0 mm".

---

## 0:00–0:20 — Hook (hero + the problem)
**Screen:** The Perennial landing page (logo + "Winter's cold, kept for summer").
**Say:** "In 2015, Boston plowed a record winter into a 75-foot mountain of snow that didn't melt
until July. That cold was wasted. Meanwhile, AI data centers drank 17 billion gallons of fresh
water last year just to stay cool. Perennial connects those two problems."

## 0:20–0:45 — The idea (City view)
**Screen:** Click "I'm a City." Show the snow-farm map and pick the 2015 blizzard date (25.3 in).
**Say:** "Cities already pile snow that survives into summer. Perennial tracks that supply, real
NOAA snowfall for any date you pick, and the date you choose feeds the calculator directly."

## 0:45–1:25 — The hero: peak shaving (Calculator)
**Screen:** Go to Calculator. Drag the month slider Jan→Aug. Show the chart (demand rising, snow
coverage), then the savings stats (water, CO₂), then the water→carbon chain.
**Say:** "Here's the clever part: collect cold in winter, spend it in summer. Watch the pile build,
then shave the July-August peak, when cooling towers drink the most. For a typical Boston winter,
stored snow covers over 70% of peak-month cooling. And this chain shows how the same cold saves
BOTH fresh water and the chiller electricity, which is where the carbon saving comes from."

## 1:25–1:55 — Show your work + the AI (Calculator)
**Screen:** Click "Show the math" (step-by-step derivation). Then open "✦ Ask AI" and type
"what if we double collection efficiency?" — show the AI changing the input and the numbers update.
**Say:** "Every number is auditable, step by step, from NOAA snowfall to CO₂. And the built-in
Claude assistant can run what-ifs for you, it changes the inputs and the whole model updates live."

## 1:55–2:20 — The business case (Dashboard)
**Screen:** Go to Dashboard. Show the KPI cards and carbon-credit value, then the PDF download.
**Say:** "Boston spends 47 million dollars a year getting rid of snow. Perennial lets the city sell
that cold instead, and gives each GPU data center a carbon-negative cooling source it can report
toward its 2030 water and carbon goals, as a one-page PDF."

## 2:20–2:45 — The engineering + Kiro (Logic)
**Screen:** Go to Logic. Show the shell-and-tube cooler schematic and the formulas.
**Say:** "The cooler is a real shell-and-tube design, dirty snow and clean coolant never mix. We
built Perennial spec-first in Kiro: steering docs kept every number sourced, a custom MCP server
pulled live NOAA, NWS, and USGS data, and property-based tests caught a 24-times error our eyes
missed."

## 2:45–3:00 — Close (scale)
**Screen:** Back to the map or hero.
**Say:** "Montreal, Minneapolis, Buffalo, Hokkaido, every cold city has this same wasted asset.
Perennial turns winter into a climate resource, exactly where AI is growing fastest. Thank you."

---

## Checklist
- [ ] Pre-set a snowy date so no "0 mm" shows on camera.
- [ ] Confirm the AI assistant is live (set ANTHROPIC_API_KEY on Vercel) OR demo the scripted guide.
- [ ] Show: hero, City (date→snowfall), Calculator (slider + math + AI), Dashboard (PDF), Logic (schematic).
- [ ] No copyrighted music. Keep under 3:00.
- [ ] Upload PUBLIC to YouTube; put the link on the submission form.
