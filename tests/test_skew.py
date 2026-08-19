import json
from datetime import date
from pathlib import Path

from vol_implicita_spx.fontes.spy import Contrato
from vol_implicita_spx.skew import calcular_curva

_FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "spy_chain_20260918.json").read_text(
        encoding="utf-8"
    )
)


def _dividend_yield() -> float:
    spot: float = _FIXTURE["spot"]
    total: float = sum(d["valor"] for d in _FIXTURE["dividendos"])
    return total / spot


def test_iv_calculada_bate_com_a_iv_que_a_yahoo_ja_publica() -> None:
    """Gabarito é a própria fonte: o preço vem da chain real, congelada em
    fixture, e a IV que calculamos por Black-Scholes-Merton europeu deve ficar
    perto da IV que a Yahoo/CBOE publicam usando o modelo delas (que trata a
    opção americana). A diferença remanescente é o viés documentado no README.
    """
    contratos = [
        Contrato(
            strike=c["strike"],
            tipo=c["tipo"],
            preco_mercado=(c["bid"] + c["ask"]) / 2,
            iv_referencia=c["impliedVolatility"],
        )
        for c in _FIXTURE["contratos"]
    ]

    curva = calcular_curva(
        contratos,
        spot=_FIXTURE["spot"],
        vencimento=date.fromisoformat(_FIXTURE["vencimento"]),
        hoje=date.fromisoformat(_FIXTURE["buscado_em"][:10]),
        taxa=0.05,
        dividendo=_dividend_yield(),
    )

    diferenca = (curva["iv"] - curva["iv_referencia"]).abs()
    maximo = diferenca.max()
    media = diferenca.mean()
    # Tolerância folgada o suficiente pro viés americano vs. europeu e pra
    # aproximação de dividendo contínuo, apertada o suficiente pra pegar erro
    # de conta real (ex.: trocar taxa por dividendo, sinal errado no d1/d2).
    assert maximo is not None and float(maximo) < 0.03  # type: ignore[arg-type]
    assert media is not None and float(media) < 0.015  # type: ignore[arg-type]


def test_contrato_sem_preco_valido_fica_com_iv_nula() -> None:
    contratos = [
        Contrato(strike=770.0, tipo="call", preco_mercado=0.0, iv_referencia=None)
    ]

    curva = calcular_curva(
        contratos,
        spot=769.25,
        vencimento=date(2026, 8, 21),
        hoje=date(2026, 8, 19),
        taxa=0.05,
        dividendo=0.01,
    )

    assert curva["iv"].to_list() == [None]
