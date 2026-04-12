from flask import Flask, jsonify
from tradingview_ta import TA_Handler, Interval
import os
import requests
from datetime import datetime

app = Flask(__name__)

# 🔑 ENV VARIABLES (FIXED)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


# 📊 GET MARKET DATA
def get_analysis():
    handler = TA_Handler(
        symbol="EURUSD",
        screener="forex",
        exchange="FX_IDC",
        interval=Interval.INTERVAL_1_MINUTE  # ✅ FIXED (correct enum)
    )
    return handler.get_analysis()


# 🤖 SIGNAL LOGIC (SIMPLE & CLEAN)
def generate_signal():
    analysis = get_analysis()
    ind = analysis.indicators

    price = ind.get("close")
    rsi = ind.get("RSI")
    ema50 = ind.get("EMA50")
    macd = ind.get("MACD.macd")

    signal = "WAIT"

    if rsi and ema50 and macd:
        if rsi < 30 and price < ema50 and macd < 0:
            signal = "BUY"
        elif rsi > 70 and price > ema50 and macd > 0:
            signal = "SELL"

    return {
        "price": price,
        "rsi": rsi,
        "ema50": ema50,
        "macd": macd,
        "signal": signal
    }


# 📩 FORMAT MESSAGE (YOUR STYLE)
def format_message(data):
    now = datetime.now()

    direction = "BUY 🟩" if data["signal"] == "BUY" else "SELL 🟥"

    return f"""🤖 AlphaSignalsBot
🚨 SIGNAL ALERT  

📉 🇪🇺 EUR/USD 🇺🇸
⏰ Entry Time: {now.strftime('%I:%M %p')}

📈 Direction: {direction}
💯 Confidence: 70%

📊 Price: {data['price']}
📉 RSI: {data['rsi']}
📈 EMA50: {data['ema50']}
📊 MACD: {data['macd']}
"""


# 📤 SEND TO TELEGRAM (FIXED)
def send_telegram(text):
    if not BOT_TOKEN or not CHAT_ID:
        return {"error": "Missing BOT_TOKEN or CHAT_ID"}

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }

    return requests.post(url, data=payload).json()


# 🌐 HOME ROUTE
@app.route("/")
def home():
    return jsonify({"status": "AlphaSignalsBot Running 🤖"})


# 📊 SIGNAL CHECK
@app.route("/signal")
def signal():
    return jsonify(generate_signal())


# 🚀 AUTO SEND SIGNAL
@app.route("/auto")
def auto():
    data = generate_signal()

    if data["signal"] == "WAIT":
        return jsonify({
            "status": "NO SIGNAL",
            "data": data
        })

    message = format_message(data)
    result = send_telegram(message)

    return jsonify({
        "sent_signal": data,
        "telegram_response": result
    })


# 🔥 RUN
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
