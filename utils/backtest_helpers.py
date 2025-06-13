import pandas as pd
from yfinance import Ticker
from utils.indicators import calc_mavilimw, calc_wae

def robust_trend_filter(df):
    trend = pd.Series(False, index=df.index)
    # Cuando hay valor en mavilimw, tendencia alcista si close > mavilimw (igual que antes)
    trend[df['mavilimw'].notna()] = (
        df.loc[df['mavilimw'].notna(), 'Close'] >
        df.loc[df['mavilimw'].notna(), 'mavilimw']
    )
    # Para primeras señales: si las últimas 3 velas (incluida la actual)
    # están por arriba de la primera mavilimw válida
    first_valid = df['mavilimw'].first_valid_index()
    if first_valid is not None and first_valid >= 2:
        for i in range(first_valid - 2, first_valid + 1):
            if (
                i >= 0 and
                all(
                    df.loc[j, 'Close'] > df.loc[first_valid, 'mavilimw']
                    for j in range(i, first_valid + 1)
                )
            ):
                trend.iloc[i] = True

    return trend
