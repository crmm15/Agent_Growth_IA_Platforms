import requests
import os
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import logging
from streamlit import secrets
from config import ARCHIVO_LOG

logger = logging.getLogger(__name__)

def send_telegram_message(text: str):
    token = secrets.get("TELEGRAM_TOKEN")
    chat = secrets.get("TELEGRAM_CHAT_ID")
    if token is None or chat is None:
        logger.warning("Telegram secrets missing; message not sent")
        return
    requests.post(
         f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat, "text": text, "parse_mode": "Markdown"},
    )

def generar_y_enviar_resumen_telegram():
    log = ARCHIVO_LOG
    if not os.path.exists(log): return
    df = pd.read_csv(log)
    resumen = df['Acción Tomada'].value_counts()
    rentab  = df.groupby('Acción Tomada')['Rentabilidad %'].mean()
    fig, axs = plt.subplots(1,2,figsize=(10,4))
    resumen.plot.pie(ax=axs[0], autopct='%1.1f%%', ylabel='')
    rentab.plot.bar(ax=axs[1]); axs[1].set_ylabel('Rentabilidad %')
    fname = f"resumen_{datetime.datetime.now():%Y%m%d_%H%M%S}.png"
    fig.savefig(fname)
    plt.close(fig)
    token = secrets.get("TELEGRAM_TOKEN")
    chat = secrets.get("TELEGRAM_CHAT_ID")
    if token is None or chat is None:
        logger.warning("Telegram secrets missing; summary not sent")
        os.remove(fname)
        return
    with open(fname, "rb") as img:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendPhoto",
            data={"chat_id": chat},
            files={"photo": img},
        )
    os.remove(fname)


def enviar_grafico_simulacion_telegram(fig, ticker):
    fname = f"sim_{ticker}_{datetime.datetime.now():%Y%m%d_%H%M%S}.png"
    fig.savefig(fname)
    plt.close(fig)
    token = secrets.get("TELEGRAM_TOKEN")
    chat = secrets.get("TELEGRAM_CHAT_ID")
    if token is None or chat is None:
        logger.warning("Telegram secrets missing; simulation graph not sent")
        os.remove(fname)
        return
    with open(fname, "rb") as img:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendPhoto",
            data={"chat_id": chat, "caption": f"Simulación {ticker}"},
            files={"photo": img},
        )
    os.remove(fname)
