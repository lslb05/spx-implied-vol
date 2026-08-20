"""SPY access via yfinance: option chain, spot and dividend.

SPY is the liquid SPX proxy used in this project — the index itself doesn't
expose an option chain via yfinance. SPY's options are American; the rest of
the package prices with European Black-Scholes, and the bias is documented
in the README, not hidden here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from spx_implied_vol.black_scholes import OptionType

TICKER = "SPY"


class TickerLike(Protocol):
    """The subset of `yfinance.Ticker` this module uses — injectable in tests."""

    options: tuple[str, ...]
    dividends: Any

    def option_chain(self, expiration: str) -> Any: ...
    def history(self, period: str) -> Any: ...


@dataclass(frozen=True)
class Contract:
    strike: float
    type: OptionType
    market_price: float
    reference_iv: float | None


def fetch_chain(expiration: str, *, ticker: TickerLike) -> list[Contract]:
    """Bid/ask mid per contract; falls back to the last trade when unquoted."""
    chain = ticker.option_chain(expiration)
    contracts = []
    types: tuple[OptionType, ...] = ("call", "put")
    for option_type, frame in zip(types, (chain.calls, chain.puts), strict=True):
        for row in frame.itertuples():
            market_price = _mid_price(row.bid, row.ask, row.lastPrice)
            if market_price is None:
                continue
            reference_iv = (
                float(row.impliedVolatility) if row.impliedVolatility else None
            )
            contracts.append(
                Contract(
                    strike=float(row.strike),
                    type=option_type,
                    market_price=market_price,
                    reference_iv=reference_iv,
                )
            )
    return contracts


def _mid_price(bid: float, ask: float, last: float) -> float | None:
    if bid and ask and bid > 0 and ask > 0:
        return (bid + ask) / 2
    return float(last) if last and last > 0 else None


def current_spot(*, ticker: TickerLike) -> float:
    history = ticker.history(period="1d")
    return float(history["Close"].iloc[-1])


def dividend_yield(*, ticker: TickerLike, spot: float) -> float:
    """Continuous dividend yield approximated by the sum of the last 365 days."""
    dividends = ticker.dividends
    if dividends.empty:
        return 0.0
    cutoff = datetime.now(UTC) - timedelta(days=365)
    recent = dividends[dividends.index >= cutoff]
    return float(recent.sum()) / spot
