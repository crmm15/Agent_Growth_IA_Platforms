import os
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import requests
from streamlit import secrets


def generar_y_enviar_resumen_telegram():
    log = "registro_acciones.csv"
    if not os.path.exists(log): return
    df = pd.read_csv(log)
    resumen = df['Acción Tomada'].value_counts()
    rentab  = df.groupby('Acción Tomada')['Rentabilidad %'].mean()
    fig, axs = plt.subplots(1,2,figsize=(10,4))
    resumen.plot.pie(ax=axs[0], autopct='%1.1f%%', ylabel='')
    rentab.plot.bar(ax=axs[1]); axs[1].set_ylabel('Rentabilidad %')
    fname = f"resumen_{datetime.datetime.now():%Y%m%d_%H%M%S}.png"
    fig.savefig(fname); plt.close(fig)
    token, chat = secrets["TELEGRAM_TOKEN"], secrets["TELEGRAM_CHAT_ID"]
    with open(fname,'rb') as img:
        requests.post(f"https://api.telegram.org/bot{token}/sendPhoto",
                      data={"chat_id":chat}, files={"photo":img})
    os.remove(fname)


def enviar_grafico_simulacion_telegram(fig, ticker):
    fname = f"sim_{ticker}_{datetime.datetime.now():%Y%m%d_%H%M%S}.png"
    fig.savefig(fname); plt.close(fig)
    token, chat = secrets["TELEGRAM_TOKEN"], secrets["TELEGRAM_CHAT_ID"]
    with open(fname,'rb') as img:
        requests.post(f"https://api.telegram.org/bot{token}/sendPhoto",
                      data={"chat_id":chat, "caption":f"Simulación {ticker}"}, files={"photo":img})
    os.remove(fname)