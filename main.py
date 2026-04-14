from flask import Flask
import time
import threading
import requests
import os
from tradingview_ta import TA_Handler, Interval

app = Flask(__name__)

# ==============================
# TELEGRAM CONFIG
# ==============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ==============================
# PAIRS
# ==============================
pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "EURJPY"]

# ==============================
# ANTI-SPAM MEMORY
# ==============================
last_signal = {}

# ==============================
# TELEGRAM FUNCTION
# ==============================
def send_signal(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
        print("📩 Sent to Telegram", flush=True)
    except Exception as e:
        print("Telegram Error:", e, flush=True)

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

        print(f"Checking {pair} | RSI: {rsi} | MACD: {macd} | Trend: {trend}", flush=True)

        # SIGNAL CONDITIONS (BALANCED)
        if rsi < 35 and macd > macd_signal and trend == "BUY":
            return "BUY"

        elif rsi > 65 and macd < macd_signal and trend == "SELL":
            return "SELL"

    except Exception as e:
        print(f"ERROR {pair}: {e}", flush=True)

    return None

# ==============================
# LIVE ENGINE LOOP
# ==============================
def run_bot():
    print("🚀 ELITE LIVE ENGINE STARTED", flush=True)

    while True:
        try:
            print("🔄 Scanning markets...", flush=True)

            for pair in pairs:
                print(f"➡️ Scanning {pair}", flush=True)

                signal = analyze_pair(pair)

                if signal:
                    now = time.time()

                    if pair in last_signal and now - last_signal[pair] < 300:
                        continue

                    last_signal[pair] = now

                    message = f"""
🔥 ELITE SIGNAL 🔥

Pair: {pair}
Signal: {signal}
Timeframe: M1

Martingale:
1️⃣ Entry
2️⃣ Entry (if loss)
3️⃣ Entry (if loss)

⚠️ Trade wisely
"""

                    print(f"✅ SIGNAL FOUND: {pair} {signal}", flush=True)
                    send_signal(message)

                    time.sleep(5)

            time.sleep(30)

        except Exception as e:
            print("🔥 LOOP CRASH:", e, flush=True)
            time.sleep(5)

# ==============================
# START ENGINE SAFELY
# ==============================
def start_engine():
    thread = threading.Thread(target=run_bot)
    thread.daemon = True
    thread.start()

start_engine()

# ==============================
# KEEP ALIVE ROUTE
# ==============================
@app.route("/")
def home():
    return "🔥 BOT RUNNING LIVE"
