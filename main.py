import os
import time
import requests
from flask import Flask
from threading import Thread
from tradingview_ta import TA_Handler, Interval

app = Flask(__name__)

# ================= ENV =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ================= MARKETS =================
MARKETS = [
    ("EURUSD", "forex", "🇪🇺"),
    ("GBPUSD", "forex", "🇬🇧"),
    ("USDJPY", "forex", "🇯🇵"),
    ("BTCUSDT", "crypto", "₿"),
    ("ETHUSDT", "crypto", "Ξ"),
    ("XAUUSD", "forex", "🥇"),
]

last_signal_time = {}
COOLDOWN = 120  # faster signals (2 min)

# ================= TELEGRAM =================
def send_signal(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

# ================= ANALYSIS =================
def get_analysis(symbol, market):
    try:
        return TA_Handler(
            symbol=symbol,
            screener="crypto" if market == "crypto" else "forex",
            exchange="BINANCE" if market == "crypto" else "FX_IDC",
            interval=Interval.INTERVAL_1_MINUTE
        ).get_analysis()
    except:
        return None

# ================= SCORE ENGINE =================
def score(symbol, market):
    a = get_analysis(symbol, market)
    if not a:
        return None

    s = a.summary
    rsi = a.indicators.get("RSI", 50)

    buy = s["BUY"]
    sell = s["SELL"]

    # SIMPLE SMART LOGIC (FAST SIGNALS)
    if buy > sell and rsi < 70:
        return "BUY", min(0.55 + (buy - sell) * 0.02, 0.80), rsi

    if sell > buy and rsi > 30:
        return "SELL", min(0.55 + (sell - buy) * 0.02, 0.80), rsi

    return None

# ================= FORMAT (YOUR STYLE) =================
def format_signal(symbol, direction, confidence, rsi, flag):
    emoji = "📈" if direction == "BUY" else "📉"

    return f"""
🤖 AlphaSignalsBot
🚨 SIGNAL ALERT  

{emoji} {flag} {symbol}
⏰ Expiry: 2 minutes
📍 Entry Time: {time.strftime('%I:%M %p')}

📈 Direction: {direction} {"🟩" if direction=="BUY" else "🟥"}
💯 Confidence: {int(confidence*100)}%
📉 RSI: {round(rsi)}

🎯 Martingale Levels:
🔁 Level 1 → {time.strftime('%I:%M %p', time.localtime(time.time()+120))}
🔁 Level 2 → {time.strftime('%I:%M %p', time.localtime(time.time()+240))}
🔁 Level 3 → {time.strftime('%I:%M %p', time.localtime(time.time()+360))}
"""

# ================= BOT LOOP =================
def bot():
    print("🚀 LEVEL 5 GOD MODE ACTIVE")
    send_signal("🚀 LEVEL 5 BOT LIVE")

    while True:
        for symbol, market, flag in MARKETS:

            now = time.time()
            if symbol in last_signal_time and now - last_signal_time[symbol] < COOLDOWN:
                continue

            result = score(symbol, market)

            if result:
                direction, confidence, rsi = result

                if confidence >= 0.58:   # balanced filter (not too strict)
                    msg = format_signal(symbol, direction, confidence, rsi, flag)
                    send_signal(msg)
                    last_signal_time[symbol] = now

        time.sleep(15)

# ================= ROUTE =================
@app.route("/")
def home():
    return "BOT RUNNING"

# ================= START =================
Thread(target=bot).start()
