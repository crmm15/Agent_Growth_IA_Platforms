import pandas as pd
import numpy as np

def calc_wae(df, sensitivity=150, fast=20, slow=40, channel=20, mult=2.0):
    fastMA = df['Close'].ewm(span=fast, adjust=False).mean()
    slowMA = df['Close'].ewm(span=slow, adjust=False).mean()
    macd = fastMA - slowMA
    t1 = (macd - macd.shift(1)) * sensitivity
    basis = df['Close'].rolling(channel).mean()
    dev = df['Close'].rolling(channel).std(ddof=0) * mult
    bb_upper = basis + dev
    bb_lower = basis - dev
    e1 = bb_upper - bb_lower
    true_range = np.maximum(
        df['High']-df['Low'],
        np.maximum(abs(df['High']-df['Close'].shift(1)), abs(df['Low']-df['Close'].shift(1)))
    )
    deadzone = true_range.rolling(100).mean().fillna(0) * 3.7
    df['wae_trendUp']   = np.clip(t1, 0, None)
    df['wae_e1']        = e1
    df['wae_deadzone']  = deadzone
    return df


def calc_mavilimw(df, fmal=3, smal=5):
    M1 = df['Close'].rolling(fmal).mean()
    M2 = M1.rolling(smal).mean()
    M3 = M2.rolling(fmal+smal).mean()
    M4 = M3.rolling(fmal+2*smal).mean()
    M5 = M4.rolling(2*fmal+2*smal).mean()
    return M5