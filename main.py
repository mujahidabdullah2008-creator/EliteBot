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
    ("XAUUSD", "forex")
]

COOLDOWN = 180
last_signal_time = 0

# ================= TELEGRAM =================
def send_signal(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ================= GET DATA =================
def get_analysis(symbol, interval):
    try:
        return TA_Handler(
            symbol=symbol,
            screener="forex" if symbol not in ["BTCUSDT", "ETHUSDT"] else "crypto",
            exchange="FX_IDC" if symbol not in ["BTCUSDT", "ETHUSDT"] else "BINANCE",
            interval=interval
        ).get_analysis()
    except:
        return None

# ================= SCORE ENGINE =================
def score(symbol):
    a1 = get_analysis(symbol, Interval.INTERVAL_1_MINUTE)
    a5 = get_analysis(symbol, Interval.INTERVAL_5_MINUTE)
    a15 = get_analysis(symbol, Interval.INTERVAL_15_MINUTES)

    if not a1 or not a5 or not a15:
        return None

    s1, s5, s15 = a1.summary, a5.summary, a15.summary
    rsi = a1.indicators.get("RSI", 50)

    # direction check
    direction = s1["RECOMMENDATION"]

    if direction not in ["BUY", "STRONG_BUY", "SELL", "STRONG_SELL"]:
        return None

    # alignment filter
    if s1["RECOMMENDATION"] != s5["RECOMMENDATION"]:
        return None

    if "BUY" in direction and "SELL" in s15["RECOMMENDATION"]:
        return None
    if "SELL" in direction and "BUY" in s15["RECOMMENDATION"]:
        return None

    buy = s1["BUY"] + s5["BUY"] + s15["BUY"]
    sell = s1["SELL"] + s5["SELL"] + s15["SELL"]
    total = buy + sell + s1["NEUTRAL"] + s5["NEUTRAL"] + s15["NEUTRAL"]

    confidence = max(buy, sell) / total if total else 0

    final_dir = "BUY" if buy > sell else "SELL"

    return {
        "symbol": symbol,
        "direction": final_dir,
        "confidence": confidence,
        "rsi": rsi
    }

# ================= FORMAT =================
def format_signal(s):
    flag = "🇪🇺" if "EUR" in s["symbol"] else "🇬🇧" if "GBP" in s["symbol"] else "🇯🇵" if "JPY" in s["symbol"] else "₿"

    entry_time = time.strftime("%I:%M %p")
    t = time.localtime(time.time() + 120)

    martingale = f"""
🎯 Martingale Levels:
🔁 Level 1 → {time.strftime("%I:%M %p", t)}
🔁 Level 2 → {time.strftime("%I:%M %p", time.localtime(time.time() + 240))}
🔁 Level 3 → {time.strftime("%I:%M %p", time.localtime(time.time() + 360))}
"""

    return f"""
🤖 AlphaSignalsBot
🚨 SIGNAL ALERT  

📉 {flag} {s['symbol']}
⏰ Expiry: 2 minutes
📍 Entry Time: {entry_time}

📈 Direction: {'🟢 BUY' if s['direction']=='BUY' else 'SELL 🟥'}
💯 Confidence: {round(s['confidence']*100)}%
📉 RSI: {round(s['rsi'])}

{martingale}

⚡ LEVEL 3 GOD MODE CONFIRMED
"""

# ================= LOOP =================
def bot():
    global last_signal_time
    print("🚀 LEVEL 3 GOD MODE ACTIVE")
    send_signal("🔥 LEVEL 3 GOD MODE BOT LIVE")

    while True:
        best = None

        for symbol, _ in MARKETS:
            s = score(symbol)
            if not s:
                continue

            if s["confidence"] < 0.65:
                continue

            if not best or s["confidence"] > best["confidence"]:
                best = s

        now = time.time()

        if best and now - last_signal_time > COOLDOWN:
            send_signal(format_signal(best))
            last_signal_time = now

        time.sleep(20)

@app.route("/")
def home():
    return "LEVEL 3 GOD MODE RUNNING"

Thread(target=bot).start()
