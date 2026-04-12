import os
import time
import requests
from flask import Flask
from threading import Thread
from tradingview_ta import TA_Handler, Interval

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("❌ Missing BOT_TOKEN or CHAT_ID")

# ================= MARKETS =================
MARKETS = [
    ("EURUSD", "forex"),
    ("GBPUSD", "forex"),
    ("USDJPY", "forex"),
    ("BTCUSDT", "crypto"),
    ("ETHUSDT", "crypto"),
    ("XAUUSD", "forex")
]

COOLDOWN = 120
last_signal = {}

# ================= TELEGRAM =================
def send(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print("📩 SENT")
    except Exception as e:
        print("Telegram error:", e)

# ================= DATA =================
def get_data(symbol, market):
    exchange = "FX_IDC" if market == "forex" else "BINANCE"

    try:
        handler = TA_Handler(
            symbol=symbol,
            screener="forex" if market == "forex" else "crypto",
            exchange=exchange,
            interval=Interval.INTERVAL_1_MINUTE
        )
        return handler.get_analysis()
    except:
        return None

# ================= SIGNAL ENGINE (FIXED) =================
def signal(symbol, market):
    data = get_data(symbol, market)
    if not data:
        return None

    s = data.summary
    ind = data.indicators

    buy = s.get("BUY", 0)
    sell = s.get("SELL", 0)
    total = buy + sell + s.get("NEUTRAL", 1)

    rsi = ind.get("RSI", 50)

    # SIMPLE FAST MODE LOGIC (IMPORTANT FIX)
    if buy > sell and rsi < 75:
        return "BUY", min(0.6 + (buy/total)*0.3, 0.95), rsi

    if sell > buy and rsi > 25:
        return "SELL", min(0.6 + (sell/total)*0.3, 0.95), rsi

    return None

# ================= FORMAT =================
def format_msg(symbol, direction, confidence, rsi):
    emoji = "🟢 BUY" if direction == "BUY" else "🔴 SELL"

    return f"""
🤖 ELITE SIGNAL ENGINE

📊 Asset: {symbol}
📉 Direction: {emoji}

💯 Confidence: {round(confidence*100)}%
📊 RSI: {round(rsi)}

⚡ FAST MODE ACTIVE
"""

# ================= LOOP =================
def run_bot():
    print("🚀 BOT STARTED")
    send("🔥 ELITE BOT LIVE (FIXED ENGINE)")

    while True:
        for symbol, market in MARKETS:
            now = time.time()

            if symbol in last_signal and now - last_signal[symbol] < COOLDOWN:
                continue

            result = signal(symbol, market)

            if result:
                direction, confidence, rsi = result

                if confidence > 0.55:
                    send(format_msg(symbol, direction, confidence, rsi))
                    last_signal[symbol] = now

        time.sleep(10)

# ================= FLASK =================
@app.route("/")
def home():
    return "🔥 ELITE BOT RUNNING (FIXED)"

Thread(target=run_bot).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
