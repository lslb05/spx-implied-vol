"""Acesso à SPY via yfinance: chain de opções, spot e dividendo.

SPY é o proxy líquido do SPX usado neste projeto — o índice em si não expõe
chain de opções via yfinance. As opções da SPY são americanas; o restante do
pacote precifica com Black-Scholes europeu, e o viés fica documentado no
README, não escondido aqui.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from vol_implicita_spx.black_scholes import TipoOpcao

TICKER = "SPY"


class TickerLike(Protocol):
    """O subconjunto de `yfinance.Ticker` que este módulo usa — injetável em teste."""

    options: tuple[str, ...]
    dividends: Any

    def option_chain(self, vencimento: str) -> Any: ...
    def history(self, period: str) -> Any: ...


@dataclass(frozen=True)
class Contrato:
    strike: float
    tipo: TipoOpcao
    preco_mercado: float
    iv_referencia: float | None


def buscar_chain(vencimento: str, *, ticker: TickerLike) -> list[Contrato]:
    """Mid do bid/ask por contrato; cai pro último negócio quando não há cotação."""
    chain = ticker.option_chain(vencimento)
    contratos = []
    tipos: tuple[TipoOpcao, ...] = ("call", "put")
    for tipo, quadro in zip(tipos, (chain.calls, chain.puts), strict=True):
        for linha in quadro.itertuples():
            preco_mercado = _preco_mid(linha.bid, linha.ask, linha.lastPrice)
            if preco_mercado is None:
                continue
            iv_referencia = (
                float(linha.impliedVolatility) if linha.impliedVolatility else None
            )
            contratos.append(
                Contrato(
                    strike=float(linha.strike),
                    tipo=tipo,
                    preco_mercado=preco_mercado,
                    iv_referencia=iv_referencia,
                )
            )
    return contratos


def _preco_mid(bid: float, ask: float, ultimo: float) -> float | None:
    if bid and ask and bid > 0 and ask > 0:
        return (bid + ask) / 2
    return float(ultimo) if ultimo and ultimo > 0 else None


def spot_atual(*, ticker: TickerLike) -> float:
    historico = ticker.history(period="1d")
    return float(historico["Close"].iloc[-1])


def dividend_yield(*, ticker: TickerLike, spot: float) -> float:
    """Yield de dividendo contínuo aproximado pela soma dos últimos 365 dias."""
    dividendos = ticker.dividends
    if dividendos.empty:
        return 0.0
    limite = datetime.now(UTC) - timedelta(days=365)
    recentes = dividendos[dividendos.index >= limite]
    return float(recentes.sum()) / spot
