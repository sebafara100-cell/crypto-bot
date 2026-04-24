import requests
import pandas as pd
import numpy as np
import time
import schedule
from datetime import datetime

TELEGRAM_TOKEN = "8388675830:AAEGuYms_DGoZWbDefII7cD0aHmMbA-PHaw"
TELEGRAM_CHAT_ID = "605041014"

PERF_7D_LONG = -8.0
PERF_7D_SHORT = 8.0
RSI_LONG = 35
RSI_SHORT = 65
RSI_PERIOD = 14

TOP_ALTS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "SHIBUSDT", "DOTUSDT",
    "LINKUSDT", "LTCUSDT", "BCHUSDT", "UNIUSDT", "ATOMUSDT",
    "XLMUSDT", "ETCUSDT", "NEARUSDT", "APTUSDT", "FILUSDT",
    "INJUSDT", "AAVEUSDT", "OPUUSDT", "HBARUSDT", "ALGOUSDT",
    "VETUSDT" 
]

def calcular_rsi(precios, periodo=14):
    delta = pd.Series(precios).diff()
    ganancia = delta.clip(lower=0)
    perdida = -delta.clip(upper=0)
    media_gan = ganancia.ewm(com=periodo - 1, min_periods=periodo).mean()
    media_per = perdida.ewm(com=periodo - 1, min_periods=periodo).mean()
    rs = media_gan / media_per
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def obtener_datos_binance(simbolo, intervalo="4h", limite=50):
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {"symbol": simbolo, "interval": intervalo, "limit": limite}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        cierres = [float(v[4]) for v in data]
        return cierres
    except Exception as e:
        print("Error obteniendo " + simbolo + ": " + str(e))
        return None

def calcular_rendimiento_7d(simbolo):
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {"symbol": simbolo, "interval": "1d", "limit": 8}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        precio_hace_7d = float(data[0][4])
        precio_actual = float(data[-1][4])
        rendimiento = ((precio_actual - precio_hace_7d) / precio_hace_7d) * 100
        return round(rendimiento, 2)
    except Exception as e:
        print("Error rendimiento 7D " + simbolo + ": " + str(e))
        return None

def enviar_telegram(mensaje):
    url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print("Mensaje enviado a Telegram")
        else:
            print("Error Telegram: " + r.text)
    except Exception as e:
        print("Error Telegram: " + str(e))

def escanear_mercado():
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
    print("Escaneando mercado: " + ahora)
    senales_long = []
    senales_short = []
    for simbolo in TOP_ALTS:
        print("Revisando " + simbolo)
        perf_7d = calcular_rendimiento_7d(simbolo)
        if perf_7d is None:
            continue
        cierres_4h = obtener_datos_binance(simbolo, "4h", 50)
        if cierres_4h is None or len(cierres_4h) < RSI_PERIOD + 2:
            continue
        rsi_actual = calcular_rsi(cierres_4h, RSI_PERIOD)
        rsi_previo = calcular_rsi(cierres_4h[:-1], RSI_PERIOD)
        precio = cierres_4h[-1]
        if perf_7d <= PERF_7D_LONG and rsi_previo < RSI_LONG and rsi_actual > rsi_previo:
            senales_long.append({"simbolo": simbolo, "precio": precio, "perf_7d": perf_7d, "rsi": round(rsi_actual, 1)})
        if perf_7d >= PERF_7D_SHORT and rsi_previo > RSI_SHORT and rsi_actual < rsi_previo:
            senales_short.append({"simbolo": simbolo, "precio": precio, "perf_7d": perf_7d, "rsi": round(rsi_actual, 1)})
        time.sleep(0.3)
    total = len(senales_long) + len(senales_short)
    if total == 0:
        print("Sin senales esta vez")
        return
    mensaje = "📡 <b>CRYPTO SCANNER " + ahora + "</b>\n\n"
    if senales_long:
        mensaje += "🟢 <b>LONG SETUPS (" + str(len(senales_long)) + ")</b>\n"
        for s in senales_long:
            mensaje += "<b>" + s["simbolo"] + "</b> | Precio: " + str(round(s["precio"], 4)) + " | 7D: " + str(s["perf_7d"]) + "% | RSI: " + str(s["rsi"]) + "\n"
    if senales_short:
        mensaje += "\n🔴 <b>SHORT SETUPS (" + str(len(senales_short)) + ")</b>\n"
        for s in senales_short:
            mensaje += "<b>" + s["simbolo"] + "</b> | Precio: " + str(round(s["precio"], 4)) + " | 7D: " + str(s["perf_7d"]) + "% | RSI: " + str(s["rsi"]) + "\n"
    mensaje += "\n<i>Confirma siempre en chart.</i>"
    enviar_telegram(mensaje)

escanear_mercado()
schedule.every(4).hours.do(escanear_mercado)
while True:
    schedule.run_pending()
    time.sleep(60)
