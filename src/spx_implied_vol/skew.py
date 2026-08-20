"""Skew curve: IV, delta and vega per strike, for one expiration."""

from collections.abc import Sequence
from datetime import date

import polars as pl

from spx_implied_vol.black_scholes import delta, implied_vol, vega
from spx_implied_vol.sources.spy import Contract

_SCHEMA = {
    "strike": pl.Float64,
    "type": pl.String,
    "iv": pl.Float64,
    "reference_iv": pl.Float64,
    "delta": pl.Float64,
    "vega": pl.Float64,
}


def compute_curve(
    contracts: Sequence[Contract],
    *,
    spot: float,
    expiration: date,
    today: date,
    rate: float,
    dividend: float,
) -> pl.DataFrame:
    """One row per contract, with IV inverted via Black-Scholes.

    `time` in years uses calendar days / 365 — the standard market
    approximation for this horizon; not trading days (exchange calendar).
    """
    time = (expiration - today).days / 365
    rows = []
    for contract in contracts:
        iv = implied_vol(
            contract.market_price,
            spot,
            contract.strike,
            time,
            rate,
            dividend,
            contract.type,
        )
        rows.append(
            {
                "strike": contract.strike,
                "type": contract.type,
                "iv": iv,
                "reference_iv": contract.reference_iv,
                "delta": delta(
                    spot, contract.strike, time, rate, dividend, iv, contract.type
                )
                if iv is not None
                else None,
                "vega": vega(spot, contract.strike, time, rate, dividend, iv)
                if iv is not None
                else None,
            }
        )
    return pl.DataFrame(rows, schema=_SCHEMA).sort(["type", "strike"])
