import os
import time
import requests
from flask import Flask
from threading import Thread
from datetime import datetime
from tradingview_ta import TA_Handler, Interval

app = Flask(__name__)

# ================= ENV =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("❌ Missing BOT_TOKEN or CHAT_ID")

# ================= MARKETS =================
MARKETS = [
    ("EURUSD", "forex", "🇪🇺 🇺🇸 EUR/USD"),
    ("GBPUSD", "forex", "🇬🇧 🇺🇸 GBP/USD"),
    ("USDJPY", "forex", "🇺🇸 🇯🇵 USD/JPY"),
    ("BTCUSDT", "crypto", "₿ BTC/USDT"),
    ("ETHUSDT", "crypto", "Ξ ETH/USDT"),
    ("XAUUSD", "forex", "🥇 GOLD (XAU/USD)")
]

COOLDOWN = 180  # faster signals but controlled
last_signal_time = {}

# ================= TELEGRAM =================
def send_signal(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
        print("📩 SENT SIGNAL")
    except Exception as e:
        print("Telegram error:", e)

# ================= ANALYSIS =================
def get_analysis(symbol, exchange):
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener="forex" if exchange == "forex" else "crypto",
            exchange="FX_IDC" if exchange == "forex" else "BINANCE",
            interval=Interval.INTERVAL_1_MINUTE
        )
        return handler.get_analysis()
    except Exception as e:
        print("Analysis error:", symbol, e)
        return None

# ================= SCORE ENGINE =================
def score_signal(symbol, exchange):
    a1 = get_analysis(symbol, exchange)
    if not a1:
        return None

    s = a1.summary
    ind = a1.indicators

    rsi = ind.get("RSI", 50)

    buy = s.get("BUY", 0)
    sell = s.get("SELL", 0)
    neutral = s.get("NEUTRAL", 0)

    total = buy + sell + neutral
    if total == 0:
        return None

    confidence = max(buy, sell) / total

    # 🔥 STRONG FILTER (IMPORTANT)
    if confidence < 0.60:
        return None

    # TREND DECISION
    if buy > sell and rsi < 70:
        return "BUY", confidence, rsi

    if sell > buy and rsi > 30:
        return "SELL", confidence, rsi

    return None

# ================= FORMAT (YOUR STYLE) =================
def format_signal(name, direction, confidence, rsi):
    now = datetime.now().strftime("%I:%M %p")

    expiry1 = (datetime.now()).strftime("%I:%M %p")
    expiry2 = (datetime.now()).strftime("%I:%M %p")
    expiry3 = (datetime.now()).strftime("%I:%M %p")

    return f"""
🤖 AlphaSignalsBot
🚨 SIGNAL ALERT  

📉 {name}
⏰ Expiry: 2 minutes
📍 Entry Time: {now}

📈 Direction: {direction} {"🟢" if direction=="BUY" else "🟥"}
💯 Confidence: {int(confidence*100)}%
📉 RSI: {round(rsi)}

🎯 Martingale Levels:
🔁 Level 1 → {expiry1}
🔁 Level 2 → {expiry2}
🔁 Level 3 → {expiry3}
"""

# ================= BOT LOOP =================
def bot_loop():
    print("🚀 LEVEL 3 GOD MODE ACTIVE")
    send_signal("🤖 AlphaSignalsBot LIVE 🚀")

    while True:
        for symbol, market, name in MARKETS:
            now = time.time()

            if symbol in last_signal_time and now - last_signal_time[symbol] < COOLDOWN:
                continue

            result = score_signal(symbol, market)

            if result:
                direction, confidence, rsi = result

                msg = format_signal(name, direction, confidence, rsi)
                send_signal(msg)

                last_signal_time[symbol] = now

        time.sleep(20)

# ================= ROUTE =================
@app.route("/")
def home():
    return "🤖 AlphaSignalsBot Running"

# ================= START =================
Thread(target=bot_loop).start()
