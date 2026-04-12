import os
import time
import requests
from datetime import datetime
from threading import Thread
from flask import Flask
from tradingview_ta import TA_Handler, Interval

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ================= MARKETS =================
MARKETS = [
    ("EURUSD", "forex"),
    ("GBPUSD", "forex"),
    ("USDJPY", "forex"),
    ("BTCUSDT", "crypto"),
    ("ETHUSDT", "crypto"),
    ("XAUUSD", "forex"),
]

COOLDOWN = 70
last_signal = {}

# ================= TELEGRAM =================
def send(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ================= DATA =================
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

# ================= LEVEL 7 SIGNAL ENGINE =================
def signal_engine(symbol, screener):
    a = get_analysis(symbol, screener)
    if not a:
        return None

    s = a.summary
    ind = a.indicators

    buy = s["BUY"]
    sell = s["SELL"]
    rsi = ind.get("RSI", 50)

    # 🎯 direction logic (balanced, not strict)
    if buy > sell:
        direction = "BUY"
        strength = buy / max(buy + sell, 1)
    else:
        direction = "SELL"
        strength = sell / max(buy + sell, 1)

    # ⚡ confidence system
    confidence = 0.50 + (strength * 0.30)

    # RSI boost
    if direction == "BUY" and rsi < 70:
        confidence += 0.05
    if direction == "SELL" and rsi > 30:
        confidence += 0.05

    return direction, min(confidence, 0.92), rsi

# ================= FORMAT (YOUR STYLE) =================
def format_signal(symbol, direction, confidence, rsi):
    now = datetime.now().strftime("%I:%M %p")

    flag = "🇪🇺" if "EUR" in symbol else "🇬🇧" if "GBP" in symbol else "🇯🇵" if "JPY" in symbol else "₿" if "BTC" in symbol else "💰"

    expiry = 2  # 🔥 FIXED 2 MINUTES

    msg = f"""
🤖 AlphaSignalsBot
🚨 SIGNAL ALERT  

📉 {flag} {symbol}
⏰ Expiry: {expiry} minutes
📍 Entry Time: {now}

📈 Direction: {'BUY 🟢' if direction == 'BUY' else 'SELL 🟥'}
💯 Confidence: {round(confidence * 100)}%
📉 RSI: {round(rsi)}

🎯 Martingale Levels:
🔁 Level 1 → +2 min
🔁 Level 2 → +4 min
🔁 Level 3 → +6 min
"""
    return msg

# ================= BOT LOOP =================
def bot():
    print("🚀 2-MINUTE SIGNAL ENGINE ACTIVE")
    send("🚀 AlphaSignalsBot LIVE (2-Min Mode)")

    while True:
        for symbol, market in MARKETS:

            now = time.time()

            # prevent spam
            if symbol in last_signal and now - last_signal[symbol] < COOLDOWN:
                continue

            result = signal_engine(symbol, market)

            if result:
                direction, confidence, rsi = result

                # 🔥 relaxed threshold (prevents silence)
                if confidence >= 0.52:

                    msg = format_signal(symbol, direction, confidence, rsi)
                    send(msg)

                    last_signal[symbol] = now

        time.sleep(15)

# ================= ROUTE =================
@app.route("/")
def home():
    return "AlphaSignalsBot 2-Min Engine Running"

# ================= START =================
Thread(target=bot).start()
