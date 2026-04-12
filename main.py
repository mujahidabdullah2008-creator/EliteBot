import os
import time
import requests
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
from tradingview_ta import TA_Handler, Interval
import pytz

# ================= APP =================
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
    ("XAUUSD", "forex")  # GOLD
]

# ================= SETTINGS =================
COOLDOWN = 180  # 3 minutes per pair
last_signal_time = {}

tz = pytz.timezone("Africa/Lagos")  # Set your timezone

# ================= TELEGRAM =================
def send_signal(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for _ in range(3):
        try:
            requests.post(url, data={"chat_id": CHAT_ID, "text": message})
            print("📩 Sent:", message)
            return
        except Exception as e:
            print("❌ Telegram Error:", e)
            time.sleep(2)

# ================= ANALYSIS =================
def get_analysis(pair, interval, screener="forex"):
    try:
        handler = TA_Handler(
            symbol=pair,
            screener=screener,
            exchange="FX_IDC" if screener=="forex" else "BINANCE",
            interval=interval
        )
        return handler.get_analysis()
    except Exception as e:
        print(f"❌ Error {pair}:", e)
        return None

# ================= ELITE SIGNAL LOGIC =================
def elite_signal(pair, screener):
    a1 = get_analysis(pair, Interval.INTERVAL_1_MINUTE, screener)
    a5 = get_analysis(pair, Interval.INTERVAL_5_MINUTES, screener)
    a15 = get_analysis(pair, Interval.INTERVAL_15_MINUTES, screener)

    if not a1 or not a5 or not a15:
        return None

    s1 = a1.summary
    s5 = a5.summary
    s15 = a15.summary
    ind = a1.indicators

    rsi = ind.get("RSI", 50)

    # --- Trend alignment ---
    if s1["RECOMMENDATION"] in ["STRONG_BUY", "BUY"] and s5["RECOMMENDATION"] in ["STRONG_BUY", "BUY"]:
        if rsi < 70:
            confidence = (s1["BUY"] + s5["BUY"]) / (
                s1["BUY"] + s1["SELL"] + s1["NEUTRAL"] +
                s5["BUY"] + s5["SELL"] + s5["NEUTRAL"]
            )
            return "BUY", confidence, rsi

    if s1["RECOMMENDATION"] in ["STRONG_SELL", "SELL"] and s5["RECOMMENDATION"] in ["STRONG_SELL", "SELL"]:
        if rsi > 30:
            confidence = (s1["SELL"] + s5["SELL"]) / (
                s1["BUY"] + s1["SELL"] + s1["NEUTRAL"] +
                s5["BUY"] + s5["SELL"] + s5["NEUTRAL"]
            )
            return "SELL", confidence, rsi

    return None

# ================= FORMAT SIGNAL =================
def format_signal(pair, direction, confidence, rsi):
    now = datetime.now(tz)

    entry_time = now.strftime("%I:%M %p")
    expiry_time = (now + timedelta(minutes=2)).strftime("%I:%M %p")

    mg1 = (now + timedelta(minutes=2)).strftime("%I:%M %p")
    mg2 = (now + timedelta(minutes=4)).strftime("%I:%M %p")
    mg3 = (now + timedelta(minutes=6)).strftime("%I:%M %p")

    # Flag icons
    if "EUR" in pair:
        flag = "🇪🇺"
    elif "GBP" in pair:
        flag = "🇬🇧"
    elif "USDJPY" in pair:
        flag = "🇯🇵"
    elif "BTC" in pair or "ETH" in pair:
        flag = "🪙"
    elif "XAU" in pair:
        flag = "🥇"
    else:
        flag = "🌍"

    direction_icon = "🟥 SELL" if direction == "SELL" else "🟩 BUY"

    return f"""
🤖 ELITE AI BOT
🚨 SIGNAL ALERT  

📊 {flag} {pair}
⏰ Expiry: 2 minutes
📍 Entry Time: {entry_time}

📈 Direction: {direction_icon}
💯 Confidence: {round(confidence*100)}%
📊 RSI: {round(rsi)}

🎯 Martingale Levels:
🔁 Level 1 → {mg1}
🔁 Level 2 → {mg2}
🔁 Level 3 → {mg3}

⚡ Fast Trade Opportunity.
"""

# ================= BOT LOOP =================
def bot_loop():
    print("🚀 ELITE BOT STARTED")
    send_signal("🔥 ELITE BOT IS LIVE")

    while True:
        for pair, market_type in MARKETS:
            now = time.time()

            # cooldown
            if pair in last_signal_time and now - last_signal_time[pair] < COOLDOWN:
                continue

            result = elite_signal(pair, "forex" if market_type=="forex" else "crypto")

            if result:
                direction, confidence, rsi = result
                if confidence >= 0.55:  # less strict for faster signals
                    msg = format_signal(pair, direction, confidence, rsi)
                    send_signal(msg)
                    last_signal_time[pair] = now

        time.sleep(20)  # faster loop

# ================= ROUTE =================
@app.route("/")
def home():
    return "🔥 ELITE BOT RUNNING"

# ================= START =================
Thread(target=bot_loop).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
