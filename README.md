# spx-implied-vol

SPY implied vol surface and skew (liquid SPX proxy), computed by numerical
Black-Scholes inversion — no ready-made pricing library involved.

## The problem

Every broker and every terminal already shows an option's implied vol. What
doesn't show is the math: inverting Black-Scholes to find the vol that
reproduces the market price requires a numerical solver (the price has no
closed-form inverse), and getting that math right — with the correct
risk-free rate and dividend — is what this repository proves.

## Result

```console
$ uv run python -m spx_implied_vol curve --expiration 2026-09-18
strike,type,iv,reference_iv,delta,vega
759.0,call,0.141798,0.159402,0.662783,80.404433
760.0,call,0.143328,0.160058,0.649517,81.584290
761.0,call,0.138608,0.155145,0.641586,82.239416
762.0,call,0.139309,0.155450,0.628633,83.229724
763.0,call,0.136693,0.152322,0.618046,83.966252
764.0,call,0.134564,0.149758,0.606649,84.686693
...
```

`reference_iv` is what Yahoo/CBOE themselves publish in the chain — a free
ground truth to validate the math without a hand-fabricated fixture. The
transcript above was computed from the fixture frozen in
`tests/fixtures/spy_chain_20260918.json` (a real SPY chain, captured
2026-08-19), with a fixed 5% risk-free rate for the example only — live
collection uses the chain at call time and the `DGS3MO` rate from Postgres.

## Problem and scope

- **User:** me, and whoever reviews the portfolio evaluating for
  quantitative research.
- **Decision:** SPY's skew and vol surface can be read without a paid
  terminal, and the math can be checked against the IV the source itself
  publishes.
- **Input:** `yfinance`, SPY's option chain. Risk-free rate: FRED `DGS3MO`,
  read from Postgres via
  [`public-market-data`](../public-market-data) through
  `DADOS_MERCADO_PUBLICO_POSTGRES_DSN` — the same variable that project
  uses, so one `.env` configures both.
- **Out of scope:** trading signals, historical backtesting (`yfinance`
  only exposes today's chain — without history, past surfaces can't be
  reconstructed yet), a parametric surface (SVI/SABR), second-order greeks.

## Architecture

```
yfinance (SPY)                    Postgres (public-market-data)
    │  chain, spot, dividends          │  DGS3MO via series_vintage
    ▼                                  ▼
sources/spy.py                   risk_free_rate.py
    │                                  │
    └──────────────┬───────────────────┘
                    ▼
              skew.py            for each contract: inverts
                    │             black_scholes.implied_vol
                    ▼
                 cli.py           skew curve as CSV
```

`black_scholes.py` depends on nothing beyond the standard library —
`math.erf` already gives the normal CDF without pulling in `scipy`/`numpy`
just for that.

Two decisions worth explaining:

**Newton-Raphson with bisection as a fallback.** Newton converges fast near
the price, but diverges when vega is near zero (a strike well out of the
money) or when a step pushes vol outside a reasonable range. In that case
the solver falls back to bisection on `[0.0001, 5.0]`, which is slow but
always converges if the price is within the band reachable by some positive
vol. Outside that band (market price below intrinsic, a quote with no real
trade), the function returns `None` instead of inventing a number.

**SPY is an American option; the math here is European.**
Black-Scholes-Merton assumes exercise only at expiration. SPY allows early
exercise and pays a dividend — which makes the American call slightly more
valuable than the European equivalent near an ex-date. Against the real
fixture used in the tests (~30-day expiration), the IV computed here
averages less than 0.015 vol point away from the IV Yahoo publishes, with a
maximum below 0.03 — the bias exists, is small at this horizon, and is
measured by the test instead of hidden.

## Run locally

Requirements: Python 3.12, `uv`, Docker (for the ephemeral test Postgres),
and [`public-market-data`](../public-market-data) running with the
`DGS3MO` series ingested:

```bash
# in public-market-data:
docker compose up -d
uv run python -m public_market_data ingest --source fred --series DGS3MO
```

```bash
uv sync
cp .env.example .env
uv run python -m spx_implied_vol curve --expiration 2026-09-18
```

Without the `DGS3MO` series ingested in the neighboring project, the command
explains why and exits with code 2 instead of inventing a rate.

## Quality

```bash
uv run python scripts/check.py
```

The check runs format, lint, types and tests with coverage. It's the same
command CI runs, on Windows, Linux and macOS.

To apply formatting and automatic lint fixes:

```bash
uv run python scripts/format.py
```

## Structure

```text
src/spx_implied_vol/
    black_scholes.py    pricing and numerical inversion — no network dependency
    sources/spy.py       yfinance adapter, testable with a fake ticker
    risk_free_rate.py    reads the public-market-data public interface
    skew.py               combines the three into a per-expiration curve
    cli.py                 coordination
tests/fixtures/           real SPY chain frozen as ground truth
```

## Limitations

- No chain history: `yfinance` only gives the current day, so a past
  surface can't be reconstructed and there's no backtest yet. Real
  point-in-time would require capturing daily snapshots — a possible next
  cut.
- Dividend is an approximated continuous yield (sum of the last 365 days of
  payments / spot), not the real ex-date calendar.
- No parametric surface (SVI/SABR): the curve is point by point, neither
  smoothed nor extrapolated between strikes.

## License

MIT. Third-party data keeps its own license and terms of use.
