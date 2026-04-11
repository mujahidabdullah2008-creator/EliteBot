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

# ================= SETTINGS =================
PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]
COOLDOWN = 300  # 5 minutes per pair
last_signal_time = {}

# ================= TELEGRAM =================
def send_signal(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for _ in range(3):
        try:
            requests.post(url, data={"chat_id": CHAT_ID, "text": message})
            print("📩 Sent:", message)
            return
        except:
            time.sleep(2)

# ================= ANALYSIS =================
def get_analysis(pair, interval):
    try:
        handler = TA_Handler(
            symbol=pair,
            screener="forex",
            exchange="FX_IDC",
            interval=interval
        )
        return handler.get_analysis()
    except Exception as e:
        print(f"❌ Error {pair}:", e)
        return None

# ================= ELITE STRATEGY =================
def elite_signal(pair):
    a1 = get_analysis(pair, Interval.INTERVAL_1_MINUTE)
    a5 = get_analysis(pair, Interval.INTERVAL_5_MINUTES)

    if not a1 or not a5:
        return None

    s1 = a1.summary
    s5 = a5.summary
    ind = a1.indicators

    rsi = ind.get("RSI", 50)

    # --- Trend alignment ---
    if s1["RECOMMENDATION"] == "STRONG_BUY" and s5["RECOMMENDATION"] in ["BUY", "STRONG_BUY"]:
        if rsi < 70:  # avoid overbought
            confidence = (s1["BUY"] + s5["BUY"]) / (
                s1["BUY"] + s1["SELL"] + s1["NEUTRAL"] +
                s5["BUY"] + s5["SELL"] + s5["NEUTRAL"]
            )
            return "BUY", confidence, rsi

    if s1["RECOMMENDATION"] == "STRONG_SELL" and s5["RECOMMENDATION"] in ["SELL", "STRONG_SELL"]:
        if rsi > 30:  # avoid oversold
            confidence = (s1["SELL"] + s5["SELL"]) / (
                s1["BUY"] + s1["SELL"] + s1["NEUTRAL"] +
                s5["BUY"] + s5["SELL"] + s5["NEUTRAL"]
            )
            return "SELL", confidence, rsi

    return None

# ================= FORMAT =================
def format_signal(pair, direction, confidence, rsi):
    flag = "🇪🇺" if "EUR" in pair else "🇬🇧" if "GBP" in pair else "🇯🇵"

    return f"""
{flag} {pair}

{'🟢 BUY' if direction == 'BUY' else '🔴 SELL'}
Confidence: {round(confidence*100)}%
RSI: {round(rsi)}

Timeframe: 1M (Confirmed with 5M)

⚡ Trade immediately
"""

# ================= BOT LOOP =================
def bot_loop():
    print("🚀 ELITE BOT STARTED")
    send_signal("🔥 ELITE BOT IS LIVE")

    while True:
        for pair in PAIRS:
            now = time.time()

            # cooldown
            if pair in last_signal_time and now - last_signal_time[pair] < COOLDOWN:
                continue

            result = elite_signal(pair)

            if result:
                direction, confidence, rsi = result

                if confidence >= 0.65:  # final filter
                    msg = format_signal(pair, direction, confidence, rsi)
                    send_signal(msg)
                    last_signal_time[pair] = now

        time.sleep(30)

# ================= ROUTE =================
@app.route("/")
def home():
    return "🔥 ELITE BOT RUNNING"

# ================= START =================
Thread(target=bot_loop).start()
