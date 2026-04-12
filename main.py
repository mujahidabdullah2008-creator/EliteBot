from flask import Flask, jsonify
from tradingview_ta import TA_Handler, Interval
import requests
import time
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# =========================
# CONFIG
# =========================
SYMBOL = "EURUSD"
SCREENER = "forex"
EXCHANGE = "FX_IDC"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

last_signal_time = 0


# =========================
# TELEGRAM
# =========================
def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}

    try:
        requests.post(url, data=data, timeout=5)
    except:
        pass


# =========================
# FORMAT SIGNAL
# =========================
def format_signal(signal, price, rsi):
    now = datetime.utcnow()

    entry_time = now.strftime("%I:%M %p")
    m1 = (now + timedelta(minutes=2)).strftime("%I:%M %p")
    m2 = (now + timedelta(minutes=4)).strftime("%I:%M %p")
    m3 = (now + timedelta(minutes=6)).strftime("%I:%M %p")

    direction_emoji = "🟩" if signal == "BUY" else "🟥"

    return f"""
🤖 AlphaSignalsBot
🚨 SIGNAL ALERT  

📉 🇪🇺 EUR/USD 🇺🇸 (OTC)
⏰ Expiry: 2 minutes
📍 Entry Time: {entry_time}

📈 Direction: {signal} {direction_emoji}
💯 Confidence: 70%

🎯 Martingale Levels:
🔁 Level 1 → {m1}
🔁 Level 2 → {m2}
🔁 Level 3 → {m3}
"""


# =========================
# SIGNAL ENGINE
# =========================
def get_signal():
    global last_signal_time

    try:
        now = time.time()

        handler = TA_Handler(
            symbol=SYMBOL,
            screener=SCREENER,
            exchange=EXCHANGE,
            interval=Interval.INTERVAL_1_MINUTE
        )

        analysis = handler.get_analysis()
        data = analysis.indicators

        price = data.get("close")
        rsi = data.get("RSI")
        ema50 = data.get("EMA50")
        macd = data.get("MACD.macd")
        macd_signal = data.get("MACD.signal")

        if None in [price, rsi, ema50, macd, macd_signal]:
            return {"signal": "WAIT"}

        # cooldown (2 mins)
        if now - last_signal_time < 120:
            return {"signal": "WAIT"}

        signal = "WAIT"

        # 🔥 REVERSAL
        if rsi < 25:
            signal = "BUY"
        elif rsi > 75:
            signal = "SELL"

        # 📈 TREND
        elif price > ema50 and rsi < 45 and macd > macd_signal:
            signal = "BUY"
        elif price < ema50 and rsi > 55 and macd < macd_signal:
            signal = "SELL"

        # 🚀 SEND
        if signal in ["BUY", "SELL"]:
            last_signal_time = now

            message = format_signal(signal, price, rsi)
            send_telegram(message)

        return {
            "price": round(price, 5),
            "rsi": round(rsi, 2),
            "signal": signal
        }

    except Exception as e:
        return {"signal": "ERROR", "error": str(e)}


# =========================
# AUTO LOOP (IMPORTANT)
# =========================
def run_bot():
    while True:
        get_signal()
        time.sleep(60)  # check every 1 min


# =========================
# ROUTES
# =========================
@app.route("/")
def home():
    return jsonify({"status": "AlphaSignalsBot Running 🤖"})


@app.route("/health")
def health():
    return jsonify({"status": "OK"})


# =========================
# START
# =========================
if __name__ == "__main__":
    import threading
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=10000)
