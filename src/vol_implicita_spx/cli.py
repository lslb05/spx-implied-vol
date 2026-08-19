"""Interface de linha de comando. A lógica vive no pacote; aqui só coordena."""

import argparse
import sys
from datetime import UTC, date, datetime

import psycopg
import yfinance as yf

from vol_implicita_spx.config import Settings
from vol_implicita_spx.fontes import spy
from vol_implicita_spx.skew import calcular_curva
from vol_implicita_spx.taxa_livre_risco import TaxaIndisponivel, taxa_3_meses


def _argumentos(argv: list[str] | None) -> argparse.Namespace:
    principal = argparse.ArgumentParser(prog="vol-implicita-spx")
    comandos = principal.add_subparsers(dest="comando", required=True)

    curva = comandos.add_parser("curva", help="curva de skew de um vencimento")
    curva.add_argument("--vencimento", required=True, type=date.fromisoformat)

    return principal.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    argumentos = _argumentos(argv)
    config = Settings()
    hoje = datetime.now(UTC).date()

    try:
        with psycopg.connect(config.dados_mercado_publico_dsn) as conexao:
            taxa = taxa_3_meses(conexao, em=hoje)
    except TaxaIndisponivel as erro:
        print(str(erro), file=sys.stderr)
        return 2
    except psycopg.OperationalError as erro:
        print(
            f"não foi possível conectar ao Postgres do dados-mercado-publico: {erro}",
            file=sys.stderr,
        )
        return 2

    ticker = yf.Ticker(spy.TICKER)
    spot = spy.spot_atual(ticker=ticker)
    dividendo = spy.dividend_yield(ticker=ticker, spot=spot)
    contratos = spy.buscar_chain(argumentos.vencimento.isoformat(), ticker=ticker)
    if not contratos:
        print(
            f"nenhum contrato encontrado para {argumentos.vencimento}", file=sys.stderr
        )
        return 2

    quadro = calcular_curva(
        contratos,
        spot=spot,
        vencimento=argumentos.vencimento,
        hoje=hoje,
        taxa=taxa,
        dividendo=dividendo,
    )
    print(quadro.write_csv().rstrip())
    return 0
