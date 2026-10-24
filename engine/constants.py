"""Fixed physical constants for Perennial.

These are NOT data to look up — they are thermodynamic constants.
Sources recorded in HACKATHON_CONTEXT.md.
"""

# --- Thermodynamics ---
LATENT_HEAT_FUSION_ICE_KJ_PER_KG: float = 334.0  # kJ/kg (NIST; some texts 335)
SPECIFIC_HEAT_WATER_KJ_PER_KG_K: float = 4.187   # kJ/(kg*K)
SPECIFIC_HEAT_ICE_KJ_PER_KG_K: float = 2.04      # kJ/(kg*K)

# --- Densities (kg/m^3) ---
DENSITY_WATER: float = 1000.0
DENSITY_ICE: float = 917.0
# Snow density varies widely with age/compaction:
DENSITY_FRESH_SNOW: float = 100.0     # fluffy, just fell
DENSITY_SETTLED_SNOW: float = 300.0   # days old
DENSITY_PACKED_PILE: float = 600.0    # plowed, compacted storage pile

# --- Unit conversions ---
KJ_PER_KWH: float = 3600.0            # 1 kWh = 3600 kJ
LITERS_PER_GALLON: float = 3.78541
CUBIC_YARD_TO_CUBIC_METER: float = 0.764555
MILE_TO_METER: float = 1609.344

# --- Handy derived value ---
# Cooling energy from melting 1 tonne (1000 kg) of ice:
#   1000 kg * 334 kJ/kg = 334000 kJ = ~92.8 kWh
COOLING_KWH_PER_TONNE_ICE: float = (
    1000.0 * LATENT_HEAT_FUSION_ICE_KJ_PER_KG / KJ_PER_KWH
)
