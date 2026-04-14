import os
import time
import threading
import requests
from flask import Flask
from tradingview_ta import TA_Handler, Interval

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY"]
INTERVAL = Interval.INTERVAL_1_MINUTE

app = Flask(__name__)

# =============== TELEGRAM =================
def send_signal(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=data)
    except:
        print("❌ Telegram Error")

# =============== STRATEGY =================
def get_signal(symbol):
    try:
        analysis = TA_Handler(
            symbol=symbol,
            screener="forex",
            exchange="FX_IDC",
            interval=INTERVAL
        ).get_analysis()

        rsi = analysis.indicators["RSI"]
        macd = analysis.indicators["MACD.macd"]
        macd_signal = analysis.indicators["MACD.signal"]

        print(f"📊 {symbol} | RSI: {rsi:.2f} | MACD: {macd:.5f}")

        if rsi < 30 and macd > macd_signal:
            return "BUY"
        elif rsi > 70 and macd < macd_signal:
            return "SELL"
        else:
            return None

    except Exception as e:
        print(f"❌ Error {symbol}: {e}")
        return None

# =============== ENGINE =================
def engine():
    print("🚀 ELITE LIVE SIGNAL ENGINE STARTED")

    while True:
        print("🔄 Scanning markets...")

        for symbol in SYMBOLS:
            signal = get_signal(symbol)

            if signal:
                message = f"""
🚨 LIVE SIGNAL 🚨

PAIR: {symbol}
DIRECTION: {signal}
TIMEFRAME: 1M

⚡ Enter immediately
                """

                print(message)
                send_signal(message)

            time.sleep(2)

        time.sleep(10)

# =============== THREAD =================
def start_engine():
    thread = threading.Thread(target=engine)
    thread.daemon = True
    thread.start()

# =============== ROUTE =================
@app.route("/")
def home():
    return "BOT IS LIVE"

# =============== START =================
start_engine()
