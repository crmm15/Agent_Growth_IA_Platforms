import streamlit as st
from utils.backtest_helpers import run_darvas_backtest

def backtest_darvas():
    st.subheader("📦 Backtesting Darvas Box")
    symbol = st.text_input("Ticker", "AAPL")
    if st.button("Ejecutar backtest"):
        df = run_darvas_backtest(symbol)
        st.line_chart(df.set_index('Date')[['Close','mav']])
        st.write(df.tail())