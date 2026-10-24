# Steering: Physics constants and units policy

Apply these rules to all engine code, calculations, and explanations.

## Units
- **SI internally, always.** Mass in kg, energy in kJ (or kWh where clearer), length in meters,
  temperature in Kelvin/Celsius. Convert to display units (gallons, inches, MWh) only at the UI edge.
- Never mix units in a formula. If an input arrives in inches or cubic yards, convert immediately
  using the named constant in `engine/constants.py`.

## Physical constants (do not hardcode elsewhere; import from engine/constants.py)
- Latent heat of fusion of ice = 334 kJ/kg.
- Specific heat of water = 4.187 kJ/(kg·K); of ice = 2.04 kJ/(kg·K).
- Density: water 1000, ice 917, fresh snow ~100, packed pile ~450-600 kg/m³.
- 1 tonne of ice ≈ 92.8 kWh of cooling.

## Core modeling rules
- Cooling depends on **water-equivalent MASS**, which is conserved as snow compacts. Density only
  converts between a measured VOLUME and that mass — never let density change the cooling result.
- Melting ice **absorbs** heat; it does not generate it. The cold is the product; meltwater is
  spent coolant.
- Snow cooling is **seasonal and finite**. Report the **fraction** of demand offset and the
  **peak-month** offset, never "100% / eliminates all cooling."
- The clean ultrapure loop and the dirty meltwater never mix — they meet only across a
  shell-and-tube heat-exchanger wall. Account for a fouling factor.
