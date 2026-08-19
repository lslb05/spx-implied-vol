"""Precificação Black-Scholes-Merton e inversão numérica de vol implícita.

Convenção: `tempo` em anos, `taxa` e `dividendo` decimais anuais contínuos
(ex.: 0.05, não 5). `dividendo` é o yield contínuo — aproximação padrão para
uma ação que paga dividendo discreto, aceitável no horizonte de meses deste
projeto.
"""

import math
from typing import Literal

TipoOpcao = Literal["call", "put"]

_TOLERANCIA = 1e-6
_MAX_ITERACOES = 100
_VOL_MINIMA = 1e-4
_VOL_MAXIMA = 5.0


def _cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _densidade(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


def _d1_d2(
    spot: float, strike: float, tempo: float, taxa: float, dividendo: float, vol: float
) -> tuple[float, float]:
    d1 = (math.log(spot / strike) + (taxa - dividendo + 0.5 * vol * vol) * tempo) / (
        vol * math.sqrt(tempo)
    )
    return d1, d1 - vol * math.sqrt(tempo)


def preco(
    spot: float,
    strike: float,
    tempo: float,
    taxa: float,
    dividendo: float,
    vol: float,
    tipo: TipoOpcao,
) -> float:
    """Preço europeu de Black-Scholes-Merton. Não modela exercício antecipado."""
    d1, d2 = _d1_d2(spot, strike, tempo, taxa, dividendo, vol)
    spot_descontado = spot * math.exp(-dividendo * tempo)
    strike_descontado = strike * math.exp(-taxa * tempo)
    if tipo == "call":
        return spot_descontado * _cdf(d1) - strike_descontado * _cdf(d2)
    return strike_descontado * _cdf(-d2) - spot_descontado * _cdf(-d1)


def vega(
    spot: float, strike: float, tempo: float, taxa: float, dividendo: float, vol: float
) -> float:
    """Sensibilidade do preço à vol — igual para call e put no mesmo strike."""
    d1, _ = _d1_d2(spot, strike, tempo, taxa, dividendo, vol)
    return spot * math.exp(-dividendo * tempo) * math.sqrt(tempo) * _densidade(d1)


def delta(
    spot: float,
    strike: float,
    tempo: float,
    taxa: float,
    dividendo: float,
    vol: float,
    tipo: TipoOpcao,
) -> float:
    d1, _ = _d1_d2(spot, strike, tempo, taxa, dividendo, vol)
    fator = math.exp(-dividendo * tempo)
    return fator * _cdf(d1) if tipo == "call" else fator * (_cdf(d1) - 1)


def vol_implicita(
    preco_mercado: float,
    spot: float,
    strike: float,
    tempo: float,
    taxa: float,
    dividendo: float,
    tipo: TipoOpcao,
) -> float | None:
    """Inverte Black-Scholes por Newton-Raphson, com bisseção como salva-vidas.

    Devolve `None` quando o preço de mercado está fora da banda alcançável por
    qualquer vol positiva (abaixo do intrínseco, spread cotado sem negócio) —
    isso é dado ruim de mercado, não bug de conta, e o chamador decide o que
    fazer com a ausência.
    """
    if tempo <= 0 or preco_mercado <= 0:
        return None

    sigma = 0.2
    for _ in range(_MAX_ITERACOES):
        diferenca = (
            preco(spot, strike, tempo, taxa, dividendo, sigma, tipo) - preco_mercado
        )
        if abs(diferenca) < _TOLERANCIA:
            return sigma
        derivada = vega(spot, strike, tempo, taxa, dividendo, sigma)
        if derivada < 1e-8:
            break
        sigma -= diferenca / derivada
        if not (_VOL_MINIMA < sigma < _VOL_MAXIMA):
            break

    return _bisseccao(preco_mercado, spot, strike, tempo, taxa, dividendo, tipo)


def _bisseccao(
    preco_mercado: float,
    spot: float,
    strike: float,
    tempo: float,
    taxa: float,
    dividendo: float,
    tipo: TipoOpcao,
) -> float | None:
    baixo, alto = _VOL_MINIMA, _VOL_MAXIMA
    f_baixo = preco(spot, strike, tempo, taxa, dividendo, baixo, tipo) - preco_mercado
    f_alto = preco(spot, strike, tempo, taxa, dividendo, alto, tipo) - preco_mercado
    if f_baixo * f_alto > 0:
        return None

    meio = baixo
    for _ in range(_MAX_ITERACOES):
        meio = (baixo + alto) / 2
        f_meio = preco(spot, strike, tempo, taxa, dividendo, meio, tipo) - preco_mercado
        if abs(f_meio) < _TOLERANCIA:
            return meio
        if f_baixo * f_meio < 0:
            alto = meio
        else:
            baixo, f_baixo = meio, f_meio
    return meio
