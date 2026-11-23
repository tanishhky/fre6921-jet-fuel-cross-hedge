"""Baseline for the revised proposal: no hedge vs one-to-one vs minimum-variance. Owner: Tanishk Yadav.

Reads data/processed/daily_prices.csv (build it with `python -m src.hedge.interim_data`, later with Tianze's
pipeline) and writes results/baseline_in_sample.csv, results/baseline_out_of_sample.csv and
figures/baseline_rolling_h.png.

Run:  python -m src.hedge.run_baseline
"""
from __future__ import annotations

import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .engine import changes, estimate_hedge_ratio, hedge_effectiveness
from .rolling import rolling_out_of_sample, summarize

ROOT = pathlib.Path(__file__).resolve().parents[2]
HORIZONS = {"1 week": 5, "1 month": 21, "1 quarter": 63}
WINDOW_DAYS = 756   # three years of trading days in every estimation window


def main():
    px = pd.read_csv(ROOT / "data" / "processed" / "daily_prices.csv", index_col="date", parse_dates=True)
    end = px.index.max()
    ins, oos_rows, paths = [], [], {}
    for name, hz in HORIZONS.items():
        fit = estimate_hedge_ratio(px, end, hz)
        ch = changes(px, hz, end)
        ins.append(dict(horizon=name, days=hz, n=fit.n, h_star=fit.h, se=fit.se, r2=fit.r2,
                        he_naive=hedge_effectiveness(ch["dS"], ch["dF"], 1.0),
                        first=str(fit.first_change_end.date()), last=str(fit.last_change_end.date())))
        window = WINDOW_DAYS // hz
        oos = rolling_out_of_sample(px, hz, window)
        s = summarize(oos)
        oos_rows.append(dict(horizon=name, days=hz, window_changes=window, **{k: v for k, v in s.items() if not k.endswith("_ci")},
                             he_naive_lo=s["he_naive_ci"][0], he_naive_hi=s["he_naive_ci"][1],
                             he_mv_lo=s["he_mv_ci"][0], he_mv_hi=s["he_mv_ci"][1]))
        paths[name] = oos["h_mv"]
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    pd.DataFrame(ins).to_csv(out / "baseline_in_sample.csv", index=False)
    pd.DataFrame(oos_rows).to_csv(out / "baseline_out_of_sample.csv", index=False)

    fig, ax = plt.subplots(figsize=(9, 4.2))
    for (name, s), c in zip(paths.items(), ["#57068C", "#B27D00", "#1F4E79"]):
        ax.plot(s.index, s.values, lw=1.4 if name == "1 week" else 1.8, color=c, label=f"{name} changes")
    ax.axhline(1.0, color="#555555", lw=0.9, ls="--", label="one-to-one hedge")
    ax.set_ylabel("minimum-variance hedge ratio h*")
    ax.set_title("Rolling three-year estimates of h* (jet fuel on NYMEX HO), decision dates only", fontsize=10)
    ax.legend(frameon=False, fontsize=9, ncol=4, loc="lower left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    (ROOT / "figures").mkdir(exist_ok=True)
    fig.savefig(ROOT / "figures" / "baseline_rolling_h.png", dpi=200)
    print(json.dumps(dict(sample=[str(px.index.min().date()), str(end.date())], days=len(px), in_sample=ins,
                          out_of_sample=oos_rows), indent=1, default=float))


if __name__ == "__main__":
    main()
