import os
import time
import requests
from datetime import datetime, timedelta
import pytz
from flask import Flask
from tradingview_ta import TA_Handler, Interval

app = Flask(__name__)

# ==============================
# ENV VARIABLES (IMPORTANT)
# ==============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ==============================
# SETTINGS
# ==============================
pairs = [
    ("EURUSD", "forex"),
    ("GBPUSD", "forex"),
    ("USDJPY", "forex"),
    ("XAUUSD", "forex"),
    ("BTCUSDT", "crypto"),
    ("ETHUSDT", "crypto"),
]

COOLDOWN = 300  # 5 mins

last_signal_time = {}
last_signal_direction = {}

# ==============================
# TIME (NIGERIA)
# ==============================
def get_time():
    tz = pytz.timezone("Africa/Lagos")
    return datetime.now(tz)

# ==============================
# CONFIDENCE
# ==============================
def calculate_confidence(rsi, macd, price, ema50):
    score = 0

    if rsi < 30 or rsi > 70:
        score += 30

    if macd > 0:
        score += 20

    if price > ema50:
        score += 20

    return min(score, 95)

# ==============================
# SIGNAL LOGIC (STRONG ONLY)
# ==============================
def get_signal(pair, screener):
    handler = TA_Handler(
        symbol=pair,
        screener=screener,
        exchange="BINANCE" if screener == "crypto" else "FX_IDC",
        interval=Interval.INTERVAL_1_MINUTE
    )

    analysis = handler.get_analysis()

    rsi = analysis.indicators["RSI"]
    macd = analysis.indicators["MACD.macd"]
    ema50 = analysis.indicators["EMA50"]
    price = analysis.indicators["close"]

    # STRONG BUY
    if rsi < 25 and macd > 0 and price > ema50:
        return "BUY", rsi, macd, ema50, price

    # STRONG SELL
    elif rsi > 75 and macd < 0 and price < ema50:
        return "SELL", rsi, macd, ema50, price

    return None, rsi, macd, ema50, price

# ==============================
# COOLDOWN + FILTER
# ==============================
def can_send(pair, direction):
    now = time.time()

    if pair not in last_signal_time:
        last_signal_time[pair] = 0
        last_signal_direction[pair] = None

    if now - last_signal_time[pair] < COOLDOWN:
        return False

    if last_signal_direction[pair] == direction:
        return False

    last_signal_time[pair] = now
    last_signal_direction[pair] = direction
    return True

# ==============================
# MARTINGALE TIME
# ==============================
def martingale_times():
    now = get_time()

    t1 = now + timedelta(minutes=2)
    t2 = now + timedelta(minutes=4)
    t3 = now + timedelta(minutes=6)

    return (
        t1.strftime("%I:%M %p"),
        t2.strftime("%I:%M %p"),
        t3.strftime("%I:%M %p"),
    )

# ==============================
# SEND TELEGRAM
# ==============================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message
    })

# ==============================
# FORMAT MESSAGE
# ==============================
def format_signal(pair, direction, confidence):
    now = get_time().strftime("%I:%M %p")
    t1, t2, t3 = martingale_times()

    emoji = "🟩" if direction == "BUY" else "🟥"
    flag = "🇪🇺 EUR/USD 🇺🇸" if pair == "EURUSD" else pair

    return f"""🤖 AlphaSignalsBot
🚨 SIGNAL ALERT  

📉 {flag} (OTC)
⏰ Expiry: 2 minutes
📍 Entry Time: {now}

📈 Direction: {direction} {emoji}
💯 Confidence: {confidence}%

🎯 Martingale Levels:
🔁 Level 1 → {t1}
🔁 Level 2 → {t2}
🔁 Level 3 → {t3}
"""

# ==============================
# MAIN LOOP (AUTO BOT)
# ==============================
def run_bot():
    print("🚀 FULL AUTO BOT RUNNING")

    while True:
        for pair, screener in pairs:
            try:
                signal, rsi, macd, ema50, price = get_signal(pair, screener)

                if signal:
                    confidence = calculate_confidence(rsi, macd, price, ema50)

                    if confidence >= 60 and can_send(pair, signal):
                        msg = format_signal(pair, signal, confidence)
                        send_telegram(msg)
                        print(f"✅ Sent: {pair} {signal}")

            except Exception as e:
                print("Error:", e)

        time.sleep(60)

# ==============================
# FLASK (KEEP ALIVE)
# ==============================
@app.route("/")
def home():
    return {"status": "AlphaSignalsBot Running 🤖"}

# ==============================
# START BOT
# ==============================
import threading

threading.Thread(target=run_bot).start()
