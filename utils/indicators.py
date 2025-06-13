import pandas as pd
import numpy as np

def calc_mavilimw(df, fmal=3, smal=5):
    """Implementa la lógica anidada de medias de MavilimW."""
    M1 = df['Close'].rolling(window=fmal, min_periods=fmal).mean()
    M2 = M1.rolling(window=smal, min_periods=smal).mean()
    M3 = M2.rolling(window=fmal+smal, min_periods=fmal+smal).mean()
    M4 = M3.rolling(window=fmal+2*smal, min_periods=fmal+2*smal).mean()
    M5 = M4.rolling(window=2*fmal+2*smal, min_periods=2*fmal+2*smal).mean()
    return M5  # Última capa, igual al "MAWW" del Pine Script

def calc_wae(df, sensitivity=150, fastLength=20, slowLength=40, channelLength=20, mult=2.0):
    # MACD de hoy y ayer
    fastMA = df['Close'].ewm(span=fastLength, adjust=False).mean()
    slowMA = df['Close'].ewm(span=slowLength, adjust=False).mean()
    macd = fastMA - slowMA
    macd_shift = macd.shift(1)
    t1 = (macd - macd_shift) * sensitivity
    
    # Bollinger Bands
    basis = df['Close'].rolling(window=channelLength).mean()
    dev = df['Close'].rolling(window=channelLength).std(ddof=0) * mult
    bb_upper = basis + dev
    bb_lower = basis - dev
    e1 = bb_upper - bb_lower
    
    # Dead Zone igual que Pine Script: promedio móvil del true range (TR)
    true_range = np.maximum(df['High'] - df['Low'], np.maximum(
        np.abs(df['High'] - df['Close'].shift(1)),
        np.abs(df['Low'] - df['Close'].shift(1))))
    deadzone = pd.Series(true_range).rolling(window=100).mean().fillna(0) * 3.7
    
    trendUp = np.where(t1 >= 0, t1, 0)
    # trendDown = np.where(t1 < 0, -t1, 0)  # Si alguna vez quieres graficar el histograma bajista
    
    df['wae_trendUp'] = trendUp
    df['wae_e1'] = e1
    df['wae_deadzone'] = deadzone
    return df
