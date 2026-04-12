from flask import Flask, jsonify
from tradingview_ta import TA_Handler, Interval
import requests
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# ================= CONFIG =================
SYMBOL = "EURUSD"
EXCHANGE = "FX_IDC"
SCREENER = "forex"

# Telegram ENV (IMPORTANT)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ================= SIGNAL FUNCTION =================
def get_signal():
    try:
        handler = TA_Handler(
            symbol=SYMBOL,
            screener=SCREENER,
            exchange=EXCHANGE,
            interval=Interval.INTERVAL_1_MINUTE
        )

        analysis = handler.get_analysis()

        rsi = analysis.indicators["RSI"]
        ema50 = analysis.indicators["EMA50"]
        macd = analysis.indicators["MACD.macd"]
        price = analysis.indicators["close"]

        signal = "WAIT"

        if rsi < 30 and price > ema50:
            signal = "BUY"
        elif rsi > 70 and price < ema50:
            signal = "SELL"

        return {
            "price": price,
            "rsi": round(rsi, 2),
            "ema50": ema50,
            "macd": macd,
            "signal": signal
        }

    except Exception as e:
        return {"error": str(e), "signal": "ERROR"}


# ================= TELEGRAM FORMAT =================
def send_telegram(signal_data):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Telegram ENV not set")
        return

    if signal_data["signal"] == "WAIT":
        return  # don't spam

    now = datetime.now()
    entry_time = now.strftime("%I:%M %p")

    m1 = (now + timedelta(minutes=2)).strftime("%I:%M %p")
    m2 = (now + timedelta(minutes=4)).strftime("%I:%M %p")
    m3 = (now + timedelta(minutes=6)).strftime("%I:%M %p")

    message = f"""
🤖 AlphaSignalsBot
🚨 SIGNAL ALERT  

📉 🇪🇺 EUR/USD 🇺🇸 (OTC)
⏰ Expiry: 2 minutes
📍 Entry Time: {entry_time}

📈 Direction: {signal_data['signal']} {"🟩" if signal_data['signal']=="BUY" else "🟥"}
💯 Confidence: 70%

🎯 Martingale Levels:
🔁 Level 1 → {m1}
🔁 Level 2 → {m2}
🔁 Level 3 → {m3}
"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": message})


# ================= ROUTES =================

@app.route("/")
def home():
    return {"status": "AlphaSignalsBot Running 🤖"}


@app.route("/signal")
def signal():
    data = get_signal()
    return jsonify(data)


@app.route("/auto")
def auto():
    data = get_signal()
    send_telegram(data)
    return jsonify({"sent": data})


# ================= RUN =================
if __name__ == "__main__":
    app.run()
