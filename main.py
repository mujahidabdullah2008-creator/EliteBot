import os
import time
import requests
from datetime import datetime
from threading import Thread
from flask import Flask
from tradingview_ta import TA_Handler, Interval

app = Flask(__name__)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

MARKETS = [
    ("EURUSD", "forex"),
    ("GBPUSD", "forex"),
    ("USDJPY", "forex"),
    ("BTCUSDT", "crypto"),
    ("ETHUSDT", "crypto"),
    ("XAUUSD", "forex"),
]

COOLDOWN = 90
last_signal_time = {}

# ================= TELEGRAM =================
def send_signal(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print("Telegram error:", e)

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

# ================= LEVEL 6 ENGINE =================
def score(symbol, screener):
    a = get_analysis(symbol, screener)
    if not a:
        return None

    s = a.indicators
    summary = a.summary

    rsi = s.get("RSI", 50)
    macd = s.get("MACD.macd", 0)
    signal = s.get("MACD.signal", 0)

    buy = summary["BUY"]
    sell = summary["SELL"]

    trend = "BUY" if buy > sell else "SELL"

    macd_bull = macd > signal

    # ================= STRONG BUY =================
    if trend == "BUY" and rsi < 70 and macd_bull:
        confidence = 0.65 + min((buy - sell) * 0.02, 0.25)
        return "BUY", confidence, rsi

    # ================= STRONG SELL =================
    if trend == "SELL" and rsi > 30 and not macd_bull:
        confidence = 0.65 + min((sell - buy) * 0.02, 0.25)
        return "SELL", confidence, rsi

    # ================= FALLBACK MODE =================
    if buy > sell:
        return "BUY", 0.55, rsi
    if sell > buy:
        return "SELL", 0.55, rsi

    return None

# ================= FORMAT (YOUR REQUEST STYLE) =================
def format_signal(symbol, direction, confidence, rsi):
    now = datetime.now().strftime("%I:%M %p")

    flag = "🇪🇺" if "EUR" in symbol else "🇬🇧" if "GBP" in symbol else "🇯🇵" if "JPY" in symbol else "₿" if "BTC" in symbol else "💰"

    martingale = [
        (2, 2),
        (2, 4),
        (2, 6)
    ]

    msg = f"""
🤖 AlphaSignalsBot
🚨 SIGNAL ALERT  

📉 {flag} {symbol}
⏰ Expiry: 2 minutes
📍 Entry Time: {now}

📈 Direction: {'BUY 🟢' if direction == 'BUY' else 'SELL 🟥'}
💯 Confidence: {round(confidence * 100)}%
📉 RSI: {round(rsi)}

🎯 Martingale Levels:
🔁 Level 1 → +{martingale[0][1]} min
🔁 Level 2 → +{martingale[1][1]} min
🔁 Level 3 → +{martingale[2][1]} min
"""
    return msg

# ================= BOT LOOP =================
def bot():
    print("🚀 LEVEL 6 ENGINE ACTIVE")
    send_signal("🚀 AlphaSignalsBot LEVEL 6 LIVE")

    while True:
        for symbol, market in MARKETS:
            now = time.time()

            if symbol in last_signal_time:
                if now - last_signal_time[symbol] < COOLDOWN:
                    continue

            result = score(symbol, market)

            if result:
                direction, confidence, rsi = result

                if confidence >= 0.55:  # relaxed but controlled
                    msg = format_signal(symbol, direction, confidence, rsi)
                    send_signal(msg)
                    last_signal_time[symbol] = now

        time.sleep(20)

# ================= ROUTE =================
@app.route("/")
def home():
    return "LEVEL 6 ENGINE RUNNING"

# ================= START =================
Thread(target=bot).start()
