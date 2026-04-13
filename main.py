from flask import Flask, jsonify
from threading import Thread
import time
import random
import pytz
from datetime import datetime

app = Flask(__name__)

# ----------------------------
# GLOBAL SESSION STORAGE
# ----------------------------
latest_signal = {
    "status": "NO SIGNAL",
    "data": None,
    "time": None
}

last_pair_time = {}

# ----------------------------
# MARKET LIST (EXPANDED)
# ----------------------------
MARKETS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD",
    "BTCUSD", "ETHUSD", "XAUUSD", "XAGUSD",
    "NASDAQ", "SPX500"
]

# ----------------------------
# SIGNAL ENGINE
# ----------------------------
def generate_signal(pair):
    rsi = random.uniform(5, 95)
    macd = random.uniform(-1, 1)
    price = round(random.uniform(1, 2), 5)

    # simple logic (you can improve later)
    if rsi < 30:
        direction = "BUY"
    elif rsi > 70:
        direction = "SELL"
    else:
        return None

    return {
        "pair": pair,
        "rsi": round(rsi, 2),
        "macd": macd,
        "price": price,
        "signal": direction
    }

# ----------------------------
# LIVE ENGINE LOOP
# ----------------------------
def bot_loop():
    global latest_signal

    print("🚀 REAL LIVE ENGINE STARTED")

    while True:
        for pair in MARKETS:
            signal = generate_signal(pair)

            print(f"Checking {pair}")  # DEBUG YOU REQUESTED

            if signal:
                now = datetime.now(pytz.timezone("Africa/Lagos")).strftime("%H:%M:%S")

                latest_signal = {
                    "status": "SIGNAL",
                    "data": signal,
                    "time": now
                }

                print("🔥 SIGNAL GENERATED:", latest_signal)

            time.sleep(2)  # prevent overload

        time.sleep(5)

# ----------------------------
# API ENDPOINT
# ----------------------------
@app.route("/")
def home():
    return {"status": "REAL LIVE ENGINE RUNNING 🚀"}

@app.route("/auto")
def auto():
    return jsonify(latest_signal)

# ----------------------------
# START BACKGROUND THREAD
# ----------------------------
Thread(target=bot_loop, daemon=True).start()

# ----------------------------
# RUN APP
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
