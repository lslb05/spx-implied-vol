from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

from vol_implicita_spx.fontes import spy


@dataclass
class _Chain:
    calls: pd.DataFrame
    puts: pd.DataFrame


class _TickerFalso:
    def __init__(self, chain: _Chain, spot: float, dividendos: pd.Series) -> None:
        self._chain = chain
        self._spot = spot
        self.dividends = dividendos
        self.options: tuple[str, ...] = ("2026-08-21",)

    def option_chain(self, vencimento: str) -> _Chain:
        return self._chain

    def history(self, period: str) -> pd.DataFrame:
        return pd.DataFrame({"Close": [self._spot]})


def _quadro(linhas: list[dict[str, float]]) -> pd.DataFrame:
    return pd.DataFrame(linhas)


def test_buscar_chain_usa_mid_do_bid_ask() -> None:
    calls = _quadro(
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
    puts = _quadro(
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
    ticker = _TickerFalso(
        _Chain(calls, puts), spot=769.0, dividendos=pd.Series(dtype=float)
    )

    contratos = spy.buscar_chain("2026-08-21", ticker=ticker)

    call = next(c for c in contratos if c.tipo == "call")
    assert call.preco_mercado == pytest.approx(2.45)
    assert call.iv_referencia == pytest.approx(0.1)


def test_buscar_chain_cai_pro_ultimo_negocio_sem_bid_ask() -> None:
    calls = _quadro(
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
    puts = _quadro([])
    ticker = _TickerFalso(
        _Chain(calls, puts), spot=769.0, dividendos=pd.Series(dtype=float)
    )

    contratos = spy.buscar_chain("2026-08-21", ticker=ticker)

    assert contratos[0].preco_mercado == pytest.approx(0.05)


def test_buscar_chain_ignora_contrato_sem_cotacao_nenhuma() -> None:
    calls = _quadro(
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
    puts = _quadro([])
    ticker = _TickerFalso(
        _Chain(calls, puts), spot=769.0, dividendos=pd.Series(dtype=float)
    )

    contratos = spy.buscar_chain("2026-08-21", ticker=ticker)

    assert contratos == []


def test_spot_atual_le_o_ultimo_fechamento() -> None:
    ticker = _TickerFalso(
        _Chain(_quadro([]), _quadro([])), spot=769.25, dividendos=pd.Series(dtype=float)
    )

    assert spy.spot_atual(ticker=ticker) == pytest.approx(769.25)


def test_dividend_yield_soma_so_os_ultimos_365_dias() -> None:
    agora = datetime.now(UTC)
    dividendos = pd.Series(
        [1.9, 1.8, 100.0],
        index=pd.DatetimeIndex(
            [
                agora - timedelta(days=90),
                agora - timedelta(days=270),
                agora - timedelta(days=800),
            ]
        ),
    )
    ticker = _TickerFalso(
        _Chain(_quadro([]), _quadro([])), spot=769.0, dividendos=dividendos
    )

    resultado = spy.dividend_yield(ticker=ticker, spot=769.0)

    assert resultado == pytest.approx(3.7 / 769.0)


def test_dividend_yield_sem_historico_e_zero() -> None:
    ticker = _TickerFalso(
        _Chain(_quadro([]), _quadro([])), spot=769.0, dividendos=pd.Series(dtype=float)
    )

    assert spy.dividend_yield(ticker=ticker, spot=769.0) == 0.0
