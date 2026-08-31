"""Estimate the effect of local housing supply on ZIP-level rents.

Primary specification is Callaway-Sant'Anna with never-treated controls. The TWFE
dose-response is reported alongside it as a specification check, not as the headline.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from nycsupply import did, geo, panel  # noqa: E402
from nycsupply.io import INTERIM, RAW, ROOT  # noqa: E402

OUT = ROOT / "outputs"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    d = pd.read_parquet(INTERIM / "panel.parquet")
    print(f"panel: {d['zip'].nunique()} ZIPs, {d['q'].nunique()} quarters, "
          f"{d['lr'].notna().sum():,} rent observations\n")

    res = did.callaway_santanna(d, emin=-8, emax=12, n_boot=2000, seed=7)
    tab = res.frame()
    print(f"Callaway-Sant'Anna: {res.n_treated} treated ZIPs vs "
          f"{res.n_control} never-treated\n")
    print("  event time  ATT(log)   se      t      95% CI")
    for _, r in tab.iterrows():
        if np.isnan(r["att"]):
            continue
        star = " *" if abs(r["t"]) > 1.96 else ""
        print(f"  {int(r['etime']):+4d}q     {r['att']:+.4f}  {r['se']:.4f}  "
              f"{r['t']:+5.2f}  [{r['lo']:+.4f}, {r['hi']:+.4f}]{star}")
    tab.to_csv(OUT / "event_study.csv", index=False)

    stat, p, dof = res.pretrend_test()
    print(f"\npre-trend joint test: chi2({dof}) = {stat:.2f}, p = {p:.3f}")
    print("  -> " + ("pre-trends REJECT parallel trends; design does not identify"
                     if p < 0.05 else
                     "no evidence against parallel trends"))

    post = tab[(tab["etime"] >= 0) & tab["att"].notna()]
    w = np.ones(len(post))
    agg, agg_se = np.average(post["att"], weights=w), post["se"].mean()
    print(f"\naverage post-treatment ATT: {agg:+.4f} log points "
          f"({100*agg:+.2f}% rent), mean se {agg_se:.4f}")
    for e in [4, 8, 12]:
        if e in set(tab["etime"]) and not np.isnan(res.se[list(res.event_time).index(e)]):
            print(f"  MDE at +{e}q (80% power): {100*res.mde(e):.2f}% rent")

    print("\nTWFE dose-response (specification check; biased under staggered "
          "continuous treatment):")
    dr, model, nobs = did.dose_response(d, dose="cum8", leads=4, lags=8)
    print(f"  n = {nobs:,}")
    for _, r in dr.iterrows():
        lab = "lead" if r["lag"] < 0 else "lag "
        print(f"  {lab} {int(abs(r['lag'])):2d}q  {r['coef']:+.5f}  "
              f"(se {r['se']:.5f}, t {r['t']:+.2f})")
    dr.to_csv(OUT / "dose_response.csv", index=False)

    print("\nSensitivity to the control-group threshold:")
    pluto = geo.load_pluto(RAW)
    stock = geo.zip_stock(pluto)
    comp = geo.attach_zip(geo.load_completions(RAW), pluto)
    rent, cov = panel.load_zori(RAW / "zori_zip.csv")
    rows = []
    for cm in [0.75, 1.0, 1.25, 1.5]:
        dd = panel.build(rent, cov, comp, stock, control_max=cm)
        rr = did.callaway_santanna(dd, emin=-8, emax=12, n_boot=400, seed=7)
        t = rr.frame()
        p8 = t[(t["etime"] >= 0) & (t["etime"] <= 8) & t["att"].notna()]
        rows.append({"control_max": cm, "n_treated": rr.n_treated,
                     "n_control": rr.n_control, "att_0_8": p8["att"].mean(),
                     "se": p8["se"].mean(), "pretrend_p": rr.pretrend_test()[1]})
    s = pd.DataFrame(rows)
    print(s.round(4).to_string(index=False))
    s.to_csv(OUT / "sensitivity.csv", index=False)


if __name__ == "__main__":
    main()
