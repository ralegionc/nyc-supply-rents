"""Validate the Callaway-Sant'Anna implementation against panels with known answers.

Simulated data is appropriate here: the point is checking that the estimator recovers
an effect that was planted on purpose, which real data cannot tell us. The findings
themselves are always estimated on the real panel.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd
import pytest

from nycsupply import did


def make_panel(n_treat=40, n_ctrl=30, T=40, effect=0.0, trend_gap=0.0, seed=0,
               noise=0.01):
    """Staggered panel with a known post-treatment level shift.

    `effect` is the per-period log-point shift applied from treatment onward.
    `trend_gap` adds a differential pre-trend to the treated group, which the
    pre-trend test should detect.
    """
    rng = np.random.default_rng(seed)
    rows = []
    cohorts = rng.integers(10, T - 12, n_treat)
    for i in range(n_treat + n_ctrl):
        treated = i < n_treat
        g = int(cohorts[i]) if treated else np.nan
        level = rng.normal(8, 0.3)
        for t in range(T):
            y = level + 0.004 * t + rng.normal(0, noise)
            if treated:
                y += trend_gap * t
                if t >= g:
                    y += effect
            rows.append({"zip": f"z{i:03d}", "ti": t, "gi": g,
                         "treated": treated, "lr": y})
    d = pd.DataFrame(rows)
    d["q"] = d["ti"]
    return d


def test_recovers_planted_effect():
    d = make_panel(effect=-0.05, seed=1)
    r = did.callaway_santanna(d, emin=-6, emax=8, n_boot=200, seed=1)
    tab = r.frame()
    post = tab[(tab["etime"] >= 0) & tab["att"].notna()]
    assert post["att"].mean() == pytest.approx(-0.05, abs=0.01)


def test_null_effect_is_null():
    d = make_panel(effect=0.0, seed=2)
    r = did.callaway_santanna(d, emin=-6, emax=8, n_boot=200, seed=2)
    tab = r.frame()
    post = tab[(tab["etime"] >= 0) & tab["att"].notna()]
    assert abs(post["att"].mean()) < 0.01
    assert (post["t"].abs() > 1.96).mean() < 0.35   # few spurious rejections


def test_baseline_period_is_normalised():
    d = make_panel(effect=-0.05, seed=3)
    r = did.callaway_santanna(d, emin=-4, emax=4, n_boot=50, seed=3)
    tab = r.frame().set_index("etime")
    assert tab.loc[-1, "att"] == pytest.approx(0.0, abs=1e-12)


def test_pretrend_test_passes_when_trends_parallel():
    d = make_panel(effect=-0.05, trend_gap=0.0, seed=4)
    r = did.callaway_santanna(d, emin=-6, emax=6, n_boot=300, seed=4)
    _, p, _ = r.pretrend_test()
    assert p > 0.05


def test_pretrend_test_catches_differential_trend():
    d = make_panel(effect=0.0, trend_gap=0.002, seed=5)
    r = did.callaway_santanna(d, emin=-6, emax=6, n_boot=300, seed=5)
    _, p, _ = r.pretrend_test()
    assert p < 0.05, "a planted differential pre-trend should be detected"


def test_never_treated_only_panel_returns_nan():
    d = make_panel(n_treat=0, n_ctrl=20, seed=6)
    r = did.callaway_santanna(d, emin=-2, emax=2, n_boot=20, seed=6)
    assert np.isnan(r.att).all()
