"""BBL and ZIP normalisation, and the HousingDB -> PLUTO -> ZIP join.

Two traps live here, both hit during the feasibility pull:

1. Socrata serialises numeric-ish text columns inconsistently. The same BBL comes back
   as "4114170006" from one dataset and "1000030001.0" from another, so a naive string
   join silently drops most rows.
2. PLUTO carries ZIPs that are not NYC residential ZIPs (PO boxes, a few NJ artefacts).
   Guarding to ^1[01]\\d{3}$ keeps the denominator honest.
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

import pandas as pd

NYC_ZIP = r"^1[01]\d{3}$"


def clean_id(s: pd.Series) -> pd.Series:
    """Normalise a Socrata numeric-ish identifier to a bare digit string."""
    return s.astype(str).str.strip().str.split(".").str[0]


def clean_zip(s: pd.Series) -> pd.Series:
    """Five-digit ZIP string, blanked where it is not a plausible NYC ZIP."""
    z = clean_id(s).str.zfill(5)
    return z.where(z.str.match(NYC_ZIP))


def load_pluto(raw_dir: Path) -> pd.DataFrame:
    """PLUTO lots as bbl / zip / residential units."""
    files = sorted(glob.glob(str(raw_dir / "pluto_bbl_*.json")))
    if not files:
        raise FileNotFoundError(f"no pluto_bbl_*.json in {raw_dir}; run 01_fetch_pluto.py")
    df = pd.concat([pd.DataFrame(json.load(open(f))) for f in files], ignore_index=True)
    df["bbl"] = clean_id(df["bbl"])
    df["zip"] = clean_zip(df["zipcode"])
    df["unitsres"] = pd.to_numeric(df.get("unitsres"), errors="coerce").fillna(0.0)
    return df.dropna(subset=["zip"])[["bbl", "zip", "unitsres"]]


def zip_stock(pluto: pd.DataFrame) -> pd.DataFrame:
    """Residential units per ZIP — the denominator for the dose variable."""
    return (pluto.groupby("zip", as_index=False)["unitsres"].sum()
                 .rename(columns={"unitsres": "stock"}))


def load_completions(raw_dir: Path) -> pd.DataFrame:
    """HousingDB jobs that completed and added net Class A units."""
    path = raw_dir / "housingdb_completions.json"
    df = pd.DataFrame(json.load(open(path)))
    df["bbl"] = clean_id(df["bbl"])
    df["net"] = pd.to_numeric(df["classanet"], errors="coerce")
    df["date"] = pd.to_datetime(df["datecomplt"], errors="coerce").dt.tz_localize(None)
    return df.dropna(subset=["net", "date"])


def attach_zip(completions: pd.DataFrame, pluto: pd.DataFrame) -> pd.DataFrame:
    """Join completions to ZIP via BBL. Reports the match rate, which should exceed 99%."""
    lots = pluto.drop_duplicates("bbl")[["bbl", "zip"]]
    m = completions.merge(lots, on="bbl", how="left")
    rate = m["zip"].notna().mean()
    unit_rate = m.loc[m["zip"].notna(), "net"].sum() / m["net"].sum()
    print(f"  bbl->zip match: {rate:.1%} of jobs, {unit_rate:.1%} of units")
    if rate < 0.95:
        raise ValueError(f"BBL join degraded to {rate:.1%} — check id normalisation")
    return m.dropna(subset=["zip"])
