from flask import Flask
import time
import threading
import requests
import os
from tradingview_ta import TA_Handler, Interval

app = Flask(__name__)

# ==============================
# SECURE TELEGRAM CONFIG
# ==============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ==============================
# PAIRS LIST
# ==============================
pairs = [
    "EURUSD", "GBPUSD", "USDJPY",
    "AUDUSD", "USDCAD", "EURJPY"
]

# ==============================
# MEMORY (ANTI-SPAM)
# ==============================
last_signal = {}

# ==============================
# TELEGRAM SEND FUNCTION
# ==============================
def send_signal(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Telegram Error:", e)

# ==============================
# ANALYSIS FUNCTION
# ==============================
def analyze_pair(pair):
    try:
        handler = TA_Handler(
            symbol=pair,
            screener="forex",
            exchange="FX_IDC",
            interval=Interval.INTERVAL_1_MINUTE
        )

        analysis = handler.get_analysis()

        rsi = analysis.indicators["RSI"]
        macd = analysis.indicators["MACD.macd"]
        macd_signal = analysis.indicators["MACD.signal"]
        trend = analysis.summary["RECOMMENDATION"]

        # DEBUG (VERY IMPORTANT)
        print(f"Checking {pair} | RSI: {rsi} | MACD: {macd} | Trend: {trend}")

        # ==============================
        # SMART CONDITIONS (BALANCED)
        # ==============================
        if rsi < 35 and macd > macd_signal and trend == "BUY":
            return "BUY"

        elif rsi > 65 and macd < macd_signal and trend == "SELL":
            return "SELL"

    except Exception as e:
        print(f"Error analyzing {pair}: {e}")

    return None

# ==============================
# MAIN BOT LOOP
# ==============================
def run_bot():
    print("🚀 ELITE LIVE SIGNAL ENGINE STARTED")

    while True:
        print("🔄 Scanning markets...")

        for pair in pairs:
            signal = analyze_pair(pair)

            if signal:
                current_time = time.time()

                # ==============================
                # ANTI-SPAM (1 signal per pair / 5 mins)
                # ==============================
                if pair in last_signal:
                    if current_time - last_signal[pair] < 300:
                        continue

                last_signal[pair] = current_time

                # ==============================
                # TELEGRAM MESSAGE FORMAT
                # ==============================
                message = f"""
🔥 ELITE SIGNAL 🔥

Pair: {pair}
Signal: {signal}
Timeframe: M1

Martingale Plan:
1️⃣ Entry
2️⃣ Entry (if loss)
3️⃣ Entry (if loss)

⚠️ Trade wisely
"""

                print(f"✅ SIGNAL: {pair} {signal}")
                send_signal(message)

                # slight delay to avoid flooding
                time.sleep(5)

        # scan every 30 seconds
        time.sleep(30)

# ==============================
# THREAD START
# ==============================
threading.Thread(target=run_bot).start()

# ==============================
# RENDER KEEP-ALIVE ROUTE
# ==============================
@app.route("/")
def home():
    return "🔥 BOT IS LIVE & SCANNING"
