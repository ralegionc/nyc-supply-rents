"""Callaway & Sant'Anna (2021) group-time ATT, hand-rolled.

No DiD package is assumed. The estimator is small enough to write out, and writing it
out means the identifying comparison is visible rather than buried in a library call.

For cohort g (first quarter treated) and period t, with a never-treated comparison group
and baseline period b = g-1:

    ATT(g,t) = E[Y_t - Y_b | G = g] - E[Y_t - Y_b | never treated]

Event-time aggregates average ATT(g, g+e) across cohorts, weighted by cohort size.
Standard errors come from a nonparametric bootstrap that resamples whole ZIPs, which
is the level treatment is assigned at.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class CSResult:
    event_time: np.ndarray
    att: np.ndarray
    se: np.ndarray
    cohort_sizes: dict
    n_treated: int
    n_control: int
    boot: np.ndarray = field(repr=False, default=None)

    def frame(self) -> pd.DataFrame:
        df = pd.DataFrame({"etime": self.event_time, "att": self.att, "se": self.se})
        df["t"] = df["att"] / df["se"]
        df["lo"] = df["att"] - 1.96 * df["se"]
        df["hi"] = df["att"] + 1.96 * df["se"]
        return df

    def pretrend_test(self) -> tuple[float, float, int]:
        """Joint test that all pre-period ATTs are zero, using the bootstrap covariance."""
        # e = -1 is the baseline period and is zero by construction, so it carries no
        # information and would make the covariance singular.
        pre = (self.event_time < 0) & (self.event_time != -1)
        if pre.sum() == 0 or self.boot is None:
            return np.nan, np.nan, 0
        b = self.boot[:, pre]
        keep = ~np.isnan(b).any(axis=0)
        b, theta = b[:, keep], self.att[pre][keep]
        if theta.size == 0:
            return np.nan, np.nan, 0
        cov = np.cov(b, rowvar=False)
        cov = np.atleast_2d(cov)
        stat = float(theta @ np.linalg.pinv(cov) @ theta)
        dof = int(np.linalg.matrix_rank(cov))
        return stat, float(stats.chi2.sf(stat, dof)), dof

    def mde(self, e: int, power: float = 0.8) -> float:
        """Minimum detectable effect at a given event time (two-sided, alpha=0.05)."""
        z = stats.norm.ppf(1 - 0.05 / 2) + stats.norm.ppf(power)
        i = int(np.where(self.event_time == e)[0][0])
        return z * self.se[i]


def _wide(d: pd.DataFrame, outcome: str):
    """Y matrix [zip x period], plus cohort index per ZIP."""
    y = d.pivot_table(index="zip", columns="ti", values=outcome, aggfunc="mean")
    y = y.reindex(columns=sorted(d["ti"].unique()))
    g = d.groupby("zip")["gi"].first().reindex(y.index)
    return y.to_numpy(dtype=float), g.to_numpy(dtype=float), y.index.to_numpy()


def _att_gt(Y: np.ndarray, G: np.ndarray, elist: np.ndarray):
    """Event-time ATTs for one (possibly resampled) panel."""
    T = Y.shape[1]
    never = np.isnan(G)
    out, wts = np.full(len(elist), np.nan), np.zeros(len(elist))
    num = np.zeros(len(elist))

    for gi, g in enumerate(np.unique(G[~never])):
        g = int(g)
        b = g - 1
        if b < 0 or b >= T:
            continue
        in_g = (G == g)
        for k, e in enumerate(elist):
            t = g + e
            if t < 0 or t >= T:
                continue
            # A unit contributes only if it is observed in both baseline and t.
            dt = Y[:, t] - Y[:, b]
            tr = dt[in_g & ~np.isnan(dt)]
            co = dt[never & ~np.isnan(dt)]
            if tr.size == 0 or co.size < 2:
                continue
            att = tr.mean() - co.mean()
            num[k] += att * tr.size
            wts[k] += tr.size

    out = np.where(wts > 0, num / np.where(wts == 0, 1, wts), np.nan)
    return out, wts


def callaway_santanna(d: pd.DataFrame, *, outcome="lr", emin=-8, emax=12,
                      n_boot=1000, seed=0) -> CSResult:
    """Group-time ATT with never-treated controls and a ZIP-clustered bootstrap."""
    elist = np.arange(emin, emax + 1)
    Y, G, zips = _wide(d, outcome)
    att, wts = _att_gt(Y, G, elist)

    rng = np.random.default_rng(seed)
    n = Y.shape[0]
    boot = np.full((n_boot, len(elist)), np.nan)
    for bidx in range(n_boot):
        idx = rng.integers(0, n, n)          # resample ZIPs with replacement
        boot[bidx], _ = _att_gt(Y[idx], G[idx], elist)

    se = np.nanstd(boot, axis=0, ddof=1)
    cohort_sizes = (d[d["treated"]].groupby("gi")["zip"].nunique().to_dict())
    return CSResult(elist, att, se, cohort_sizes,
                    n_treated=int(d[d["treated"]]["zip"].nunique()),
                    n_control=int(d[~d["treated"]]["zip"].nunique()),
                    boot=boot)


def dose_response(d: pd.DataFrame, *, outcome="lr", dose="cum8", leads=4, lags=8):
    """Continuous-dose distributed lag with ZIP and quarter fixed effects.

    Reported as a specification check only. Two-way fixed effects is biased under
    staggered and repeated continuous treatment (Goodman-Bacon 2021; de Chaisemartin
    and D'Haultfoeuille 2020); it is here to show the intensity margin and to confirm
    the panel behaves, not to carry the headline.
    """
    import statsmodels.formula.api as smf

    w = d.dropna(subset=[outcome]).sort_values(["zip", "q"]).copy()
    terms = []
    for L in range(-leads, lags + 1):
        col = f"d_{'m' if L < 0 else 'p'}{abs(L)}"
        w[col] = w.groupby("zip")[dose].shift(L)
        terms.append(col)
    w["qs"] = w["q"].astype(str)
    w = w.dropna(subset=terms)
    f = f"{outcome} ~ " + " + ".join(terms) + " + C(zip) + C(qs)"
    m = smf.ols(f, data=w).fit(cov_type="cluster", cov_kwds={"groups": w["zip"]})
    res = pd.DataFrame({
        "lag": list(range(-leads, lags + 1)),
        "coef": [m.params[t] for t in terms],
        "se": [m.bse[t] for t in terms],
    })
    res["t"] = res["coef"] / res["se"]
    return res, m, len(w)
