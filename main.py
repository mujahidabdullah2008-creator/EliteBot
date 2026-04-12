from flask import Flask, jsonify, request
from tradingview_ta import TA_Handler, Interval
import time

app = Flask(__name__)

# =========================
# CONFIG
# =========================
SYMBOL = "EURUSD"
SCREENER = "forex"
EXCHANGE = "FX_IDC"

last_signal_time = 0


# =========================
# ANALYSIS FUNCTION
# =========================
def get_signal(symbol):
    global last_signal_time

    try:
        now = time.time()

        # ⛔ Enforce 2-minute cycle
        if now - last_signal_time < 120:
            return {
                "signal": "WAIT",
                "reason": "Waiting 2-minute cycle"
            }

        handler = TA_Handler(
            symbol=symbol,
            screener=SCREENER,
            exchange=EXCHANGE,
            interval=Interval.INTERVAL_1_MINUTE
        )

        analysis = handler.get_analysis()
        indicators = analysis.indicators

        price = indicators.get("close")
        rsi = indicators.get("RSI")
        ema50 = indicators.get("EMA50")
        macd = indicators.get("MACD.macd")
        macd_signal = indicators.get("MACD.signal")

        # ✅ Prevent NULL crash
        if None in [price, rsi, ema50, macd, macd_signal]:
            return {
                "price": None,
                "signal": "WAIT",
                "reason": "Data not ready"
            }

        # =========================
        # SMART STRATEGY
        # =========================

        # BUY conditions
        if price > ema50 and rsi < 35 and macd > macd_signal:
            signal = "BUY"
            last_signal_time = now

        # SELL conditions
        elif price < ema50 and rsi > 65 and macd < macd_signal:
            signal = "SELL"
            last_signal_time = now

        else:
            signal = "WAIT"

        return {
            "price": round(price, 5),
            "rsi": round(rsi, 2),
            "ema50": round(ema50, 5),
            "signal": signal
        }

    except Exception as e:
        return {
            "price": None,
            "signal": "ERROR",
            "error": str(e)
        }


# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return jsonify({
        "status": "BOT RUNNING",
        "engine": "SMART 2-MIN ENGINE"
    })


@app.route("/signal")
def signal():
    symbol = request.args.get("symbol", SYMBOL)
    result = get_signal(symbol)
    return jsonify(result)


@app.route("/health")
def health():
    return jsonify({"status": "OK"})


# =========================
# START
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
