import pytest

from vol_implicita_spx.black_scholes import TipoOpcao, delta, preco, vol_implicita

_SPOT = 769.25
_STRIKE = 770.0
_TEMPO = 30 / 365
_TAXA = 0.05
_DIVIDENDO = 0.012


@pytest.mark.parametrize("tipo", ["call", "put"])
@pytest.mark.parametrize("vol_verdadeira", [0.05, 0.15, 0.30, 0.80])
def test_inversao_recupera_a_vol_usada_para_gerar_o_preco(
    tipo: TipoOpcao, vol_verdadeira: float
) -> None:
    preco_mercado = preco(
        _SPOT, _STRIKE, _TEMPO, _TAXA, _DIVIDENDO, vol_verdadeira, tipo
    )

    vol_recuperada = vol_implicita(
        preco_mercado, _SPOT, _STRIKE, _TEMPO, _TAXA, _DIVIDENDO, tipo
    )

    assert vol_recuperada == pytest.approx(vol_verdadeira, abs=1e-4)


def test_preco_abaixo_do_intrinseco_nao_tem_vol_implicita() -> None:
    # Um call de strike bem OTM não vale mais que zero por nenhuma vol positiva
    # razoável cobrir com um preço de mercado absurdamente alto — aqui o
    # cenário inverso: preço colado em zero para um strike bem ITM é
    # inconsistente com qualquer vol, porque o intrínseco já supera o preço.
    preco_mercado = 0.01
    strike_itm = 500.0

    resultado = vol_implicita(
        preco_mercado, _SPOT, strike_itm, _TEMPO, _TAXA, _DIVIDENDO, "call"
    )

    assert resultado is None


def test_tempo_zero_nao_converge() -> None:
    assert vol_implicita(5.0, _SPOT, _STRIKE, 0.0, _TAXA, _DIVIDENDO, "call") is None


def test_delta_de_call_fica_entre_zero_e_um() -> None:
    d = delta(_SPOT, _STRIKE, _TEMPO, _TAXA, _DIVIDENDO, 0.2, "call")

    assert 0 < d < 1


def test_delta_de_put_fica_entre_menos_um_e_zero() -> None:
    d = delta(_SPOT, _STRIKE, _TEMPO, _TAXA, _DIVIDENDO, 0.2, "put")

    assert -1 < d < 0
