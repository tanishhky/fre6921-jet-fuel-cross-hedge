"""Tests for the hedge engine (owner: Tanishk Yadav). Run from the repo root: pytest -q"""
import numpy as np
import pandas as pd
import pytest

from src.hedge import (changes, estimate_hedge_ratio, hedge_effectiveness, ols_hedge_ratio,
                       rolling_out_of_sample)


def synthetic(n=1500, beta=0.8, seed=1):
    """Random-walk futures and a spot price that loads on them with a known beta plus basis noise."""
    rng = np.random.default_rng(seed)
    dF = rng.normal(0, 0.03, n)
    dS = beta * dF + rng.normal(0, 0.012, n)
    idx = pd.bdate_range("2010-01-04", periods=n)
    return pd.DataFrame({"jet": 2 + np.cumsum(dS), "ho": 2 + np.cumsum(dF)}, index=idx)


def with_future(px, k=300, seed=99):
    """Append k future days with wild prices that would change any estimate they leaked into."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(px.index[-1] + pd.offsets.BDay(), periods=k)
    fut = pd.DataFrame({"jet": 50 + rng.normal(0, 5, k), "ho": -20 + rng.normal(0, 5, k)}, index=idx)
    return pd.concat([px, fut])


def test_ols_recovers_known_beta():
    px = synthetic(beta=0.8)
    fit = estimate_hedge_ratio(px, px.index[-1], horizon=1)
    assert abs(fit.h - 0.8) < 3 * fit.se


def test_changes_end_on_decision_date_and_do_not_overlap():
    px = synthetic()
    d = px.index[700]
    ch = changes(px, 5, d)
    assert ch.index.max() == d
    gaps = np.diff([px.index.get_loc(t) for t in ch.index])
    assert set(gaps) == {5}


def test_minimum_variance_ratio_beats_other_ratios_in_sample():
    px = synthetic()
    ch = changes(px, 5, px.index[-1])
    h, *_ = ols_hedge_ratio(ch["dS"], ch["dF"])
    he_star = hedge_effectiveness(ch["dS"], ch["dF"], h)
    for other in (0.0, 0.5, 1.0, 1.2):
        assert he_star >= hedge_effectiveness(ch["dS"], ch["dF"], other) - 1e-12
    assert hedge_effectiveness(ch["dS"], ch["dF"], 0.0) == pytest.approx(0.0)


def test_estimate_ignores_future_data():
    """No lookahead: adding data after the decision date leaves the estimate unchanged."""
    px = synthetic()
    d = px.index[900]
    a = estimate_hedge_ratio(px, d, horizon=5, window=104)
    b = estimate_hedge_ratio(with_future(px), d, horizon=5, window=104)
    assert (a.h, a.se, a.r2, a.n) == (b.h, b.se, b.r2, b.n)
    assert a.last_change_end <= d


def test_rolling_past_decisions_unchanged_by_future_data():
    """Every past hedge ratio in the rolling backtest is identical after future data is appended."""
    px = synthetic()
    base = rolling_out_of_sample(px, horizon=5, window=104)
    ext = rolling_out_of_sample(with_future(px), horizon=5, window=104)
    common = base.index.intersection(ext.index)
    assert len(common) == len(base)
    pd.testing.assert_series_equal(base["h_mv"], ext.loc[common, "h_mv"])
    assert (base["realised_end"] > base.index).all()
