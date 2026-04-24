import requests
import pandas as pd
import time
import schedule
from datetime import datetime

TELEGRAM_TOKEN = "8388675830:AAEGuYms_DGoZWbDefII7cD0aHmMbA-PHaw"
TELEGRAM_CHAT_ID = "605041014"

PERF_7D_LONG = -8.0
PERF_7D_SHORT = 8.0
RSI_LONG = 40
RSI_SHORT = 60
RSI_PERIOD = 14

TOP_IDS = [
    "bitcoin","ethereum","binance-coin","solana","xrp",
    "dogecoin","cardano","avalanche","polkadot","chainlink",
    "litecoin","uniswap","cosmos","stellar","near"
]

def calcular_rsi(precios, periodo=14):
    delta = pd.Series(precios).diff()
    ganancia = delta.clip(lower=0)
    perdida = -delta.clip(upper=0)
    media_gan = ganancia.ewm(com=periodo-1, min_periods=periodo).mean()
    media_per = perdida.ewm(com=periodo-1, min_periods=periodo).mean()
    rs = media_gan / media_per
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def obtener_datos_moneda(coin_id):
    url = "https://api.coincap.io/v2/assets/" + coin_id + "/history"
    params = {"interval": "h1", "start": int((time.time()-14*86400)*1000), "end": int(time.time()*1000)}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()["data"]
        precios = [float(p["priceUsd"]) for p in data]
        return precios
    except Exception as e:
        print("Error " + coin_id + ": " + str(e))
        return None

def calcular_rendimiento_7d(precios):
    if len(precios) < 170:
        return None
    return round(((precios[-1] - precios[-168]) / precios[-168]) * 100, 2)

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
    print("Escaneando: " + ahora)
    senales_long = []
    senales_short = []
    for coin_id in TOP_IDS:
        print("Revisando " + coin_id)
        precios = obtener_datos_moneda(coin_id)
        if precios is None or len(precios) < RSI_PERIOD + 2:
            continue
        perf_7d = calcular_rendimiento_7d(precios)
        if perf_7d is None:
            continue
        rsi_actual = calcular_rsi(precios, RSI_PERIOD)
        rsi_previo = calcular_rsi(precios[:-1], RSI_PERIOD)
        precio = precios[-1]
        print(coin_id + " 7D:" + str(perf_7d) + "% RSI:" + str(round(rsi_actual,1)))
        if perf_7d <= PERF_7D_LONG and rsi_previo < RSI_LONG and rsi_actual > rsi_previo:
            senales_long.append({"simbolo": coin_id.upper(), "precio": precio, "perf_7d": perf_7d, "rsi": round(rsi_actual,1)})
        if perf_7d >= PERF_7D_SHORT and rsi_previo > RSI_SHORT and rsi_actual < rsi_previo:
            senales_short.append({"simbolo": coin_id.upper(), "precio": precio, "perf_7d": perf_7d, "rsi": round(rsi_actual,1)})
        time.sleep(2)

    if len(senales_long) + len(senales_short) == 0:
        print("Sin senales esta vez")
        return

    mensaje = "📡 <b>CRYPTO SCANNER " + ahora + "</b>\n\n"
    if senales_long:
        mensaje += "🟢 <b>LONG (" + str(len(senales_long)) + ")</b>\n"
        for s in senales_long:
            mensaje += "<b>" + s["simbolo"] + "</b> $" + str(round(s["precio"],4)) + " | 7D:" + str(s["perf_7d"]) + "% RSI:" + str(s["rsi"]) + "\n"
    if senales_short:
        mensaje += "\n🔴 <b>SHORT (" + str(len(senales_short)) + ")</b>\n"
        for s in senales_short:
            mensaje += "<b>" + s["simbolo"] + "</b> $" + str(round(s["precio"],4)) + " | 7D:" + str(s["perf_7d"]) + "% RSI:" + str(s["rsi"]) + "\n"
    mensaje += "\n<i>Confirma siempre en chart.</i>"
    enviar_telegram(mensaje)

escanear_mercado()
schedule.every(4).hours.do(escanear_mercado)
while True:
    schedule.run_pending()
    time.sleep(60)
