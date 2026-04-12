from flask import Flask, jsonify
from tradingview_ta import TA_Handler, Interval
import threading
import time

app = Flask(__name__)

latest_signal = {"signal": "WAITING", "price": None}

def generate_signal():
    global latest_signal

    handler = TA_Handler(
        symbol="BTCUSDT",
        screener="crypto",
        exchange="BINANCE",
        interval=Interval.INTERVAL_2_MINUTES
    )

    while True:
        analysis = handler.get_analysis()

        if analysis.summary["RECOMMENDATION"] in ["BUY", "STRONG_BUY"]:
            latest_signal = {"signal": "BUY", "price": analysis.indicators["close"]}
        elif analysis.summary["RECOMMENDATION"] in ["SELL", "STRONG_SELL"]:
            latest_signal = {"signal": "SELL", "price": analysis.indicators["close"]}
        else:
            latest_signal = {"signal": "HOLD", "price": analysis.indicators["close"]}

        time.sleep(120)  # 2 minutes

@app.route("/")
def home():
    return "BOT RUNNING OK"

@app.route("/signal")
def signal():
    return jsonify(latest_signal)

if __name__ == "__main__":
    t = threading.Thread(target=generate_signal)
    t.start()
    app.run(host="0.0.0.0", port=10000)
