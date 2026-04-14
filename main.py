from flask import Flask, jsonify
from threading import Thread
import time
import pytz
from datetime import datetime, timedelta
import requests
from tradingview_ta import TA_Handler, Interval

app = Flask(__name__)

# ----------------------------
# TELEGRAM CONFIG
# ----------------------------
BOT_TOKEN = "8766011392:AAGhf8-nVXDjnR_BwT0Gba4RLtJAcc46np8"
CHAT_ID = "7068848522"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except:
        print("Telegram error")

# ----------------------------
# GLOBAL STORAGE
# ----------------------------
latest_signal = {"status": "NO SIGNAL"}
last_signal_time = {}

# ----------------------------
# MARKETS
# ----------------------------
MARKETS = [
    ("EURUSD", "forex"),
    ("GBPUSD", "forex"),
    ("USDJPY", "forex"),
    ("BTCUSDT", "crypto"),
    ("ETHUSDT", "crypto"),
    ("XAUUSD", "forex"),
]

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
# FORMAT SIGNAL MESSAGE
# ----------------------------
def format_signal(symbol, direction):
    lagos = pytz.timezone("Africa/Lagos")
    now = datetime.now(lagos)

    entry = now.strftime("%I:%M %p")
    expiry = (now + timedelta(minutes=2)).strftime("%I:%M %p")

    mg1 = (now + timedelta(minutes=2)).strftime("%I:%M %p")
    mg2 = (now + timedelta(minutes=4)).strftime("%I:%M %p")
    mg3 = (now + timedelta(minutes=6)).strftime("%I:%M %p")

    pair_name = symbol.replace("USD", "/USD")

    msg = f"""
🤖 AlphaSignalsBot
🚨 SIGNAL ALERT  

📉 {pair_name}
⏰ Expiry: 2 minutes
📍 Entry Time: {entry}

📈 Direction: {direction} {'🟩' if direction=='BUY' else '🟥'}
💯 Confidence: 80%

🎯 Martingale Levels:
🔁 Level 1 → {mg1}
🔁 Level 2 → {mg2}
🔁 Level 3 → {mg3}
"""
    return msg

# ----------------------------
# SIGNAL LOGIC
# ----------------------------
def generate_signal(symbol, screener):
    analysis = get_analysis(symbol, screener)
    if not analysis:
        return None

    rsi = analysis.indicators.get("RSI")
    rec = analysis.summary.get("RECOMMENDATION")

    print(f"Checking {symbol} | RSI: {rsi} | REC: {rec}")

    if rec == "STRONG_BUY" and rsi < 35:
        direction = "BUY"
    elif rec == "STRONG_SELL" and rsi > 65:
        direction = "SELL"
    else:
        return None

    # cooldown (5 min)
    now_ts = time.time()
    if symbol in last_signal_time:
        if now_ts - last_signal_time[symbol] < 300:
            return None

    last_signal_time[symbol] = now_ts

    return direction

# ----------------------------
# MAIN ENGINE
# ----------------------------
def bot_loop():
    print("🚀 TELEGRAM SIGNAL BOT STARTED")

    while True:
        for symbol, screener in MARKETS:
            direction = generate_signal(symbol, screener)

            if direction:
                message = format_signal(symbol, direction)

                print("🔥 SENDING SIGNAL")
                print(message)

                send_telegram(message)

            time.sleep(3)

        time.sleep(5)

# ----------------------------
# API
# ----------------------------
@app.route("/")
def home():
    return {"status": "TELEGRAM BOT RUNNING 🚀"}

# ----------------------------
# START ENGINE
# ----------------------------
Thread(target=bot_loop, daemon=True).start()

# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
