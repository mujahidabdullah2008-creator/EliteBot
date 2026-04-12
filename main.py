import os
import time
import requests
from datetime import datetime
from threading import Thread
from flask import Flask
from tradingview_ta import TA_Handler, Interval

app = Flask(__name__)
import os
import time
import requests
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
from tradingview_ta import TA_Handler, Interval

app = Flask(__name__)

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

# ================= STATE CONTROL =================
active_trades = {}   # symbol -> trade data
COOLDOWN = 120

# ================= TELEGRAM =================
def send(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ================= ANALYSIS =================
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

# ================= SIGNAL ENGINE =================
def generate_signal(symbol, screener):
    a = get_analysis(symbol, screener)
    if not a:
        return None

    s = a.summary
    ind = a.indicators

    buy = s["BUY"]
    sell = s["SELL"]
    rsi = ind.get("RSI", 50)

    if buy >= sell:
        direction = "BUY"
        strength = buy / max(buy + sell, 1)
    else:
        direction = "SELL"
        strength = sell / max(buy + sell, 1)

    confidence = 0.50 + (strength * 0.30)

    if direction == "BUY" and rsi < 70:
        confidence += 0.05
    if direction == "SELL" and rsi > 30:
        confidence += 0.05

    return direction, min(confidence, 0.92), rsi

# ================= FORMAT =================
def format_signal(symbol, direction, confidence, rsi, stage):
    now = datetime.now().strftime("%I:%M %p")

    flag = "🇪🇺" if "EUR" in symbol else "🇬🇧" if "GBP" in symbol else "🇯🇵" if "JPY" in symbol else "₿" if "BTC" in symbol else "💰"

    return f"""
🤖 AlphaSignalsBot
🚨 SIGNAL ALERT ({stage})

📉 {flag} {symbol}
⏰ Expiry: 2 minutes
📍 Entry Time: {now}

📈 Direction: {'BUY 🟢' if direction == 'BUY' else 'SELL 🟥'}
💯 Confidence: {round(confidence * 100)}%
📉 RSI: {round(rsi)}

🎯 Martingale Levels:
🔁 Level 1 → +2 min
🔁 Level 2 → +4 min
🔁 Level 3 → +6 min
"""

# ================= TRADE SYSTEM =================
def bot():
    print("🚀 LEVEL 7 TRADE ENGINE ACTIVE")
    send("🚀 AlphaSignalsBot LEVEL 7 FIX ONLINE")

    while True:
        now = datetime.now()

        for symbol, market in MARKETS:

            # ================= BLOCK ACTIVE TRADE =================
            if symbol in active_trades:
                trade = active_trades[symbol]

                entry_time = trade["time"]

                # M1
                if not trade["m1"] and now >= entry_time + timedelta(minutes=2):
                    send(format_signal(symbol, trade["dir"], trade["conf"], trade["rsi"], "M1"))
                    trade["m1"] = True

                # M2
                if not trade["m2"] and now >= entry_time + timedelta(minutes=4):
                    send(format_signal(symbol, trade["dir"], trade["conf"], trade["rsi"], "M2"))
                    trade["m2"] = True

                # M3
                if not trade["m3"] and now >= entry_time + timedelta(minutes=6):
                    send(format_signal(symbol, trade["dir"], trade["conf"], trade["rsi"], "M3"))
                    trade["m3"] = True
                    del active_trades[symbol]

                continue

            # ================= NEW SIGNAL =================
            result = generate_signal(symbol, market)

            if result:
                direction, confidence, rsi = result

                if confidence >= 0.55:

                    send(format_signal(symbol, direction, confidence, rsi, "ENTRY"))

                    active_trades[symbol] = {
                        "dir": direction,
                        "conf": confidence,
                        "rsi": rsi,
                        "time": now,
                        "m1": False,
                        "m2": False,
                        "m3": False
                    }

        time.sleep(5)

# ================= ROUTE =================
@app.route("/")
def home():
    return "LEVEL 7 FIX ACTIVE"

# ================= START =================
Thread(target=bot).start()
