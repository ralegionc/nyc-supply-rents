"""Panel construction: ZIP x quarter rents, supply dose, and treatment cohorts."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

NYC_COUNTIES = ["New York County", "Kings County", "Queens County",
                "Bronx County", "Richmond County"]

# Defaults chosen from the feasibility pull, not from taste:
MIN_STOCK = 3_000      # below this, ZIPs are commercial; 10103 has 59 units and a 293% "shock"
MIN_MONTHS = 60        # ZORI coverage needed for a ZIP to be usable
TREAT_PCT = 2.0        # trailing-4q supply, % of stock, that counts as a shock
CONTROL_MAX = 1.0      # a clean never-treated ZIP never exceeds this
PRE_MAX = 2.0          # supply before the panel opens that disqualifies a control


def load_zori(path: Path, counties=NYC_COUNTIES) -> pd.DataFrame:
    """Zillow ZORI, wide months -> long ZIP x quarter mean rent."""
    z = pd.read_csv(path, dtype={"RegionName": str})
    months = [c for c in z.columns if c[:2] == "20"]
    z = z[z["CountyName"].isin(counties)].copy()
    z["zip"] = z["RegionName"].str.zfill(5)
    cov = z.set_index("zip")[months].notna().sum(axis=1).rename("zori_months")

    long = z.melt(id_vars="zip", value_vars=months, var_name="m", value_name="rent")
    long = long.dropna(subset=["rent"])
    long["m"] = pd.to_datetime(long["m"])
    long["q"] = long["m"].dt.to_period("Q")
    rent = long.groupby(["zip", "q"], as_index=False)["rent"].mean()
    return rent, cov


def build(rent: pd.DataFrame, coverage: pd.Series, completions: pd.DataFrame,
          stock: pd.DataFrame, *, min_stock=MIN_STOCK, min_months=MIN_MONTHS,
          treat_pct=TREAT_PCT, control_max=CONTROL_MAX, pre_max=PRE_MAX) -> pd.DataFrame:
    """Balanced-ish ZIP x quarter panel with dose, cohort and event time."""
    comp = completions.copy()
    comp["q"] = comp["date"].dt.to_period("Q")
    q_units = comp.groupby(["zip", "q"], as_index=False)["net"].sum()

    # Supply that landed before the rent series opens. Hunters Point (11109) took
    # 17-24% shocks in 2012-14, which is invisible inside a panel starting 2015 — it
    # would otherwise enter as a pristine never-treated control.
    start = rent["q"].min()
    pre = (q_units[q_units["q"] < start].groupby("zip", as_index=False)["net"].sum()
           .merge(stock, on="zip", how="left"))
    pre["pre_pct"] = 100.0 * pre["net"] / pre["stock"]
    pre_treated = set(pre.loc[pre["pre_pct"] >= pre_max, "zip"])
    if pre_treated:
        print(f"  {len(pre_treated)} ZIPs disqualified as controls: >={pre_max}% of stock "
              f"built before {start}")

    keep = stock.loc[stock["stock"] >= min_stock, "zip"]
    ok_cov = coverage[coverage >= min_months].index
    zips = sorted(set(keep) & set(ok_cov) & set(rent["zip"]))

    # Rectangular ZIP x quarter frame so quarters with no completions read as zero,
    # not as missing. Getting this wrong silently drops the untreated periods.
    qs = pd.period_range(rent["q"].min(), rent["q"].max(), freq="Q")
    grid = pd.MultiIndex.from_product([zips, qs], names=["zip", "q"]).to_frame(index=False)

    d = (grid.merge(rent, on=["zip", "q"], how="left")
             .merge(q_units, on=["zip", "q"], how="left")
             .merge(stock, on="zip", how="left"))
    d["net"] = d["net"].fillna(0.0)
    d["dose"] = 100.0 * d["net"] / d["stock"]
    d = d.sort_values(["zip", "q"]).reset_index(drop=True)

    # Trailing four quarters of supply, as % of stock: the annual supply rate.
    d["cum4"] = d.groupby("zip")["dose"].transform(
        lambda s: s.rolling(4, min_periods=1).sum())
    d["cum8"] = d.groupby("zip")["dose"].transform(
        lambda s: s.rolling(8, min_periods=1).sum())

    d = _assign_cohorts(d, treat_pct=treat_pct, control_max=control_max,
                        pre_treated=pre_treated)
    d["lr"] = np.log(d["rent"])
    return d


def _assign_cohorts(d: pd.DataFrame, *, treat_pct: float, control_max: float,
                    pre_treated: set) -> pd.DataFrame:
    """Cohort g = first quarter a ZIP's trailing-4q supply crosses the threshold.

    ZIPs that never cross but do exceed `control_max` are dropped: they are neither
    a clean control nor a treated unit, and leaving them in the comparison group
    biases the estimate toward zero.
    """
    peak = d.groupby("zip")["cum4"].max()
    treated = peak[peak >= treat_pct].index
    clean = [z for z in peak[peak < control_max].index if z not in pre_treated]
    ambiguous = peak[(peak >= control_max) & (peak < treat_pct)].index
    print(f"  cohorts: {len(treated)} treated, {len(clean)} never-treated, "
          f"{len(ambiguous)} ambiguous ZIPs dropped")

    first = (d[d["cum4"] >= treat_pct].groupby("zip")["q"].min().rename("g"))
    d = d[d["zip"].isin(list(treated) + list(clean))].merge(
        first, on="zip", how="left")

    # Event time in quarters; never-treated carry NaN and act as the comparison group.
    qi = {q: i for i, q in enumerate(sorted(d["q"].unique()))}
    d["ti"] = d["q"].map(qi)
    d["gi"] = d["g"].map(qi)
    d["etime"] = d["ti"] - d["gi"]
    d["treated"] = d["gi"].notna()
    return d
