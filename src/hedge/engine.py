"""Minimum-variance hedge engine. Owner: Tanishk Yadav.

Every function that reads prices takes an explicit decision date `as_of` and uses only rows dated on or
before it. Nothing here calls the clock, so a past decision can always be reproduced exactly.

Conventions
-----------
prices : DataFrame indexed by trading date, with a spot column (jet fuel, $/gal) and a futures column
         (NYMEX HO front month, $/gal).
change : price at the end of a horizon minus price at its start, over non-overlapping horizons counted
         back from the decision date, so the most recent change ends on the decision date.
h      : futures position per unit of exposure. The airline is short the physical, so its cost change per
         gallon is dS - h dF, and h* minimises the variance of that cost.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

SPOT, FUT = "jet", "ho"


@dataclass(frozen=True)
class HedgeFit:
    as_of: pd.Timestamp
    horizon: int          # trading days per change
    window: int | None    # number of past changes used (None = all available)
    h: float              # minimum-variance hedge ratio
    se: float             # OLS standard error of h
    r2: float             # in-sample hedge effectiveness, equal to the regression R^2
    n: int                # number of changes used
    first_change_end: pd.Timestamp
    last_change_end: pd.Timestamp


def visible(prices: pd.DataFrame, as_of) -> pd.DataFrame:
    """Rows a decision taken on `as_of` is allowed to see."""
    as_of = pd.Timestamp(as_of)
    past = prices.loc[prices.index <= as_of]
    if len(past):
        assert past.index.max() <= as_of, "lookahead: a row after the decision date leaked in"
    return past


def changes(prices: pd.DataFrame, horizon: int, as_of, spot: str = SPOT, fut: str = FUT) -> pd.DataFrame:
    """Non-overlapping `horizon`-day changes ending on or before `as_of`, newest ending on the last visible row."""
    past = visible(prices, as_of)[[spot, fut]].dropna()
    ends = np.arange(len(past) - 1, horizon - 1, -horizon)[::-1]
    starts = ends - horizon
    out = pd.DataFrame({
        "dS": past[spot].to_numpy()[ends] - past[spot].to_numpy()[starts],
        "dF": past[fut].to_numpy()[ends] - past[fut].to_numpy()[starts],
    }, index=past.index[ends])
    out.index.name = "change_end"
    return out


def ols_hedge_ratio(dS, dF) -> tuple[float, float, float, int]:
    """OLS of dS on [1, dF]. Returns slope, its standard error, R^2 and n."""
    y, x = np.asarray(dS, float), np.asarray(dF, float)
    n = len(y)
    if n < 3:
        raise ValueError("need at least 3 changes to estimate a hedge ratio")
    X = np.column_stack([np.ones(n), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ beta
    s2 = e @ e / (n - 2)
    se = float(np.sqrt(s2 * np.linalg.inv(X.T @ X)[1, 1]))
    r2 = float(1 - (e @ e) / np.sum((y - y.mean()) ** 2))
    return float(beta[1]), se, r2, n


def estimate_hedge_ratio(prices: pd.DataFrame, as_of, horizon: int, window: int | None = None,
                         spot: str = SPOT, fut: str = FUT) -> HedgeFit:
    """h* estimated on a decision date, from the last `window` non-overlapping changes it can see."""
    as_of = pd.Timestamp(as_of)
    ch = changes(prices, horizon, as_of, spot, fut)
    if window is not None:
        ch = ch.iloc[-window:]
    assert ch.index.max() <= as_of, "lookahead: a change ending after the decision date was used"
    h, se, r2, n = ols_hedge_ratio(ch["dS"], ch["dF"])
    return HedgeFit(as_of, horizon, window, h, se, r2, n, ch.index.min(), ch.index.max())


def hedged_cost_change(dS, dF, h) -> np.ndarray:
    """Change in the airline's fuel cost per gallon after a long futures hedge of ratio h."""
    return np.asarray(dS, float) - np.asarray(h, float) * np.asarray(dF, float)


def hedge_effectiveness(dS, dF, h) -> float:
    """Share of the unhedged cost variance removed: 1 - Var(dS - h dF) / Var(dS)."""
    return float(1 - np.var(hedged_cost_change(dS, dF, h), ddof=1) / np.var(np.asarray(dS, float), ddof=1))
