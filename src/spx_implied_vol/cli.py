"""Command-line interface. Logic lives in the package; this only coordinates."""

import argparse
import sys
from datetime import UTC, date, datetime

import psycopg
import yfinance as yf

from spx_implied_vol.config import Settings
from spx_implied_vol.risk_free_rate import RateUnavailable, rate_3_months
from spx_implied_vol.skew import compute_curve
from spx_implied_vol.sources import spy


def _arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="spx-implied-vol")
    subparsers = parser.add_subparsers(dest="command", required=True)

    curve = subparsers.add_parser("curve", help="skew curve for one expiration")
    curve.add_argument("--expiration", required=True, type=date.fromisoformat)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _arguments(argv)
    config = Settings()
    today = datetime.now(UTC).date()

    try:
        with psycopg.connect(config.market_data_dsn) as connection:
            rate = rate_3_months(connection, at=today)
    except RateUnavailable as error:
        print(str(error), file=sys.stderr)
        return 2
    except psycopg.OperationalError as error:
        print(
            f"could not connect to public-market-data's Postgres: {error}",
            file=sys.stderr,
        )
        return 2

    ticker = yf.Ticker(spy.TICKER)
    spot = spy.current_spot(ticker=ticker)
    dividend = spy.dividend_yield(ticker=ticker, spot=spot)
    contracts = spy.fetch_chain(args.expiration.isoformat(), ticker=ticker)
    if not contracts:
        print(f"no contract found for {args.expiration}", file=sys.stderr)
        return 2

    frame = compute_curve(
        contracts,
        spot=spot,
        expiration=args.expiration,
        today=today,
        rate=rate,
        dividend=dividend,
    )
    print(frame.write_csv().rstrip())
    return 0
