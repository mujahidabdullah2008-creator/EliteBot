import os
import time
import requests
from datetime import datetime, timedelta
import pytz
from flask import Flask
from tradingview_ta import TA_Handler, Interval
import threading

app = Flask(__name__)

# ==============================
# ENV VARIABLES
# ==============================
from flask import Flask, jsonify
from threading import Thread
from tradingview_ta import TA_Handler, Interval
from datetime import datetime
import pytz
import os
import time

app = Flask(__name__)

# =====================
# ENV VARIABLES
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# =====================
# ASSETS (FOREX + CRYPTO + STOCKS + COMMODITIES)
# =====================
ASSETS = [
    ("FX_IDC:EURUSD", "EUR/USD 🇪🇺🇺🇸"),
    ("FX_IDC:GBPUSD", "GBP/USD 🇬🇧🇺🇸"),
    ("FX_IDC:USDJPY", "USD/JPY 🇺🇸🇯🇵"),
    ("BINANCE:BTCUSDT", "BTC/USDT ₿"),
    ("BINANCE:ETHUSDT", "ETH/USDT ⟠"),
    ("TVC:GOLD", "GOLD XAU/USD 🟡"),
    ("SP:SPX", "S&P 500 📊"),
]

last_signal = None


# =====================
# ANALYSIS FUNCTION
# =====================
def analyze(symbol):
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener="forex" if "FX" in symbol else "crypto",
            exchange="FX_IDC" if "FX" in symbol else "BINANCE",
            interval=Interval.INTERVAL_1_MINUTE
        )

        analysis = handler.get_analysis()

        rsi = analysis.indicators.get("RSI", 50)
        macd = analysis.indicators.get("MACD.macd", 0)
        price = analysis.indicators.get("close", 0)

        # SIMPLE STRATEGY
        if rsi < 30 and macd > 0:
            signal = "BUY"
        elif rsi > 70 and macd < 0:
            signal = "SELL"
        else:
            signal = "WAIT"

        return {
            "rsi": rsi,
            "macd": macd,
            "price": price,
            "signal": signal
        }

    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return {"signal": "WAIT", "rsi": 0, "macd": 0, "price": 0}


# =====================
# SIGNAL FORMAT (YOUR STYLE)
# =====================
def format_signal(name, direction, data):
    global last_signal

    tz = pytz.timezone("Africa/Lagos")
    now = datetime.now(tz)

    entry_time = now.strftime("%I:%M %p")
    level1 = (now.replace(second=0, microsecond=0)).strftime("%I:%M %p")
    level2 = (now.replace(second=0, microsecond=0)).strftime("%I:%M %p")
    level3 = (now.replace(second=0, microsecond=0)).strftime("%I:%M %p")

    msg = f"""
🤖 AlphaSignalsBot
🚨 SIGNAL ALERT  

📉 {name}
⏰ Expiry: 2 minutes
📍 Entry Time: {entry_time}

📈 Direction: {direction} 🟥
💯 Confidence: 70%

🎯 Martingale Levels:
🔁 Level 1 → {level1}
🔁 Level 2 → {level2}
🔁 Level 3 → {level3}
"""

    last_signal = msg
    print(msg)
    return msg


# =====================
# BOT LOOP (FULL AUTO)
# =====================
def bot_loop():
    while True:
        print("\n🔄 Scanning markets...")

        for symbol, name in ASSETS:
            data = analyze(symbol)

            print(f"Checking {name} | RSI: {data['rsi']} | MACD: {data['macd']}")

            if data["signal"] != "WAIT":
                format_signal(name, data["signal"], data)

        time.sleep(60)  # scan every 1 minute


# =====================
# FLASK ROUTES
# =====================
@app.route("/")
def home():
    return {"status": "AlphaSignalsBot Running 🤖"}

@app.route("/signal")
def signal():
    return {"last_signal": last_signal}

@app.route("/health")
def health():
    return {"bot": "active", "assets": len(ASSETS)}


# =====================
# START BOT THREAD
# =====================
Thread(target=bot_loop, daemon=True).start()


# =====================
# RUN SERVER
# =====================
if __name__ == "__main__":
    print("🚀 FULL AUTO BOT STARTED")
    app.run(host="0.0.0.0", port=10000)
