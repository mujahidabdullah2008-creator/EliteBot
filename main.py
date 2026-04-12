from flask import Flask, jsonify
import threading
import time
from datetime import datetime
import pytz

from tradingview_ta import TA_Handler, Interval

app = Flask(__name__)

SYMBOLS = [
    ("EURUSD", "FX_IDC:EURUSD"),
    ("GBPUSD", "FX_IDC:GBPUSD"),
    ("USDJPY", "FX_IDC:USDJPY"),
    ("BTCUSDT", "BINANCE:BTCUSDT"),
    ("ETHUSDT", "BINANCE:ETHUSDT"),
    ("XAUUSD", "OANDA:XAUUSD")
]

COOLDOWN = 120
last_signal_time = 0


# =========================
# GET MARKET DATA
# =========================
def get_analysis(name, symbol):
    exchange, sym = symbol.split(":")

    screener = "crypto" if "BINANCE" in exchange else "forex"

    handler = TA_Handler(
        symbol=sym,
        screener=screener,
        exchange=exchange,
        interval=Interval.INTERVAL_1_MINUTE
    )

    return handler.get_analysis()


# =========================
# SIGNAL LOGIC (FIXED)
# =========================
def calculate_signal(name, symbol):
    try:
        analysis = get_analysis(name, symbol)

        rec = analysis.summary.get("RECOMMENDATION", "NEUTRAL")
        indicators = analysis.indicators

        rsi = indicators.get("RSI", 50)

        # Normalize recommendation
        rec = rec.upper()

        if "BUY" in rec:
            direction = "BUY 🟢"
        elif "SELL" in rec:
            direction = "SELL 🔴"
        else:
            return None  # ignore neutral only

        # Simple RSI sanity check (NOT strict)
        if direction.startswith("BUY") and rsi > 80:
            return None
        if direction.startswith("SELL") and rsi < 20:
            return None

        # Confidence (REALISTIC, not fake strict)
        confidence = 60 + abs(50 - rsi)

        return {
            "asset": name,
            "direction": direction,
            "rsi": round(rsi, 2),
            "confidence": int(min(confidence, 90))
        }

    except Exception as e:
        print(f"ERROR on {name}: {e}")
        return None


# =========================
# FORMAT SIGNAL
# =========================
def format_signal(sig):
    now = datetime.now(pytz.timezone("Africa/Lagos"))
    t = now.strftime("%I:%M %p")

    return f"""
🤖 AlphaSignalsBot
🚨 LIVE SIGNAL

📉 {sig['asset']}
⏰ Expiry: 2 minutes
📍 Entry Time: {t}

📈 Direction: {sig['direction']}
💯 Confidence: {sig['confidence']}%
📉 RSI: {sig['rsi']}

🎯 Martingale Levels:
🔁 Level 1 → {t}
🔁 Level 2 → {t}
🔁 Level 3 → {t}
"""


# =========================
# BOT ENGINE
# =========================
def bot():
    global last_signal_time
    print("🚀 BOT RUNNING (FIXED VERSION)")

    while True:
        now = time.time()

        # cooldown control
        if now - last_signal_time < COOLDOWN:
            time.sleep(5)
            continue

        signal_found = False

        for name, symbol in SYMBOLS:
            sig = calculate_signal(name, symbol)

            # DEBUG (VERY IMPORTANT)
            print(f"Checking {name} ->", sig)

            if sig:
                print(format_signal(sig))
                last_signal_time = now
                signal_found = True
                break

        if not signal_found:
            print("⚠️ No valid signal at this time")

        time.sleep(10)


# =========================
# FLASK SERVER
# =========================
@app.route("/")
def home():
    return jsonify({
        "status": "BOT RUNNING",
        "mode": "FIXED ENGINE",
        "cooldown": COOLDOWN
    })


threading.Thread(target=bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
