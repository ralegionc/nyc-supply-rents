"""Fetch PLUTO lot-level BBL / ZIP / residential units (paginated).

PLUTO is ~858k lots; Socrata caps a page at 50k, so this walks offsets until a page
comes back short. Ordering by bbl makes the pagination stable across runs.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nycsupply.io import RAW, socrata  # noqa: E402

DATASET = "64uk-42ks"
PAGE = 50_000


def main(force: bool = False) -> None:
    print("PLUTO lots:")
    for page in range(40):  # generous upper bound; loop exits on a short page
        dest = RAW / f"pluto_bbl_{page}.json"
        socrata(DATASET, dest, select="bbl,zipcode,unitsres",
                order="bbl", limit=PAGE, offset=page * PAGE,
                name=f"pluto_bbl_{page}", force=force)
        import json
        n = len(json.load(open(dest)))
        if n < PAGE:
            print(f"  done at page {page} ({n} rows on last page)")
            break


if __name__ == "__main__":
    main(force="--force" in sys.argv)
