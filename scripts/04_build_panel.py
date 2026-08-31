"""Build the ZIP x quarter analysis panel from the cached raw pulls."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from nycsupply import geo, panel  # noqa: E402
from nycsupply.io import INTERIM, RAW  # noqa: E402


def main() -> None:
    INTERIM.mkdir(parents=True, exist_ok=True)

    print("PLUTO:")
    pluto = geo.load_pluto(RAW)
    stock = geo.zip_stock(pluto)
    print(f"  {len(pluto):,} lots, {len(stock)} ZIPs, "
          f"{stock['stock'].sum():,.0f} residential units")
    stock.to_csv(INTERIM / "zip_stock.csv", index=False)

    print("HousingDB:")
    comp = geo.load_completions(RAW)
    comp = geo.attach_zip(comp, pluto)
    print(f"  {len(comp):,} completions, {comp['net'].sum():,.0f} net units")
    comp.to_parquet(INTERIM / "completions_zip.parquet")

    print("ZORI:")
    rent, cov = panel.load_zori(RAW / "zori_zip.csv")
    print(f"  {rent['zip'].nunique()} NYC ZIPs, "
          f"{rent['q'].min()} to {rent['q'].max()}")
    cov.to_csv(INTERIM / "zori_coverage.csv")

    print("Panel:")
    d = panel.build(rent, cov, comp, stock)
    obs = d["lr"].notna().sum()
    print(f"  {d['zip'].nunique()} ZIPs x {d['q'].nunique()} quarters, "
          f"{obs:,} non-missing rent observations")
    d.to_parquet(INTERIM / "panel.parquet")
    print(f"  wrote {INTERIM / 'panel.parquet'}")


if __name__ == "__main__":
    main()
