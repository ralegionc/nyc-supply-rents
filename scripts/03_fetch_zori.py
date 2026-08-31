"""Fetch the Zillow ZORI rent index at ZIP level.

Use the ZIP file, not the metro file: metro-level is far too coarse for anything
resembling a local supply shock. `sfrcondomfr` is the all-home-type series.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nycsupply.io import RAW, fetch  # noqa: E402

URL = ("https://files.zillowstatic.com/research/public_csvs/zori/"
       "Zip_zori_uc_sfrcondomfr_sm_month.csv")


def main(force: bool = False) -> None:
    print("Zillow ZORI (ZIP):")
    fetch(URL, RAW / "zori_zip.csv", name="zori_zip", force=force)


if __name__ == "__main__":
    main(force="--force" in sys.argv)
