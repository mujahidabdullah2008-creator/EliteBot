from flask import Flask, jsonify
from tradingview_ta import TA_Handler, Interval
import requests
import os
import threading
import time
from datetime import datetime, timedelta

app = Flask(__name__)

# 🔑 ENV VARIABLES
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 🧠 PREVENT SPAM
last_signal_time = None


# 📊 GET MARKET DATA
def get_analysis():
    handler = TA_Handler(
        symbol="EURUSD",
        screener="forex",
        exchange="FX_IDC",
        interval=Interval.INTERVAL_1_MINUTE
    )
    return handler.get_analysis()


# 🤖 SMART SIGNAL LOGIC (IMPROVED)
def generate_signal():
    analysis = get_analysis()
    ind = analysis.indicators

    price = ind.get("close")
    rsi = ind.get("RSI")
    ema50 = ind.get("EMA50")
    macd = ind.get("MACD.macd")

    signal = "WAIT"
    confidence = 0

    # 🔥 MORE REALISTIC CONDITIONS (NOT TOO STRICT)
    if rsi and ema50 and macd:
        # BUY condition
        if rsi < 40 and price < ema50 and macd < 0:
            signal = "BUY"
            confidence = 65

        # SELL condition
        elif rsi > 60 and price > ema50 and macd > 0:
            signal = "SELL"
            confidence = 65

    return {
        "price": price,
        "rsi": rsi,
        "ema50": ema50,
        "macd": macd,
        "signal": signal,
        "confidence": confidence
    }


# 📩 FORMAT MESSAGE (YOUR STYLE)
def format_message(data):
    now = datetime.now()

    direction = "BUY 🟩" if data["signal"] == "BUY" else "SELL 🟥"

    return f"""🤖 AlphaSignalsBot
🚨 SIGNAL ALERT  

📉 🇪🇺 EUR/USD 🇺🇸 (OTC)
⏰ Expiry: 2 minutes
📍 Entry Time: {now.strftime('%I:%M %p')}

📈 Direction: {direction}
💯 Confidence: {data['confidence']}%

🎯 Martingale Levels:
🔁 Level 1 → {(now + timedelta(minutes=2)).strftime('%I:%M %p')}
🔁 Level 2 → {(now + timedelta(minutes=4)).strftime('%I:%M %p')}
🔁 Level 3 → {(now + timedelta(minutes=6)).strftime('%I:%M %p')}
"""


# 📤 SEND TELEGRAM
def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Missing BOT_TOKEN or CHAT_ID")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}

    try:
        requests.post(url, data=payload)
        print("✅ Sent to Telegram")
    except Exception as e:
        print("❌ Telegram Error:", e)


# 🔁 AUTO LOOP (CORE ENGINE)
def auto_loop():
    global last_signal_time

    while True:
        try:
            data = generate_signal()

            print("📊 Checking market:", data)

            # 🚫 Skip if no signal
            if data["signal"] == "WAIT":
                print("⏳ No signal")
            
            else:
                now = datetime.now()

                # 🚫 Avoid spamming (1 signal per 2 mins)
                if last_signal_time and (now - last_signal_time).seconds < 120:
                    print("🚫 Skipped (cooldown)")
                else:
                    msg = format_message(data)
                    send_telegram(msg)
                    last_signal_time = now

        except Exception as e:
            print("❌ Error:", e)

        time.sleep(60)  # ⏱ runs every 1 minute


# 🌐 ROUTES (FOR TESTING ONLY)
@app.route("/")
def home():
    return jsonify({"status": "AlphaSignalsBot FULL AUTO 🤖"})


@app.route("/signal")
def signal():
    return jsonify(generate_signal())


# 🚀 START BACKGROUND LOOP
threading.Thread(target=auto_loop).start()


# 🔥 RUN SERVER
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
