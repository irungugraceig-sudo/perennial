# How We Used Kiro to Build Perennial

Perennial (Energy & Climate Tech) was built end to end with Kiro. This is not a feature
checklist, it is how specific Kiro capabilities changed the way the project was built and the
decisions that came out of it.

---

## 1. Kiro tools we used (IDE, CLI, Web, Crew) and how they differed

- **Kiro IDE** was the primary surface. All spec authoring, engine/API/frontend implementation,
  running the property-based tests, debugging the Vercel deploy, and the iterative redesign
  happened here, turn by turn with the agent.
- **Kiro CLI** is what actually powers the agent harness and, notably, is the backend Kiro Crew
  drives through the Agent Client Protocol. Setting up `kiro-cli login` was the key to connecting
  Crew.
- **Kiro Crew** we explored as the autonomous, multi-surface workspace (dashboard at
  `localhost:5476`, CLI, messaging). The distinction we learned: the IDE is pair-programming
  (synchronous, you watch each step), while Crew is delegation (asynchronous, scheduled, runs
  while you are away). That difference shaped where we'd put the product's own recurring jobs
  (e.g. a daily NWS forecast pull to update projected pile mass).

The practical takeaway: the IDE for building and tight iteration; the CLI/Crew for unattended,
scheduled work that mirrors the product's own logic.

## 2. Spec-driven development vs. vibe coding

We did both, deliberately, and the contrast was the most instructive part of the project.

- **Vibe-coded v0:** the first engine pass was built conversationally, fast, no spec. It produced
  a collection estimate that was **24× off** between two methods (993,723 t vs. 40,827 t). We only
  caught it because the property-based tests and a cross-check surfaced the mismatch, not because
  we read the code carefully.
- **Spec-driven v1:** we then wrote a real Kiro spec (`.kiro/specs/perennial/` →
  `requirements.md`, `design.md`, `tasks.md`) with EARS-style acceptance criteria. New features
  (the three-view architecture, the seasonal peak-shaving model, the terrain/date work) were
  designed against requirements before implementation.

What the spec changed: it forced the honesty rules to be explicit requirements ("report the
fraction of demand offset, never 100%", "expose collection efficiency as an input, never a hidden
constant"). That turned vague intentions into testable criteria, and it is why the final numbers
are defensible. Vibe coding was great for exploration and speed; the spec was what made the result
trustworthy.

## 3. Agent hooks, the workflows we automated

Three hooks in `.kiro/hooks/`:

- **`test-on-save`** (PostFileSave on `engine/` and `tests/`): runs the property-based suite on
  every engine edit. This is how the 24× bug and later a float-rounding edge case were caught
  immediately instead of at review time.
- **`guard-kiro`** (PostFileSave on `.gitignore`): fails the save if `.kiro` is ever added to
  `.gitignore`, a direct guard against the Hackachusetts disqualification rule. A small hook that
  removes a real, costly risk.
- **`engine-drift`** (PostFileSave on `engine/`): re-runs the viability model and diffs key outputs
  against a stored baseline, flagging silent "number drift" when a formula changes.

The benefit: the feedback loop moved from "remember to run tests" to "the tests and guards run
themselves," which mattered a lot during a fast, multi-pass redesign.

## 4. Steering docs, shaping Kiro's responses

Two steering files in `.kiro/steering/`:

- **`physics-and-units.md`**: SI internally, named constants imported from one module, the rule
  that cooling depends on water-equivalent MASS (not density), and that melting ice ABSORBS heat.
- **`assumptions-and-sources.md`**: no hidden magic numbers, every figure cites its agency, cross-
  check independent estimates, label modeled vs. measured, state uncertainty honestly.

The highest-impact strategy was encoding **honesty as steering**. Before, the agent would
occasionally produce a clean-looking number with no provenance. After, every result came with its
formula, its source, and its caveat, which is exactly what the "Show the math" panel and the Logic
view surface to users. Steering turned a style preference into a consistent product property.

## 5. MCP, extending Kiro's reach

We built a custom MCP server (`mcp_server/perennial_data.py`) exposing three tools:
`noaa_seasonal_snowfall`, `nws_snow_forecast`, and `usgs_terrain`. It wraps the same engine
functions the app uses, so Kiro could pull **live NOAA, NWS, and USGS data during development** to
validate numbers, for example confirming the 2014-15 Boston record winter really was 110.6 inches
before we hard-trusted the pipeline.

Why it mattered: without MCP, verifying real-world data meant leaving the loop to hand-check
government APIs. With it, Kiro could fetch and reason over the real data inline, and the "how we
built it" and "what the product does" became the same data layer.

## 6. Property-based testing, what it caught

The engine is pure functions, which made Hypothesis a natural fit. We encoded invariants as laws:
offset is never negative and never exceeds 100%; more snow never yields less cooling (monotonicity);
collected mass is linear in area; a pile can never deliver more cold than it holds (energy
conservation); heat-exchanger losses only ever reduce delivered cold.

PBT earned its place twice:
- It exposed the **24× collection-estimate mismatch** by failing a cross-check invariant, a bug a
  hand-picked unit test would likely have missed because the individual numbers each looked
  plausible.
- It found a **float-rounding edge case** in the impact projection (a value rounded to whole
  gallons tripped a too-tight tolerance), which clarified a real modeling choice.

These are exactly the "issues unit tests miss" PBT is meant to find: not wrong answers on obvious
inputs, but broken relationships across the whole input space.

## 7. The honest deployment story

Deploying to Vercel surfaced three real engineering problems that Kiro worked through: an auth wall
(disabled), static-vs-function routing (the static build namespaces under `/web/`, so routes and
the FastAPI `/api` mount were set accordingly), and a **282 MB serverless function exceeding
Vercel's 225 MB limit**. The fix was architectural, not a hack: because the snowfall predictor was
written with a pure-Python climatology fallback behind a lazy scikit-learn import, we moved the
heavy ML stack to `requirements-dev.txt` and let the deployed function run slim. The product still
predicts snowfall in production, just via the climatology model instead of the trained one.

---

## Summary

Kiro was not just an autocomplete here. The spec made the numbers trustworthy, steering made
honesty a consistent property, hooks turned safety and testing into reflexes, MCP put real
government data inside the build loop, and property-based testing caught the bugs that mattered.
The result is a climate tool whose every figure can be audited back to a formula and a public
source, which is the whole point.
