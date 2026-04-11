import time, requests, os
from datetime import datetime
from threading import Thread
from flask import Flask
from tradingview_ta import TA_Handler, Interval
import pytz

# ================= APP =================
app = Flask(__name__)

# ================= SETTINGS =================
TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

PAIRS = [
    {"symbol": "EURUSD", "exchange": "OANDA"},
    {"symbol": "GBPUSD", "exchange": "OANDA"},
    {"symbol": "USDJPY", "exchange": "OANDA"},
]

# ================= TIMEZONE =================
TZ = pytz.timezone("Africa/Lagos")

# 🔥 DEBUG SESSION FUNCTION
def in_session():
    now = datetime.now(TZ)
    hour = now.hour

    print("🕒 Nigeria time:", now)  # DEBUG LINE

    morning = (8 <= hour < 12)
    afternoon = (14 <= hour < 18)

    if morning or afternoon:
        print("✅ داخل session (ACTIVE)")
        return True
    else:
        print("⏳ خارج session (WAITING)")
        return False

# ================= SIGNAL =================
pair_index = 0

def generate_signal():
    global pair_index

    pair = PAIRS[pair_index]
    pair_index = (pair_index + 1) % len(PAIRS)

    try:
        handler = TA_Handler(
            symbol=pair["symbol"],
            screener="forex",
            exchange=pair["exchange"],
            interval=Interval.INTERVAL_1_MINUTE
        )

        data = handler.get_analysis().indicators

        ema9 = data.get("EMA9")
        ema21 = data.get("EMA21")
        rsi = data.get("RSI")

        print(f"[DEBUG] {pair['symbol']} EMA9={ema9} EMA21={ema21} RSI={rsi}")

        if ema9 is None or ema21 is None or rsi is None:
            return None

        confidence = int(rsi)

        if ema9 > ema21 and rsi > 50:
            return pair, "BUY 🟩", confidence

        if ema9 < ema21 and rsi < 50:
            return pair, "SELL 🟥", confidence

    except Exception as e:
        print("Signal error:", e)

    return None

# ================= TELEGRAM =================
def send_signal(pair, direction, confidence):
    now = datetime.now(TZ).strftime("%I:%M %p")

    msg = f"""
🔥 SIGNAL ALERT

{pair['symbol']} {direction}

⏰ Time: {now} (NG)
💯 Confidence: {confidence}%
"""

    try:
        requests.get(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            params={"chat_id": CHAT_ID, "text": msg}
        )
    except Exception as e:
        print("Telegram error:", e)

# ================= BOT LOOP =================
def bot_loop():
    while True:
        try:
            if not in_session():
                time.sleep(60)
                continue

            signal = generate_signal()

            print("📊 Signal:", signal)

            if signal:
                pair, direction, confidence = signal
                send_signal(pair, direction, confidence)

            time.sleep(90)

        except Exception as e:
            print("Bot error:", e)
            time.sleep(10)

# ================= ROUTE =================
@app.route('/')
def home():
    return "🔥 ELITE BOT IS LIVE"

# ================= START =================
Thread(target=bot_loop).start()
