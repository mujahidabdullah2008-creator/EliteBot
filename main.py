import time, sqlite3, requests, random, os
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask, render_template
from tradingview_ta import TA_Handler, Interval

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

# ================= DATABASE =================
conn = sqlite3.connect('trades.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS trades (
id INTEGER PRIMARY KEY AUTOINCREMENT,
symbol TEXT,
direction TEXT,
entry_time TEXT,
result TEXT,
confidence INTEGER,
profit REAL DEFAULT 0
)
''')
conn.commit()

# ================= SESSION =================
def in_session():
    hour = datetime.now().hour
    return (8 <= hour < 12) or (14 <= hour < 18)

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

        print(f"DEBUG {pair['symbol']} EMA9={ema9} EMA21={ema21} RSI={rsi}")

        if ema9 is None or ema21 is None or rsi is None:
            return None

        confidence = int(rsi)

        if ema9 > ema21 and rsi > 50:
            return pair, "BUY", confidence
        if ema9 < ema21 and rsi < 50:
            return pair, "SELL", confidence

    except Exception as e:
        print("Signal error:", e)

    return None

# ================= TELEGRAM =================
def send_signal(pair, direction, confidence):
    msg = f"{pair['symbol']} {direction} | Confidence: {confidence}%"

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
                print("Waiting for session...")
                time.sleep(60)
                continue

            signal = generate_signal()

            print("Signal:", signal)

            if signal:
                pair, direction, confidence = signal
                send_signal(pair, direction, confidence)

            time.sleep(90)

        except Exception as e:
            print("Bot error:", e)
            time.sleep(10)

# ================= ROUTES =================
@app.route('/')
def home():
    return "BOT IS WORKING 🔥"

# ================= RUN =================
Thread(target=bot_loop).start()
