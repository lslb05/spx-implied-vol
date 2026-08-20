from dataclasses import dataclass

import pandas as pd
import psycopg
import pytest

from spx_implied_vol.cli import main


@dataclass
class _Chain:
    calls: pd.DataFrame
    puts: pd.DataFrame


class _FakeTicker:
    options: tuple[str, ...] = ("2026-08-21",)

    def __init__(self, with_contracts: bool) -> None:
        rows = (
            [
                {
                    "strike": 770.0,
                    "bid": 2.4,
                    "ask": 2.5,
                    "lastPrice": 2.6,
                    "impliedVolatility": 0.1,
                }
            ]
            if with_contracts
            else []
        )
        self._chain = _Chain(pd.DataFrame(rows), pd.DataFrame([]))
        self.dividends = pd.Series(dtype=float)

    def option_chain(self, expiration: str) -> _Chain:
        return self._chain

    def history(self, period: str) -> pd.DataFrame:
        return pd.DataFrame({"Close": [769.25]})


@pytest.fixture(autouse=True)
def dsn_in_environment(monkeypatch: pytest.MonkeyPatch, dsn: str) -> None:
    monkeypatch.setenv("DADOS_MERCADO_PUBLICO_POSTGRES_DSN", dsn)


def _seed_rate(connection: psycopg.Connection) -> None:
    connection.execute(
        """
        INSERT INTO series_vintage
            (fonte, serie, data_evento, data_publicacao, vigente_ate, valor,
             data_disponibilidade)
        VALUES ('fred', 'DGS3MO', CURRENT_DATE, CURRENT_DATE, CURRENT_DATE + 7,
                5.33, CURRENT_DATE)
        """
    )


def test_missing_rate_guides_and_exits_with_code_two() -> None:
    assert main(["curve", "--expiration", "2026-08-21"]) == 2


def test_curve_prints_csv_with_the_computed_iv(
    connection: psycopg.Connection,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_rate(connection)
    monkeypatch.setattr("spx_implied_vol.cli.yf.Ticker", lambda _: _FakeTicker(True))

    code = main(["curve", "--expiration", "2026-08-21"])

    assert code == 0
    output = capsys.readouterr().out
    assert "strike" in output
    assert "770" in output


def test_no_contract_in_chain_guides_and_exits_with_code_two(
    connection: psycopg.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_rate(connection)
    monkeypatch.setattr("spx_implied_vol.cli.yf.Ticker", lambda _: _FakeTicker(False))

    assert main(["curve", "--expiration", "2026-08-21"]) == 2
