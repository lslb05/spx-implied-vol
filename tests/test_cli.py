from dataclasses import dataclass

import pandas as pd
import psycopg
import pytest

from vol_implicita_spx.cli import main


@dataclass
class _Chain:
    calls: pd.DataFrame
    puts: pd.DataFrame


class _TickerFalso:
    options: tuple[str, ...] = ("2026-08-21",)

    def __init__(self, com_contratos: bool) -> None:
        linhas = (
            [
                {
                    "strike": 770.0,
                    "bid": 2.4,
                    "ask": 2.5,
                    "lastPrice": 2.6,
                    "impliedVolatility": 0.1,
                }
            ]
            if com_contratos
            else []
        )
        self._chain = _Chain(pd.DataFrame(linhas), pd.DataFrame([]))
        self.dividends = pd.Series(dtype=float)

    def option_chain(self, vencimento: str) -> _Chain:
        return self._chain

    def history(self, period: str) -> pd.DataFrame:
        return pd.DataFrame({"Close": [769.25]})


@pytest.fixture(autouse=True)
def dsn_no_ambiente(monkeypatch: pytest.MonkeyPatch, dsn: str) -> None:
    monkeypatch.setenv("DADOS_MERCADO_PUBLICO_POSTGRES_DSN", dsn)


def _semear_taxa(conexao: psycopg.Connection) -> None:
    conexao.execute(
        """
        INSERT INTO series_vintage
            (fonte, serie, data_evento, data_publicacao, vigente_ate, valor,
             data_disponibilidade)
        VALUES ('fred', 'DGS3MO', CURRENT_DATE, CURRENT_DATE, CURRENT_DATE + 7,
                5.33, CURRENT_DATE)
        """
    )


def test_sem_taxa_ingerida_orienta_e_sai_com_codigo_dois() -> None:
    assert main(["curva", "--vencimento", "2026-08-21"]) == 2


def test_curva_imprime_csv_com_a_iv_calculada(
    conexao: psycopg.Connection,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _semear_taxa(conexao)
    monkeypatch.setattr("vol_implicita_spx.cli.yf.Ticker", lambda _: _TickerFalso(True))

    codigo = main(["curva", "--vencimento", "2026-08-21"])

    assert codigo == 0
    saida = capsys.readouterr().out
    assert "strike" in saida
    assert "770" in saida


def test_sem_contrato_na_chain_orienta_e_sai_com_codigo_dois(
    conexao: psycopg.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    _semear_taxa(conexao)
    monkeypatch.setattr(
        "vol_implicita_spx.cli.yf.Ticker", lambda _: _TickerFalso(False)
    )

    assert main(["curva", "--vencimento", "2026-08-21"]) == 2
