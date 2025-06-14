import pandas as pd
import numpy as np

def wma(series: pd.Series, length: int) -> pd.Series:
    """
    Weighted Moving Average (WMA) implementation matching TradingView's wma().
    """
    # For each window, weights = 1..length
    weights = np.arange(1, length + 1)
    # Sum of weights
    denom = weights.sum()
    # Apply rolling WMA
    return series.rolling(length).apply(lambda x: np.dot(x, weights) / denom, raw=True)

def calc_mavilimw(df: pd.DataFrame, fmal: int = 3, smal: int = 5) -> pd.Series:
    """
    Nested WMA chain replicating the MavilimW indicator from TradingView.
    PineScript uses lengths: fmal, smal, tmal=fmal+smal, Fmal=smal+tmal, Ftmal=tmal+Fmal, Smal=Fmal+Ftmal.
    """
    tmal = fmal + smal                 # third length
    Fmal = smal + tmal                 # fourth length
    Ftmal = tmal + Fmal                # fifth length
    Smal = Fmal + Ftmal                # sixth length for final WMA

    # Sequential weighted moving averages
    M1 = wma(df['Close'], fmal)
    M2 = wma(M1, smal)
    M3 = wma(M2, tmal)
    M4 = wma(M3, Fmal)
    M5 = wma(M4, Ftmal)
    MAVW = wma(M5, Smal)

    return MAVW


def calc_wae(df: pd.DataFrame, sensitivity: float = 150, fastLength: int = 20,
             slowLength: int = 40, channelLength: int = 20, mult: float = 2.0) -> pd.DataFrame:
    # existing implementation unchanged
    fastMA = df['Close'].ewm(span=fastLength, adjust=False).mean()
    slowMA = df['Close'].ewm(span=slowLength, adjust=False).mean()
    macd = fastMA - slowMA
    macd_shift = macd.shift(1)
    t1 = (macd - macd_shift) * sensitivity

    basis = df['Close'].rolling(window=channelLength).mean()
    dev = df['Close'].rolling(window=channelLength).std(ddof=0) * mult
    bb_upper = basis + dev
    bb_lower = basis - dev
    e1 = bb_upper - bb_lower

    true_range = np.maximum(df['High'] - df['Low'],
                             np.maximum(np.abs(df['High'] - df['Close'].shift(1)),
                                        np.abs(df['Low'] - df['Close'].shift(1))))
    deadzone = pd.Series(true_range).rolling(window=100).mean().fillna(0) * 3.7

    df['wae_trendUp'] = np.where(t1 >= 0, t1, 0)
    df['wae_e1'] = e1
    df['wae_deadzone'] = deadzone
    return df
