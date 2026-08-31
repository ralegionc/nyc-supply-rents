"""Guard the identifier normalisation that the BBL join depends on."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import pytest

from nycsupply import geo


def test_clean_id_strips_float_suffix():
    s = pd.Series(["1000030001.0", "4114170006", " 3012340005 ", 2022220003])
    out = geo.clean_id(s).tolist()
    assert out == ["1000030001", "4114170006", "3012340005", "2022220003"]


def test_clean_zip_pads_and_filters():
    s = pd.Series(["10001.0", "7302", "11201", "99999", None])
    out = geo.clean_zip(s).tolist()
    assert out[0] == "10001"
    assert out[1] is None or pd.isna(out[1])   # 07302 is Jersey City
    assert out[2] == "11201"
    assert pd.isna(out[3]) and pd.isna(out[4])


def test_attach_zip_rejects_a_broken_join():
    """A join that silently collapses should raise, not return a tiny frame."""
    comp = pd.DataFrame({"bbl": ["1000030001"] * 10,
                         "net": [5.0] * 10,
                         "date": pd.to_datetime(["2020-01-01"] * 10)})
    pluto = pd.DataFrame({"bbl": ["9999999999"], "zip": ["11201"],
                          "unitsres": [10.0]})
    with pytest.raises(ValueError, match="join degraded"):
        geo.attach_zip(comp, pluto)


def test_zip_stock_sums_units():
    pluto = pd.DataFrame({"bbl": ["1", "2", "3"], "zip": ["10001", "10001", "11201"],
                          "unitsres": [10.0, 5.0, 7.0]})
    st = geo.zip_stock(pluto).set_index("zip")["stock"]
    assert st["10001"] == 15.0 and st["11201"] == 7.0
