"""Black-Scholes-Merton pricing and numerical implied vol inversion.

Convention: `time` in years, `rate` and `dividend` as continuous annual
decimals (e.g. 0.05, not 5). `dividend` is the continuous yield — the
standard approximation for a stock that pays discrete dividends, acceptable
over this project's month-scale horizon.
"""

import math
from typing import Literal

OptionType = Literal["call", "put"]

_TOLERANCE = 1e-6
_MAX_ITERATIONS = 100
_MIN_VOL = 1e-4
_MAX_VOL = 5.0


def _cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _density(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


def _d1_d2(
    spot: float, strike: float, time: float, rate: float, dividend: float, vol: float
) -> tuple[float, float]:
    d1 = (math.log(spot / strike) + (rate - dividend + 0.5 * vol * vol) * time) / (
        vol * math.sqrt(time)
    )
    return d1, d1 - vol * math.sqrt(time)


def price(
    spot: float,
    strike: float,
    time: float,
    rate: float,
    dividend: float,
    vol: float,
    option_type: OptionType,
) -> float:
    """European Black-Scholes-Merton price. Doesn't model early exercise."""
    d1, d2 = _d1_d2(spot, strike, time, rate, dividend, vol)
    discounted_spot = spot * math.exp(-dividend * time)
    discounted_strike = strike * math.exp(-rate * time)
    if option_type == "call":
        return discounted_spot * _cdf(d1) - discounted_strike * _cdf(d2)
    return discounted_strike * _cdf(-d2) - discounted_spot * _cdf(-d1)


def vega(
    spot: float, strike: float, time: float, rate: float, dividend: float, vol: float
) -> float:
    """Sensitivity of price to vol — same for a call and put at the same strike."""
    d1, _ = _d1_d2(spot, strike, time, rate, dividend, vol)
    return spot * math.exp(-dividend * time) * math.sqrt(time) * _density(d1)


def delta(
    spot: float,
    strike: float,
    time: float,
    rate: float,
    dividend: float,
    vol: float,
    option_type: OptionType,
) -> float:
    d1, _ = _d1_d2(spot, strike, time, rate, dividend, vol)
    factor = math.exp(-dividend * time)
    return factor * _cdf(d1) if option_type == "call" else factor * (_cdf(d1) - 1)


def implied_vol(
    market_price: float,
    spot: float,
    strike: float,
    time: float,
    rate: float,
    dividend: float,
    option_type: OptionType,
) -> float | None:
    """Inverts Black-Scholes via Newton-Raphson, with bisection as a fallback.

    Returns `None` when the market price is outside the band reachable by any
    positive vol (below intrinsic, a quoted spread with no trade) — that's
    bad market data, not an accounting bug, and the caller decides what to do
    with the absence.
    """
    if time <= 0 or market_price <= 0:
        return None

    sigma = 0.2
    for _ in range(_MAX_ITERATIONS):
        difference = (
            price(spot, strike, time, rate, dividend, sigma, option_type) - market_price
        )
        if abs(difference) < _TOLERANCE:
            return sigma
        derivative = vega(spot, strike, time, rate, dividend, sigma)
        if derivative < 1e-8:
            break
        sigma -= difference / derivative
        if not (_MIN_VOL < sigma < _MAX_VOL):
            break

    return _bisection(market_price, spot, strike, time, rate, dividend, option_type)


def _bisection(
    market_price: float,
    spot: float,
    strike: float,
    time: float,
    rate: float,
    dividend: float,
    option_type: OptionType,
) -> float | None:
    low, high = _MIN_VOL, _MAX_VOL
    f_low = price(spot, strike, time, rate, dividend, low, option_type) - market_price
    f_high = price(spot, strike, time, rate, dividend, high, option_type) - market_price
    if f_low * f_high > 0:
        return None

    mid = low
    for _ in range(_MAX_ITERATIONS):
        mid = (low + high) / 2
        f_mid = (
            price(spot, strike, time, rate, dividend, mid, option_type) - market_price
        )
        if abs(f_mid) < _TOLERANCE:
            return mid
        if f_low * f_mid < 0:
            high = mid
        else:
            low, f_low = mid, f_mid
    return mid
