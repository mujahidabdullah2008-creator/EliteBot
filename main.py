from flask import Flask
from threading import Thread
import time
import pytz
from datetime import datetime, timedelta
import requests
import os
from tradingview_ta import TA_Handler, Interval

app = Flask(__name__)

# ----------------------------
# TELEGRAM CONFIG (SAFE)
# ----------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ TELEGRAM NOT CONFIGURED")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}

    try:
        requests.post(url, data=data)
    except:
        print("❌ Telegram error")

# ----------------------------
# MARKETS (MULTI ASSETS)
# ----------------------------
MARKETS = [
    ("EURUSD", "forex"),
    ("GBPUSD", "forex"),
    ("USDJPY", "forex"),
    ("AUDUSD", "forex"),
    ("XAUUSD", "forex"),   # GOLD
    ("BTCUSDT", "crypto"),
    ("ETHUSDT", "crypto"),
]

# ----------------------------
# STORAGE
# ----------------------------
last_signal_time = {}

# ----------------------------
# GET DATA
# ----------------------------
def get_analysis(symbol, screener):
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener=screener,
            exchange="FX_IDC" if screener == "forex" else "BINANCE",
            interval=Interval.INTERVAL_1_MINUTE
        )
        return handler.get_analysis()
    except:
        return None

# ----------------------------
# FORMAT SIGNAL
# ----------------------------
def format_signal(symbol, direction):
    lagos = pytz.timezone("Africa/Lagos")
    now = datetime.now(lagos)

    entry = now.strftime("%I:%M %p")
    expiry = (now + timedelta(minutes=2)).strftime("%I:%M %p")

    mg1 = (now + timedelta(minutes=2)).strftime("%I:%M %p")
    mg2 = (now + timedelta(minutes=4)).strftime("%I:%M %p")
    mg3 = (now + timedelta(minutes=6)).strftime("%I:%M %p")

    pair = symbol.replace("USDT", "/USDT").replace("USD", "/USD")

    return f"""
🤖 AlphaSignalsBot
🚨 SIGNAL ALERT  

📊 {pair}
⏰ Expiry: 2 minutes
📍 Entry Time: {entry}

📈 Direction: {direction} {'🟩' if direction=='BUY' else '🟥'}
💯 Confidence: 75%

🎯 Martingale Levels:
🔁 Level 1 → {mg1}
🔁 Level 2 → {mg2}
🔁 Level 3 → {mg3}
"""

# ----------------------------
# SIGNAL LOGIC (BALANCED)
# ----------------------------
def generate_signal(symbol, screener):
    analysis = get_analysis(symbol, screener)
    if not analysis:
        return None

    rsi = analysis.indicators.get("RSI")
    macd = analysis.indicators.get("MACD.macd")
    rec = analysis.summary.get("RECOMMENDATION")

    print(f"Checking {symbol} | RSI: {rsi} | MACD: {macd} | REC: {rec}")

    if rsi is None or macd is None:
        return None

    # ✅ Balanced conditions (more signals, still smart)
    if rec in ["BUY", "STRONG_BUY"] and rsi < 45 and macd > -0.001:
        direction = "BUY"

    elif rec in ["SELL", "STRONG_SELL"] and rsi > 55 and macd < 0.001:
        direction = "SELL"

    else:
        return None

    # ⛔ Cooldown (avoid spam)
    now_ts = time.time()
    if symbol in last_signal_time:
        if now_ts - last_signal_time[symbol] < 180:  # 3 minutes
            return None

    last_signal_time[symbol] = now_ts
    return direction

# ----------------------------
# BOT ENGINE
# ----------------------------
def bot_loop():
    print("🚀 LIVE SIGNAL ENGINE RUNNING")

    while True:
        print("🔄 Scanning markets...")

        for symbol, screener in MARKETS:
            direction = generate_signal(symbol, screener)

            if direction:
                msg = format_signal(symbol, direction)

                print("🔥 SIGNAL FOUND")
                print(msg)

                send_telegram(msg)

            time.sleep(2)

        time.sleep(5)

# ----------------------------
# ROUTE
# ----------------------------
@app.route("/")
def home():
    return {"status": "LIVE BOT RUNNING 🚀"}

# ----------------------------
# START
# ----------------------------
Thread(target=bot_loop, daemon=True).start()

# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
