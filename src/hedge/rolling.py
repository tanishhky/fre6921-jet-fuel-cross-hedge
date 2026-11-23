"""Rolling out-of-sample evaluation. Owner: Tanishk Yadav.

At each decision date the hedge ratio is estimated from changes that end on or before that date, then held
over the next `horizon` trading days. The realised change over that holding period is only read after the
decision has been recorded, and it never enters a later estimate until its end date has passed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .engine import FUT, SPOT, estimate_hedge_ratio, hedge_effectiveness, hedged_cost_change


def rolling_out_of_sample(prices: pd.DataFrame, horizon: int, window: int, min_changes: int | None = None,
                          spot: str = SPOT, fut: str = FUT) -> pd.DataFrame:
    """One row per decision date: the hedge ratio set that day and the change realised over the next horizon."""
    px = prices[[spot, fut]].dropna()
    dates = px.index
    need = (min_changes or window) * horizon
    rows = []
    for i in range(need, len(px) - horizon, horizon):
        d = dates[i]
        fit = estimate_hedge_ratio(px, d, horizon, window, spot, fut)
        j = i + horizon
        dS = px[spot].iat[j] - px[spot].iat[i]
        dF = px[fut].iat[j] - px[fut].iat[i]
        rows.append(dict(decision=d, realised_end=dates[j], h_mv=fit.h, h_se=fit.se, n_est=fit.n,
                         dS=dS, dF=dF))
    out = pd.DataFrame(rows).set_index("decision")
    out["cost_none"] = out["dS"]
    out["cost_naive"] = hedged_cost_change(out["dS"], out["dF"], 1.0)
    out["cost_mv"] = hedged_cost_change(out["dS"], out["dF"], out["h_mv"])
    return out


def bootstrap_ci(oos: pd.DataFrame, col: str, n_boot: int = 2000, seed: int = 6921, level: float = 0.95):
    """Bootstrap interval for the variance reduction of strategy `col` against no hedge, resampling periods."""
    rng = np.random.default_rng(seed)
    a, b = oos["cost_none"].to_numpy(), oos[col].to_numpy()
    n = len(a)
    stats = []
    for _ in range(n_boot):
        k = rng.integers(0, n, n)
        stats.append(1 - np.var(b[k], ddof=1) / np.var(a[k], ddof=1))
    lo, hi = np.quantile(stats, [(1 - level) / 2, 1 - (1 - level) / 2])
    return float(lo), float(hi)


def summarize(oos: pd.DataFrame) -> dict:
    """Out-of-sample hedge effectiveness of the one-to-one and minimum-variance hedges against no hedge."""
    res = dict(n=len(oos), first=str(oos.index.min().date()), last=str(oos["realised_end"].max().date()),
               sd_none=float(oos["cost_none"].std(ddof=1)), sd_naive=float(oos["cost_naive"].std(ddof=1)),
               sd_mv=float(oos["cost_mv"].std(ddof=1)), h_mean=float(oos["h_mv"].mean()),
               h_min=float(oos["h_mv"].min()), h_max=float(oos["h_mv"].max()))
    for k in ("naive", "mv"):
        res[f"he_{k}"] = hedge_effectiveness(oos["dS"], oos["dF"], 1.0 if k == "naive" else oos["h_mv"])
        res[f"he_{k}_ci"] = bootstrap_ci(oos, f"cost_{k}")
    return res
