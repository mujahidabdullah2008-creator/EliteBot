from flask import Flask, jsonify, request
from tradingview_ta import TA_Handler, Interval
import traceback

app = Flask(__name__)

# =========================
# CONFIG
# =========================
DEFAULT_SYMBOL = "EURUSD"
DEFAULT_EXCHANGE = "FX_IDC"
DEFAULT_SCREENER = "forex"


# =========================
# CORE ENGINE
# =========================
def get_analysis(symbol):
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener=DEFAULT_SCREENER,
            exchange=DEFAULT_EXCHANGE,
            interval=Interval.INTERVAL_2_MINUTES
        )

        analysis = handler.get_analysis()
        indicators = analysis.indicators

        price = indicators.get("close")
        rsi = indicators.get("RSI")
        macd = indicators.get("MACD.macd")
        macd_signal = indicators.get("MACD.signal")

        # SAFE CHECK (prevents null crashes)
        if price is None or rsi is None or macd is None or macd_signal is None:
            return {
                "price": None,
                "signal": "WAITING",
                "reason": "Insufficient indicator data"
            }

        # =========================
        # SIMPLE STRATEGY LOGIC
        # =========================

        if rsi <= 30 and macd > macd_signal:
            signal = "BUY"

        elif rsi >= 70 and macd < macd_signal:
            signal = "SELL"

        else:
            signal = "WAIT"

        return {
            "price": price,
            "rsi": rsi,
            "macd": macd,
            "macd_signal": macd_signal,
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
        "message": "2-MINUTE ENGINE ACTIVE"
    })


@app.route("/signal", methods=["GET"])
def signal():
    symbol = request.args.get("symbol", DEFAULT_SYMBOL)

    result = get_analysis(symbol)

    return jsonify(result)


@app.route("/health")
def health():
    return jsonify({"status": "OK"})


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
