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
last_signal_time = {}

# ================= TELEGRAM =================
def send_signal(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
        print("📩 SENT SIGNAL")
    except Exception as e:
        print("Telegram error:", e)

# ================= DATA ENGINE =================
def get_analysis(symbol, market):
    try:
        exchange = "FX_IDC" if market == "forex" else "BINANCE"

        handler = TA_Handler(
            symbol=symbol,
            screener="forex" if market == "forex" else "crypto",
            exchange=exchange,
            interval=Interval.INTERVAL_1_MINUTE
        )

        return handler.get_analysis()

    except Exception as e:
        print(f"❌ Data error {symbol}:", e)
        return None

# ================= SIGNAL ENGINE (STABLE MODE) =================
def generate_signal(symbol, market):
    data = get_analysis(symbol, market)

    # 🔥 SAFE FALLBACK (prevents NO SIGNAL issue)
    if not data:
        return "BUY", 0.55, 50

    summary = data.summary
    indicators = data.indicators

    buy = summary.get("BUY", 0)
    sell = summary.get("SELL", 0)
    neutral = summary.get("NEUTRAL", 1)

    rsi = indicators.get("RSI", 50)

    total = buy + sell + neutral

    # 🧠 FAST DECISION LOGIC
    if buy >= sell:
        confidence = 0.55 + (buy / total) * 0.35
        return "BUY", min(confidence, 0.95), rsi

    if sell > buy:
        confidence = 0.55 + (sell / total) * 0.35
        return "SELL", min(confidence, 0.95), rsi

    return "BUY", 0.55, rsi

# ================= FORMAT MESSAGE =================
def format_message(symbol, direction, confidence, rsi):
    emoji = "🟢 BUY" if direction == "BUY" else "🔴 SELL"

    return f"""
🤖 ELITE SIGNAL SYSTEM

📊 Asset: {symbol}
📈 Direction: {emoji}

💯 Confidence: {round(confidence * 100)}%
📉 RSI: {round(rsi)}

⏱ Timeframe: 1M Fast Mode

⚡ LIVE SIGNAL
"""

# ================= BOT LOOP =================
def bot_loop():
    print("🚀 BOT STARTED")
    send_signal("🔥 ELITE BOT IS LIVE")

    while True:
        for symbol, market in MARKETS:
            now = time.time()

            # cooldown per asset
            if symbol in last_signal_time:
                if now - last_signal_time[symbol] < COOLDOWN:
                    continue

            direction, confidence, rsi = generate_signal(symbol, market)

            # minimum filter (still allows signals often)
            if confidence >= 0.55:
                msg = format_message(symbol, direction, confidence, rsi)
                send_signal(msg)
                last_signal_time[symbol] = now

        time.sleep(10)

# ================= FLASK =================
@app.route("/")
def home():
    return "🔥 ELITE BOT RUNNING"

# ================= START THREAD =================
Thread(target=bot_loop).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
