import os
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID


def send_telegram_message(text: str):
    """Envía mensaje de texto a Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    })


def send_telegram_chart(df: pd.DataFrame, chart_type: str = "decisions"):
    """Genera y envía gráfico (pie o barra) según tipo."""
    fig, ax = plt.subplots(figsize=(6, 4))
    if chart_type == "decisions":
        df["Acción Tomada"].value_counts().plot.pie(
            ax=ax, autopct="%1.1f%%", ylabel=""
        )
    else:
        df.groupby("Acción Tomada")["Rentabilidad %"].mean().plot.bar(
            ax=ax, rot=45
        )
        ax.set_ylabel("Rentabilidad %")
    fname = f"chart_{chart_type}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    fig.tight_layout(); fig.savefig(fname); plt.close(fig)
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
        data={"chat_id": TELEGRAM_CHAT_ID},
        files={"photo": open(fname, "rb")}
    )
    os.remove(fname)