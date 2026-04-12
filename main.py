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

last_signal_time = 0
COOLDOWN = 120  # 2 minutes


# ===== GET ANALYSIS =====
def get_analysis(name, symbol):
    handler = TA_Handler(
        symbol=symbol.split(":")[1],
        screener="crypto" if "BINANCE" in symbol else "forex",
        exchange=symbol.split(":")[0],
        interval=Interval.INTERVAL_1_MINUTE
    )
    return handler.get_analysis()


# ===== LEVEL 8 SMART SCORE ENGINE =====
def calculate_signal(name, symbol):
    analysis = get_analysis(name, symbol)

    rsi = analysis.indicators.get("RSI", 50)
    recommendation = analysis.summary["RECOMMENDATION"]

    # 🔥 TREND FILTER (KEY UPGRADE)
    trend = recommendation  # BUY / SELL / NEUTRAL

    if trend not in ["BUY", "SELL"]:
        return None

    # 🔥 SCORE ENGINE
    rsi_score = abs(50 - rsi)

    if rsi_score < 6:
        return None  # weak market

    confidence = 50 + rsi_score

    if confidence < 65:
        return None

    direction = "BUY 🟢" if trend == "BUY" else "SELL 🔴"

    return {
        "asset": name,
        "direction": direction,
        "rsi": round(rsi, 2),
        "confidence": int(min(confidence, 92))
    }


# ===== FORMAT SIGNAL =====
def format_signal(sig):
    now = datetime.now(pytz.timezone("Africa/Lagos"))
    t = now.strftime("%I:%M %p")

    return f"""
🤖 AlphaSignalsBot
🚨 LEVEL 8 SIGNAL ENGINE

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


# ===== ENGINE LOOP =====
def bot():
    global last_signal_time
    print("🚀 LEVEL 8 ENGINE ACTIVE")

    while True:
        now = time.time()

        if now - last_signal_time < COOLDOWN:
            time.sleep(5)
            continue

        for name, symbol in SYMBOLS:
            try:
                sig = calculate_signal(name, symbol)

                if sig:
                    last_signal_time = now
                    print(format_signal(sig))
                    break

            except Exception as e:
                print("ERROR:", e)

        time.sleep(10)


# ===== FLASK =====
@app.route("/")
def home():
    return jsonify({"status": "LEVEL 8 ENGINE RUNNING"})


threading.Thread(target=bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
