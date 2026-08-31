"""Figures: the event study, and the ZORI coverage-selection problem."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from nycsupply import geo, panel  # noqa: E402
from nycsupply.io import INTERIM, RAW, ROOT  # noqa: E402

FIG = ROOT / "outputs" / "figures"
INK, ACCENT, MUTED = "#1a1a1a", "#c2410c", "#9ca3af"


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=9)
    ax.grid(axis="y", color="#e5e7eb", lw=0.8)
    ax.set_axisbelow(True)


def event_study():
    t = pd.read_csv(ROOT / "outputs" / "event_study.csv").dropna(subset=["att"])
    fig, ax = plt.subplots(figsize=(9, 5))
    style(ax)
    ax.axhline(0, color=MUTED, lw=1)
    ax.axvline(-0.5, color=MUTED, lw=1, ls="--")
    ax.fill_between(t["etime"], 100 * t["lo"], 100 * t["hi"],
                    color=ACCENT, alpha=0.15, lw=0)
    ax.plot(t["etime"], 100 * t["att"], color=ACCENT, lw=2, marker="o", ms=4)
    ax.set_xlabel("quarters since the ZIP's first large supply shock", fontsize=10)
    ax.set_ylabel("effect on rent (%)", fontsize=10)
    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(2))
    ax.set_title("A supply shock of 2%+ of ZIP housing stock moves rents by "
                 "less than 2%", fontsize=12, color=INK, pad=30, loc="left")
    ax.text(0.0, 1.015, "Callaway-Sant'Anna ATT, never-treated controls, "
            "95% CI from a ZIP-clustered bootstrap",
            transform=ax.transAxes, fontsize=9, color="#6b7280", va="bottom")
    fig.tight_layout()
    fig.savefig(FIG / "event_study.png", dpi=160, bbox_inches="tight")
    print(f"  wrote {FIG/'event_study.png'}")


def coverage_selection():
    """The finding that matters: rent data is missing where supply shocks are cheap."""
    pluto = geo.load_pluto(RAW)
    stock = geo.zip_stock(pluto)
    comp = geo.attach_zip(geo.load_completions(RAW), pluto)
    cov = pd.read_csv(INTERIM / "zori_coverage.csv", dtype={"zip": str}
                      ).set_index("zip")["zori_months"]

    comp["y"] = comp["date"].dt.year
    ann = (comp[comp["y"].between(2015, 2025)]
           .groupby(["zip", "y"], as_index=False)["net"].sum()
           .merge(stock, on="zip"))
    ann["pct"] = 100 * ann["net"] / ann["stock"]
    peak = (ann[ann["stock"] >= 3000].groupby("zip")["pct"].max()
            .rename("max_shock").to_frame())
    peak["months"] = peak.index.map(cov).fillna(0)
    peak = peak[peak["max_shock"] > 0]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    style(ax)
    dark = peak["months"] < 12
    # One ZIP (10004, FiDi) peaks at ~29% and flattens everything else if left in
    # frame; clip the axis and mark it rather than losing the bulk of the data.
    CAP = 12.0
    rng = np.random.default_rng(0)
    jit = rng.uniform(-1.2, 1.2, len(peak))    # separates the pile at zero coverage
    y = peak["max_shock"].clip(upper=CAP)
    ax.scatter(peak.loc[~dark, "months"] + jit[~dark.to_numpy()], y[~dark],
               s=34, color=MUTED, alpha=0.75, lw=0, label="covered by ZORI")
    ax.scatter(peak.loc[dark, "months"] + jit[dark.to_numpy()], y[dark],
               s=54, color=ACCENT, lw=0, label="little or no rent data")
    ax.axvline(60, color=INK, lw=1, ls="--")
    ax.set_ylim(-0.5, CAP + 0.8)
    ax.text(61, CAP + 0.1, "usable threshold (60 months)", fontsize=8.5, color=INK)
    off = peak["max_shock"] > CAP
    for z in peak.index[off]:
        ax.annotate(f"{z} ({peak.loc[z,'max_shock']:.0f}%)",
                    (peak.loc[z, "months"], CAP), textcoords="offset points",
                    xytext=(-64, -2), fontsize=8, color=MUTED)
    ax.set_xlabel("months of Zillow ZORI coverage, 2015-2026 (jittered)", fontsize=10)
    ax.set_ylabel("largest annual supply shock (% of ZIP stock)", fontsize=10)
    ax.set_title("The neighbourhoods where supply might matter most are the ones "
                 "no rent index covers", fontsize=12, color=INK, pad=30, loc="left")
    ax.text(0.0, 1.015, f"{int(dark.sum())} of {len(peak)} NYC ZIPs with a measurable "
            "supply shock have under 12 months of rent data",
            transform=ax.transAxes, fontsize=9, color="#6b7280", va="bottom")
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG / "zori_coverage_selection.png", dpi=160, bbox_inches="tight")
    print(f"  wrote {FIG/'zori_coverage_selection.png'}")
    n_dark = int(dark.sum())
    print(f"  {n_dark} ZIPs with a supply shock have <12 months of rent data")


if __name__ == "__main__":
    FIG.mkdir(parents=True, exist_ok=True)
    print("figures:")
    event_study()
    coverage_selection()
