"""Curva de skew: IV, delta e vega por strike, para um vencimento."""

from collections.abc import Sequence
from datetime import date

import polars as pl

from vol_implicita_spx.black_scholes import delta, vega, vol_implicita
from vol_implicita_spx.fontes.spy import Contrato

_ESQUEMA = {
    "strike": pl.Float64,
    "tipo": pl.String,
    "iv": pl.Float64,
    "iv_referencia": pl.Float64,
    "delta": pl.Float64,
    "vega": pl.Float64,
}


def calcular_curva(
    contratos: Sequence[Contrato],
    *,
    spot: float,
    vencimento: date,
    hoje: date,
    taxa: float,
    dividendo: float,
) -> pl.DataFrame:
    """Uma linha por contrato, com IV invertida via Black-Scholes.

    `tempo` em anos usa dias corridos / 365 — aproximação padrão de mercado
    para este horizonte; não é dia útil (calendário de pregão).
    """
    tempo = (vencimento - hoje).days / 365
    linhas = []
    for contrato in contratos:
        iv = vol_implicita(
            contrato.preco_mercado,
            spot,
            contrato.strike,
            tempo,
            taxa,
            dividendo,
            contrato.tipo,
        )
        linhas.append(
            {
                "strike": contrato.strike,
                "tipo": contrato.tipo,
                "iv": iv,
                "iv_referencia": contrato.iv_referencia,
                "delta": delta(
                    spot, contrato.strike, tempo, taxa, dividendo, iv, contrato.tipo
                )
                if iv is not None
                else None,
                "vega": vega(spot, contrato.strike, tempo, taxa, dividendo, iv)
                if iv is not None
                else None,
            }
        )
    return pl.DataFrame(linhas, schema=_ESQUEMA).sort(["tipo", "strike"])
