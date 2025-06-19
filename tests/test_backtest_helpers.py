import pandas as pd
from pandas.testing import assert_series_equal
from utils.backtest_helpers import robust_trend_filter


def test_robust_trend_filter_initial_trend():
    df = pd.DataFrame({
        'Close': [1, 2, 3, 4, 5],
        'mavilimw': [None, None, 2, 3, 4],
    })
    expected = pd.Series([False, False, True, True, True])
    result = robust_trend_filter(df)
    assert_series_equal(result, expected)
