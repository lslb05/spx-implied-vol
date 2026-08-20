from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

from spx_implied_vol.sources import spy


@dataclass
class _Chain:
    calls: pd.DataFrame
    puts: pd.DataFrame


class _FakeTicker:
    def __init__(self, chain: _Chain, spot: float, dividends: pd.Series) -> None:
        self._chain = chain
        self._spot = spot
        self.dividends = dividends
        self.options: tuple[str, ...] = ("2026-08-21",)

    def option_chain(self, expiration: str) -> _Chain:
        return self._chain

    def history(self, period: str) -> pd.DataFrame:
        return pd.DataFrame({"Close": [self._spot]})


def _frame(rows: list[dict[str, float]]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def test_fetch_chain_uses_bid_ask_mid() -> None:
    calls = _frame(
        [
            {
                "strike": 770.0,
                "bid": 2.4,
                "ask": 2.5,
                "lastPrice": 2.6,
                "impliedVolatility": 0.1,
            }
        ]
    )
    puts = _frame(
        [
            {
                "strike": 770.0,
                "bid": 3.0,
                "ask": 3.2,
                "lastPrice": 3.1,
                "impliedVolatility": 0.12,
            }
        ]
    )
    ticker = _FakeTicker(
        _Chain(calls, puts), spot=769.0, dividends=pd.Series(dtype=float)
    )

    contracts = spy.fetch_chain("2026-08-21", ticker=ticker)

    call = next(c for c in contracts if c.type == "call")
    assert call.market_price == pytest.approx(2.45)
    assert call.reference_iv == pytest.approx(0.1)


def test_fetch_chain_falls_back_to_last_trade_without_bid_ask() -> None:
    calls = _frame(
        [
            {
                "strike": 780.0,
                "bid": 0.0,
                "ask": 0.0,
                "lastPrice": 0.05,
                "impliedVolatility": 0.3,
            }
        ]
    )
    puts = _frame([])
    ticker = _FakeTicker(
        _Chain(calls, puts), spot=769.0, dividends=pd.Series(dtype=float)
    )

    contracts = spy.fetch_chain("2026-08-21", ticker=ticker)

    assert contracts[0].market_price == pytest.approx(0.05)


def test_fetch_chain_ignores_contract_with_no_quote_at_all() -> None:
    calls = _frame(
        [
            {
                "strike": 900.0,
                "bid": 0.0,
                "ask": 0.0,
                "lastPrice": 0.0,
                "impliedVolatility": 0.0,
            }
        ]
    )
    puts = _frame([])
    ticker = _FakeTicker(
        _Chain(calls, puts), spot=769.0, dividends=pd.Series(dtype=float)
    )

    contracts = spy.fetch_chain("2026-08-21", ticker=ticker)

    assert contracts == []


def test_current_spot_reads_the_last_close() -> None:
    ticker = _FakeTicker(
        _Chain(_frame([]), _frame([])), spot=769.25, dividends=pd.Series(dtype=float)
    )

    assert spy.current_spot(ticker=ticker) == pytest.approx(769.25)


def test_dividend_yield_sums_only_the_last_365_days() -> None:
    now = datetime.now(UTC)
    dividends = pd.Series(
        [1.9, 1.8, 100.0],
        index=pd.DatetimeIndex(
            [
                now - timedelta(days=90),
                now - timedelta(days=270),
                now - timedelta(days=800),
            ]
        ),
    )
    ticker = _FakeTicker(
        _Chain(_frame([]), _frame([])), spot=769.0, dividends=dividends
    )

    result = spy.dividend_yield(ticker=ticker, spot=769.0)

    assert result == pytest.approx(3.7 / 769.0)


def test_dividend_yield_with_no_history_is_zero() -> None:
    ticker = _FakeTicker(
        _Chain(_frame([]), _frame([])), spot=769.0, dividends=pd.Series(dtype=float)
    )

    assert spy.dividend_yield(ticker=ticker, spot=769.0) == 0.0
