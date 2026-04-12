from flask import Flask, jsonify
import threading
import time
from datetime import datetime
import pytz
from tradingview_ta import TA_Handler, Interval

app = Flask(__name__)

# ===== CONFIG =====
SYMBOLS = [
    ("EURUSD", "FX_IDC:EURUSD"),
    ("GBPUSD", "FX_IDC:GBPUSD"),
    ("USDJPY", "FX_IDC:USDJPY"),
    ("BTCUSDT", "BINANCE:BTCUSDT"),
    ("ETHUSDT", "BINANCE:ETHUSDT"),
    ("XAUUSD", "OANDA:XAUUSD")
]

TIMEFRAME = Interval.INTERVAL_1_MINUTE  # ✅ FIXED (no 5-minute bug)
SIGNAL_COOLDOWN = 120  # 2 minutes cycle

last_signal_time = 0


# ===== ANALYSIS ENGINE =====
def get_analysis(symbol, screener):
    handler = TA_Handler(
        symbol=screener.split(":")[1],
        screener="crypto" if "BINANCE" in screener else "forex",
        exchange=screener.split(":")[0] if ":" in screener else "FX_IDC",
        interval=TIMEFRAME
    )
    return handler.get_analysis()


def generate_signal():
    global last_signal_time

    now = time.time()

    # prevent spam signals (IMPORTANT FIX)
    if now - last_signal_time < SIGNAL_COOLDOWN:
        return None

    for name, symbol in SYMBOLS:
        try:
            analysis = get_analysis(name, symbol)

            rsi = analysis.indicators.get("RSI", 50)
            action = analysis.summary["RECOMMENDATION"]

            direction = "BUY 🟢" if "BUY" in action else "SELL 🔴"

            confidence = min(85, max(55, int(abs(50 - rsi) + 55)))

            if confidence < 60:
                continue

            last_signal_time = now

            return {
                "asset": name,
                "direction": direction,
                "rsi": round(rsi, 2),
                "confidence": confidence
            }

        except Exception as e:
            print("ERROR:", e)

    return None


# ===== FORMAT (YOUR REQUEST STYLE) =====
def format_signal(sig):
    now = datetime.now(pytz.timezone("Africa/Lagos"))
    entry = now.strftime("%I:%M %p")

    return f"""
🤖 AlphaSignalsBot
🚨 SIGNAL ALERT  

📉 {sig['asset']}
⏰ Expiry: 2 minutes
📍 Entry Time: {entry}

📈 Direction: {sig['direction']}
💯 Confidence: {sig['confidence']}%
📉 RSI: {sig['rsi']}

🎯 Martingale Levels:
🔁 Level 1 → {(now).strftime('%I:%M %p')}
🔁 Level 2 → {(now).strftime('%I:%M %p')}
🔁 Level 3 → {(now).strftime('%I:%M %p')}
"""


# ===== BACKGROUND ENGINE =====
def bot_loop():
    print("🚀 LEVEL 7 FIXED ENGINE RUNNING")

    while True:
        signal = generate_signal()

        if signal:
            print(format_signal(signal))
        else:
            print("⏳ No valid signal (waiting trend cycle)")

        time.sleep(30)


# ===== FLASK ROUTE =====
@app.route("/")
def home():
    return jsonify({"status": "LEVEL 7 FIXED ENGINE ACTIVE"})


# ===== START BOT THREAD =====
threading.Thread(target=bot_loop, daemon=True).start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
