import pandas as pd
import numpy as np
from utils.indicators import wma, calc_mavilimw

def test_wma_basic():
    s = pd.Series([1, 2, 3, 4, 5])
    result = wma(s, 3)
    expected = pd.Series([np.nan, np.nan, 14 / 6, 20 / 6, 26 / 6])
    assert result.isna().sum() == 2
    np.testing.assert_allclose(result.dropna().values, expected.dropna().values)


def test_calc_mavilimw_chain():
    close = pd.Series(range(1, 21), name="Close")
    df = pd.DataFrame({"Close": close})

    # expected calculation using explicit WMA chain
    fmal = 3
    smal = 5
    tmal = fmal + smal
    Fmal = smal + tmal
    Ftmal = tmal + Fmal
    Smal = Fmal + Ftmal

    M1 = wma(df["Close"], fmal)
    M2 = wma(M1, smal)
    M3 = wma(M2, tmal)
    M4 = wma(M3, Fmal)
    M5 = wma(M4, Ftmal)
    expected = wma(M5, Smal)

    result = calc_mavilimw(df, fmal=fmal, smal=smal)
    pd.testing.assert_series_equal(result, expected)
