# Project contract — SPX Implied Vol

Read the global `CLAUDE.md` and use this file for what's specific to this
repository.

## Product outcome

- **Problem:** an implied vol surface and skew aren't trivial to compute
  correctly (American option, risk-free rate, dividend). A repository that
  gets this right proves derivatives literacy.
- **User:** me, and whoever reviews the portfolio evaluating for
  quantitative research.
- **Verifiable output:** IV, delta and vega per strike/expiration, computed
  by Black-Scholes inversion (Newton-Raphson) and validated against the
  `impliedVolatility` Yahoo/CBOE already publish in the chain — the source
  carries its own ground truth, no fabricated external fixture needed.
- **Allowed data source:** `yfinance`, SPY's option chain (the liquid SPX
  proxy; the index itself doesn't expose a chain via yfinance). Risk-free
  rate: FRED `DGS3MO` via Postgres from `public-market-data`
  (`DADOS_MERCADO_PUBLICO_POSTGRES_DSN` from the neighboring project — read
  through the public `series_vintage` interface, without importing its
  code).
- **Smallest end-to-end cut:** a CLI that takes an expiration, fetches the
  SPY chain, computes IV+delta+vega per strike and returns that
  expiration's skew curve.
- **Out of scope:** trading signals, historical backtesting (`yfinance`
  only gives the day's chain — without history, past surfaces can't be
  reconstructed yet), a parametric surface (SVI/SABR), second-order greeks.

Do not implement while a `FILL_IN` that changes the design is still open.

## Commands

```bash
uv sync
uv run python scripts/format.py
uv run python scripts/check.py
```

## Local rules

- The package is `spx_implied_vol` and lives in `src/spx_implied_vol`.
- Notebooks import from `src/`; production code never imports a notebook.
- Configuration comes from the environment via `Settings`.
- Preserve raw data and time-vintage metadata whenever there's ingestion.
- Update this file when a structural decision changes.

## Style

Public code, read by people. The rule is restraint — the full list is in
`AGENTS.md`, "Style" section, and applies equally to me and to Codex.

- A comment explains *why*, never *what*. If it paraphrases the line below,
  delete it; if the line needs paraphrasing, rename the variable instead.
- Docstrings only where the signature isn't enough (unit, timezone, side
  effect, what it raises). A three-line private helper doesn't need one.
- Tests assert behavior that can break, not a constant. Coverage is a
  consequence of testing what matters, never a target to inflate.
- Don't catch an exception you don't know how to handle; don't abstract for
  a single caller.

## Commit authorship

Author and committer are one and the same: the repository owner. No
`Co-Authored-By:`, no session trailer, no mention of Claude, Codex or any
tool. Don't change `user.name` or `user.email`.

## Session state

- **Decided:** first cut delivered — CLI `curve --expiration` that fetches
  the SPY chain, inverts Black-Scholes via Newton-Raphson (bisection as a
  fallback) and returns IV, delta and vega per strike. Risk-free rate read
  from the public-market-data Postgres (`DGS3MO` series). Validated
  against the IV Yahoo itself publishes, using a frozen fixture from a real
  chain.
- **Pending:** ingest `DGS3MO` into `public-market-data` for real (today
  only the README's fixed example rate has been exercised; the real command
  depends on the series existing in the neighboring Postgres).
- **Next step:** decide whether a second cut for daily snapshots (via
  Airflow, matching `public-market-data`'s pattern) is worth it to start
  accumulating surface history — without it, a vol backtest stays out of
  reach.
