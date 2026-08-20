import pytest

from spx_implied_vol.black_scholes import OptionType, delta, implied_vol, price

_SPOT = 769.25
_STRIKE = 770.0
_TIME = 30 / 365
_RATE = 0.05
_DIVIDEND = 0.012


@pytest.mark.parametrize("option_type", ["call", "put"])
@pytest.mark.parametrize("true_vol", [0.05, 0.15, 0.30, 0.80])
def test_inversion_recovers_the_vol_used_to_generate_the_price(
    option_type: OptionType, true_vol: float
) -> None:
    market_price = price(_SPOT, _STRIKE, _TIME, _RATE, _DIVIDEND, true_vol, option_type)

    recovered_vol = implied_vol(
        market_price, _SPOT, _STRIKE, _TIME, _RATE, _DIVIDEND, option_type
    )

    assert recovered_vol == pytest.approx(true_vol, abs=1e-4)


def test_price_below_intrinsic_has_no_implied_vol() -> None:
    # A well-OTM call isn't worth more than zero for any reasonable positive
    # vol at an absurdly high market price — here the inverse scenario: a
    # price pinned near zero for a well-ITM strike is inconsistent with any
    # vol, because intrinsic value already exceeds the price.
    market_price = 0.01
    itm_strike = 500.0

    result = implied_vol(
        market_price, _SPOT, itm_strike, _TIME, _RATE, _DIVIDEND, "call"
    )

    assert result is None


def test_zero_time_does_not_converge() -> None:
    assert implied_vol(5.0, _SPOT, _STRIKE, 0.0, _RATE, _DIVIDEND, "call") is None


def test_call_delta_is_between_zero_and_one() -> None:
    d = delta(_SPOT, _STRIKE, _TIME, _RATE, _DIVIDEND, 0.2, "call")

    assert 0 < d < 1


def test_put_delta_is_between_minus_one_and_zero() -> None:
    d = delta(_SPOT, _STRIKE, _TIME, _RATE, _DIVIDEND, 0.2, "put")

    assert -1 < d < 0
