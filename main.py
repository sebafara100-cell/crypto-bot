import requests
import pandas as pd
import numpy as np
import time
import schedule
from datetime import datetime

TELEGRAM_TOKEN = "8388675830:AAEGuYms_DGoZWbDefII7cD0aHmMbA-PHaw"
TELEGRAM_CHAT_ID = "605041014"

PERF_7D_LONG  = -8.0
PERF_7D_SHORT =  8.0
RSI_LONG      = 35
RSI_SHORT     = 65
RSI_PERIOD    = 14

TOP_ALTS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "SHIBUSDT", "DOTUSDT",
    "LINKUSDT", "LTCUSDT", "BCHUSDT", "UNIUSDT", "ATOMUSDT",
    "XLMUSDT", "ETCUSDT", "NEARUSDT", "APTUSDT", "FILUSDT",
    "INJUSDT", "AAVEUSDT", "ARBUSDT", "OPUSDT", "MKRUSDT",
    "SUIUSDT", "TIAUSDT", "SEIUSDT", "WLDUSDT", "FETUSDT"
]

def calcular_rsi(precios, periodo=14):
    delta = pd.Series(precios).diff()
    ganancia = delta.clip(lower=0)
    perdida  = -delta.clip(upper=0)
    media_gan = ganancia.ewm(com=periodo - 1, min_periods=periodo).mean()
    media_per = perdida.ewm(com=periodo - 1, min_periods=periodo).mean()
    rs  = media_gan / media_per
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def obtener_datos_binance(simbolo
