"""Carbon-credit accounting for Perennial.

When snow cooling displaces chiller electricity, it avoids grid CO2. Avoided CO2
can be issued as carbon credits (1 credit = 1 tonne CO2 avoided) and sold on
voluntary carbon markets. This module turns avoided CO2 into credits and dollars,
plus a per-day figure for the downloadable daily report.

Prices are an explicit, adjustable input (voluntary market prices vary widely).
Default ~$15/tonne is a mid-range voluntary-market figure; the UI exposes it.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_CREDIT_PRICE_USD_PER_TONNE = 15.0


@dataclass(frozen=True)
class CarbonCredits:
    co2_avoided_tonnes_yr: float
    credits_yr: float               # 1 credit = 1 tonne CO2 avoided
    credit_price_usd: float
    credit_value_usd_yr: float
    co2_avoided_kg_per_day: float
    credit_value_usd_per_day: float


def carbon_credits(
    co2_avoided_tonnes_yr: float,
    credit_price_usd_per_tonne: float = DEFAULT_CREDIT_PRICE_USD_PER_TONNE,
) -> CarbonCredits:
    if co2_avoided_tonnes_yr < 0:
        raise ValueError("co2_avoided must be non-negative")
    if credit_price_usd_per_tonne < 0:
        raise ValueError("credit price must be non-negative")

    credits = co2_avoided_tonnes_yr  # 1 tonne = 1 credit
    value_yr = credits * credit_price_usd_per_tonne
    return CarbonCredits(
        co2_avoided_tonnes_yr=co2_avoided_tonnes_yr,
        credits_yr=credits,
        credit_price_usd=credit_price_usd_per_tonne,
        credit_value_usd_yr=value_yr,
        co2_avoided_kg_per_day=co2_avoided_tonnes_yr * 1000.0 / 365.0,
        credit_value_usd_per_day=value_yr / 365.0,
    )
