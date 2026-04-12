import os
import time
import requests
from flask import Flask
from threading import Thread
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
    ("XAUUSD", "forex")  # GOLD
]

COOLDOWN = 300
last_signal_time = {}

# ================= TELEGRAM =================
def send_signal(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
        print("📩 Sent:", message)
    except Exception as e:
        print("❌ Send error:", e)

# ================= ANALYSIS =================
def get_analysis(symbol, screener, interval):
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener=screener,
            exchange="BINANCE" if screener == "crypto" else "FX_IDC",
            interval=interval
        )
        return handler.get_analysis()
    except Exception as e:
        print(f"❌ {symbol} error:", e)
        return None

# ================= SMART STRATEGY =================
def elite_signal(symbol, screener):
    a1 = get_analysis(symbol, screener, Interval.INTERVAL_1_MINUTE)
    a5 = get_analysis(symbol, screener, Interval.INTERVAL_5_MINUTES)

    if not a1 or not a5:
        return None

    s1 = a1.summary
    s5 = a5.summary
    rsi = a1.indicators.get("RSI", 50)

    print(f"{symbol} → {s1['RECOMMENDATION']} / {s5['RECOMMENDATION']} (RSI {rsi})")

    # 🔥 RELAXED CONDITIONS (MORE SIGNALS)
    if s1["RECOMMENDATION"] in ["BUY", "STRONG_BUY"] and s5["RECOMMENDATION"] in ["BUY", "STRONG_BUY"]:
        if rsi < 75:
            confidence = (s1["BUY"] + s5["BUY"]) / 40
            return "BUY", confidence, rsi

    if s1["RECOMMENDATION"] in ["SELL", "STRONG_SELL"] and s5["RECOMMENDATION"] in ["SELL", "STRONG_SELL"]:
        if rsi > 25:
            confidence = (s1["SELL"] + s5["SELL"]) / 40
            return "SELL", confidence, rsi

    return None

# ================= FORMAT =================
def format_signal(symbol, direction, confidence, rsi):
    return f"""
📊 {symbol}

{'🟢 BUY' if direction == 'BUY' else '🔴 SELL'}
Confidence: {round(confidence*100)}%
RSI: {round(rsi)}

⏱ 1M (confirmed 5M)
⚡ Enter now
"""

# ================= BOT LOOP =================
def bot_loop():
    print("🚀 ELITE BOT STARTED")
    send_signal("🔥 ELITE BOT IS LIVE")

    while True:
        for symbol, screener in MARKETS:
            now = time.time()

            if symbol in last_signal_time and now - last_signal_time[symbol] < COOLDOWN:
                continue

            result = elite_signal(symbol, screener)

            if result:
                direction, confidence, rsi = result

                if confidence >= 0.55:  # 🔥 more signals now
                    msg = format_signal(symbol, direction, confidence, rsi)
                    send_signal(msg)
                    last_signal_time[symbol] = now

        time.sleep(20)

# ================= SAFE START =================
def start_bot():
    thread = Thread(target=bot_loop)
    thread.daemon = True
    thread.start()

start_bot()

@app.route("/")
def home():
    return "🔥 ELITE BOT RUNNING"
