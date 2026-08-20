import json
from datetime import date
from pathlib import Path

from spx_implied_vol.skew import compute_curve
from spx_implied_vol.sources.spy import Contract

_FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "spy_chain_20260918.json").read_text(
        encoding="utf-8"
    )
)


def _dividend_yield() -> float:
    spot: float = _FIXTURE["spot"]
    total: float = sum(d["value"] for d in _FIXTURE["dividends"])
    return total / spot


def test_computed_iv_matches_the_iv_yahoo_already_publishes() -> None:
    """The ground truth is the source itself: the price comes from a real
    chain, frozen in a fixture, and the IV we compute via European
    Black-Scholes-Merton should land close to the IV Yahoo/CBOE publish using
    their model (which handles the American option). The remaining
    difference is the bias documented in the README.
    """
    contracts = [
        Contract(
            strike=c["strike"],
            type=c["type"],
            market_price=(c["bid"] + c["ask"]) / 2,
            reference_iv=c["impliedVolatility"],
        )
        for c in _FIXTURE["contracts"]
    ]

    curve = compute_curve(
        contracts,
        spot=_FIXTURE["spot"],
        expiration=date.fromisoformat(_FIXTURE["expiration"]),
        today=date.fromisoformat(_FIXTURE["fetched_at"][:10]),
        rate=0.05,
        dividend=_dividend_yield(),
    )

    difference = (curve["iv"] - curve["reference_iv"]).abs()
    maximum = difference.max()
    average = difference.mean()
    # Loose enough for the American-vs-European bias and the continuous
    # dividend approximation, tight enough to catch a real accounting error
    # (e.g. swapping rate for dividend, a wrong sign in d1/d2).
    assert maximum is not None and float(maximum) < 0.03  # type: ignore[arg-type]
    assert average is not None and float(average) < 0.015  # type: ignore[arg-type]


def test_contract_with_no_valid_price_has_null_iv() -> None:
    contracts = [
        Contract(strike=770.0, type="call", market_price=0.0, reference_iv=None)
    ]

    curve = compute_curve(
        contracts,
        spot=769.25,
        expiration=date(2026, 8, 21),
        today=date(2026, 8, 19),
        rate=0.05,
        dividend=0.01,
    )

    assert curve["iv"].to_list() == [None]
