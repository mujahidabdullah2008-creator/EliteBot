import os
import time
import requests
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta
import pytz
from tradingview_ta import TA_Handler, Interval

app = Flask(__name__)

# ================= ENV =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ================= MARKETS =================
MARKETS = [
    ("EURUSD", "forex", "🇪🇺 🇺🇸 EUR/USD"),
    ("GBPUSD", "forex", "🇬🇧 🇺🇸 GBP/USD"),
    ("USDJPY", "forex", "🇺🇸 🇯🇵 USD/JPY"),
    ("BTCUSDT", "crypto", "₿ BTC/USDT"),
    ("ETHUSDT", "crypto", "Ξ ETH/USDT"),
    ("XAUUSD", "forex", "🥇 GOLD (XAU/USD)")
]

# ================= STATE MEMORY =================
last_signal_time = {}
last_trend = {}  # 🔥 LEVEL 4 CORE (trend cycle memory)

COOLDOWN = 180  # faster but controlled

# ================= TIME =================
def now_ng():
    return datetime.now(pytz.timezone("Africa/Lagos"))

# ================= TELEGRAM =================
def send_signal(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print("📩 SENT")
    except Exception as e:
        print("Telegram error:", e)

# ================= ANALYSIS =================
def get_analysis(symbol, exchange_type):
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener="forex" if exchange_type == "forex" else "crypto",
            exchange="FX_IDC" if exchange_type == "forex" else "BINANCE",
            interval=Interval.INTERVAL_1_MINUTE
        )
        return handler.get_analysis()
    except Exception as e:
        print("Analysis error:", symbol, e)
        return None

# ================= SCORE ENGINE (LEVEL 4 FILTER) =================
def evaluate(symbol, market_type):
    a = get_analysis(symbol, market_type)
    if not a:
        return None

    s = a.summary
    ind = a.indicators

    rsi = ind.get("RSI", 50)

    buy = s.get("BUY", 0)
    sell = s.get("SELL", 0)
    neutral = s.get("NEUTRAL", 0)

    total = buy + sell + neutral
    if total == 0:
        return None

    confidence = max(buy, sell) / total

    # ❌ weak signal filter
    if confidence < 0.62:
        return None

    # direction logic
    if buy > sell and rsi < 70:
        return "BUY", confidence, rsi

    if sell > buy and rsi > 30:
        return "SELL", confidence, rsi

    return None

# ================= FORMAT (YOUR EXACT STYLE) =================
def format_signal(name, direction, confidence, rsi):
    now = now_ng()

    entry = now.strftime("%I:%M %p")

    m1 = (now + timedelta(minutes=2)).strftime("%I:%M %p")
    m2 = (now + timedelta(minutes=4)).strftime("%I:%M %p")
    m3 = (now + timedelta(minutes=6)).strftime("%I:%M %p")

    return f"""
🤖 AlphaSignalsBot
🚨 SIGNAL ALERT  

📉 {name}
⏰ Expiry: 2 minutes
📍 Entry Time: {entry}

📈 Direction: {direction} {"🟢" if direction=="BUY" else "🟥"}
💯 Confidence: {int(confidence*100)}%
📉 RSI: {round(rsi)}

🎯 Martingale Levels:
🔁 Level 1 → {m1}
🔁 Level 2 → {m2}
🔁 Level 3 → {m3}
"""

# ================= BOT LOOP (LEVEL 4 CORE) =================
def bot():
    print("🚀 LEVEL 4 GOD SYSTEM ACTIVE")
    send_signal("🤖 AlphaSignalsBot LEVEL 4 LIVE 🚀")

    while True:
        for symbol, market, name in MARKETS:
            now = time.time()

            # cooldown per asset
            if symbol in last_signal_time and now - last_signal_time[symbol] < COOLDOWN:
                continue

            result = evaluate(symbol, market)

            if result:
                direction, confidence, rsi = result

                # 🔥 LEVEL 4 CORE: TREND CYCLE FILTER
                if symbol in last_trend:
                    if last_trend[symbol] == direction:
                        continue  # ❌ ignore same trend signal

                # update trend memory
                last_trend[symbol] = direction
                last_signal_time[symbol] = now

                msg = format_signal(name, direction, confidence, rsi)
                send_signal(msg)

        time.sleep(15)

# ================= FLASK =================
@app.route("/")
def home():
    return "🤖 LEVEL 4 GOD SYSTEM ACTIVE"

# ================= START =================
Thread(target=bot).start()
