import pandas as pd
from yfinance import Ticker
from utils.indicators import calc_mavilimw, calc_wae


def run_darvas_backtest(symbol, period='6mo'):
    df = Ticker(symbol).history(period=period)
    df['mav'] = calc_mavilimw(df)
    df = calc_wae(df)
    df['prev_close'] = df['Close'].shift(1)
    df['prev_mav']   = df['mav'].shift(1)
    df['darvas_high'] = df['High'].rolling(20).max()
    df['darvas_low']  = df['Low'].rolling(20).min()
    df['buy_signal'] = (df['Close']>df['darvas_high'].shift(1))&(df['prev_close']<=df['darvas_high'].shift(1))
    df['sell_signal'] = (df['Close']<df['darvas_low'].shift(1))&(df['prev_close']>=df['darvas_low'].shift(1))
    return df