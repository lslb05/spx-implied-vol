# Decisions

Record only decisions that change the future cost of change.

## Template

### YYYY-MM-DD — Title

- **Context:** what constraint or problem required a decision.
- **Decision:** the path chosen.
- **Alternatives:** relevant options discarded.
- **Consequences:** gains, costs and the trigger to revisit.

### 2026-08-18 — Keep `CLAUDE.md` and `AGENTS.md` in the public repository

- **Context:** both files declare that the repository is built with agent
  support. The alternative was ignoring them in git so the public
  repository wouldn't reveal the workflow.
- **Decision:** keep both versioned and public.
- **Alternatives:** ignore `AGENTS.md` in `.gitignore`; keep it local only.
  Both break delegation to Codex, which reads this file from the
  repository — the cost is functional and immediate, the gain is cosmetic.
- **Consequences:** the repository states the method instead of hiding it,
  which is also verifiable by whoever reads it. Revisit if some destination
  ever requires the opposite.

### 2026-08-19 — SPY as SPX proxy, and European Black-Scholes over an American option

- **Context:** the SPX index doesn't expose an option chain via `yfinance`;
  the only free ways to get index option data at scale are ETF proxies
  (SPY) or paid data (CBOE DataShop). SPY is American; the simplest pricing
  model to implement without a new dependency is Black-Scholes-Merton,
  which assumes European.
- **Decision:** use SPY's chain and accept the American-vs-European bias,
  measuring it in a test (`tests/test_skew.py`) against the IV the source
  itself publishes, instead of hiding it or trying to correct it with a
  binomial model in this first cut.
- **Alternatives:** a binomial model (Cox-Ross-Rubinstein) to correctly
  price early exercise — more faithful, but more code and more parameters
  to validate in a cut that already carries enough technical risk
  (numerical inversion). CBOE DataShop for European XSP — paid, outside the
  portfolio's public-source rule.
- **Consequences:** the bias stays small and documented for the tested
  horizon (~30 days, average difference below 0.015 vol point). If a future
  cut needs a short-dated option (a few days) or a long LEAP, the bias
  grows and the decision should be revisited — don't assume it stays small
  outside the tested range.

### 2026-08-19 — Newton-Raphson with bisection as a fallback, no `scipy`

- **Context:** inverting Black-Scholes to find IV has no closed form. Plain
  Newton-Raphson is fast but diverges when vega is near zero (a strike well
  out of the money) — common in a real chain, as the test fixture showed on
  the first contracts tried.
- **Decision:** Newton-Raphson as the fast path; if it leaves the
  `[0.0001, 5.0]` range or vega gets too small, it falls back to bisection
  on the same range, which always converges if the price is within the band
  reachable by some positive vol. Outside that band, it returns `None`
  instead of inventing a number.
- **Alternatives:** `scipy.optimize.brentq` — more battle-tested, but pulls
  in all of `scipy` (a heavy dependency) just for one root-finding function
  that's ~15 lines to implement with the guarantee this project needs.
- **Consequences:** no new dependency beyond what was already needed; the
  cost is maintaining this solver's tests (`tests/test_black_scholes.py`
  covers the price→IV round trip for vols from 5% to 80%, call and put).
