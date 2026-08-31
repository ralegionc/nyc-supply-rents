"""Fetch NYC HousingDB project-level completions that added net residential units.

`classanet` is the net change in Class A (permanent residential) units, so filtering to
`classanet > 0` keeps genuine supply additions and drops demolitions and conversions.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nycsupply.io import RAW, socrata  # noqa: E402

DATASET = "br6q-ssj3"


def main(force: bool = False) -> None:
    print("HousingDB completions:")
    socrata(
        DATASET, RAW / "housingdb_completions.json",
        select="job_number,bbl,job_type,classanet,datecomplt,job_status,datepermit,latitude,longitude",
        where="datecomplt > '2012-01-01' and classanet > 0",
        limit=50_000, name="housingdb_completions", force=force,
    )


if __name__ == "__main__":
    main(force="--force" in sys.argv)
