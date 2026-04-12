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
# SIGNAL ENGINE
# =========================
def get_signal(symbol):
    global last_signal_time

    try:
        now = time.time()

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

        # 🚫 Prevent bad data
        if None in [price, rsi, ema50, macd, macd_signal]:
            return {
                "price": None,
                "signal": "WAIT",
                "reason": "Data not ready"
            }

        # ⛔ 2-minute delay (ONLY after a trade)
        if now - last_signal_time < 120:
            return {
                "price": round(price, 5),
                "rsi": round(rsi, 2),
                "signal": "WAIT",
                "reason": "Cooldown active"
            }

        # =========================
        # SMART LOGIC
        # =========================

        signal = "WAIT"

        # 🔥 REVERSAL (strong signals)
        if rsi < 25:
            signal = "BUY"

        elif rsi > 75:
            signal = "SELL"

        # 📈 TREND CONFIRMATION
        elif price > ema50 and rsi < 45 and macd > macd_signal:
            signal = "BUY"

        elif price < ema50 and rsi > 55 and macd < macd_signal:
            signal = "SELL"

        # Save time ONLY if trade happens
        if signal in ["BUY", "SELL"]:
            last_signal_time = now

        return {
            "price": round(price, 5),
            "rsi": round(rsi, 2),
            "ema50": round(ema50, 5),
            "macd": round(macd, 5),
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
        "engine": "SMART ACTIVE ENGINE"
    })


@app.route("/signal")
def signal():
    symbol = request.args.get("symbol", SYMBOL)
    return jsonify(get_signal(symbol))


@app.route("/health")
def health():
    return jsonify({"status": "OK"})


# =========================
# START
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
