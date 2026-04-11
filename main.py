import time
import sqlite3
import requests
import random
import os
from datetime import datetime
from threading import Thread

from flask import Flask, render_template
from tradingview_ta import TA_Handler, Interval
import pytz

# ================= ENV =================
TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# ================= PAIRS =================
PAIRS = [
    {"symbol": "EURUSD", "exchange": "OANDA", "flag1": "🇪🇺", "flag2": "🇺🇸"},
    {"symbol": "GBPUSD", "exchange": "OANDA", "flag1": "🇬🇧", "flag2": "🇺🇸"},
    {"symbol": "USDJPY", "exchange": "OANDA", "flag1": "🇺🇸", "flag2": "🇯🇵"},
    {"symbol": "AUDUSD", "exchange": "OANDA", "flag1": "🇦🇺", "flag2": "🇺🇸"},
]

# ================= TIMEZONE =================
TZ = pytz.timezone("Africa/Lagos")

def in_session():
    hour = datetime.now(TZ).hour
    return (8 <= hour < 12) or (14 <= hour < 18)

# ================= DB =================
conn = sqlite3.connect("trades.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS trades (
id INTEGER PRIMARY KEY AUTOINCREMENT,
symbol TEXT,
direction TEXT,
entry_time TEXT,
result TEXT,
confidence INTEGER,
profit REAL DEFAULT 0
)
""")
conn.commit()

# ================= SIGNAL ENGINE =================
pair_index = 0

def fetch_data(pair):
    try:
        handler = TA_Handler(
            symbol=pair["symbol"],
            screener="forex",
            exchange=pair["exchange"],
            interval=Interval.INTERVAL_1_MINUTE
        )
        return handler.get_analysis().indicators
    except:
        time.sleep(10)
        return None


def generate_signal():
    global pair_index

    pair = PAIRS[pair_index]
    pair_index = (pair_index + 1) % len(PAIRS)

    data = fetch_data(pair)

    if not data:
        return None

    ema9 = data.get("EMA9")
    ema21 = data.get("EMA21")
    rsi = data.get("RSI")

    if ema9 is None or ema21 is None or rsi is None:
        return None

    confidence = int(rsi)

    if ema9 > ema21:
        return pair, "BUY 🟩", confidence

    if ema9 < ema21:
        return pair, "SELL 🟥", confidence

    return None

# ================= TELEGRAM =================
def send_signal(pair, direction, confidence):
    now = datetime.now(TZ)

    message = f"""
🔥 SIGNAL ALERT

{pair['flag1']} {pair['symbol']} {pair['flag2']}
📊 Direction: {direction}

⏰ Time: {now.strftime('%I:%M %p')}
💯 Confidence: {confidence}%
"""

    try:
        requests.get(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            params={"chat_id": CHAT_ID, "text": message}
        )
    except Exception as e:
        print("Telegram error:", e)

# ================= SAVE =================
def save_trade(pair, direction, confidence):
    now = datetime.now(TZ)

    cursor.execute("""
    INSERT INTO trades (symbol, direction, entry_time, result, confidence)
    VALUES (?, ?, ?, ?, ?)
    """, (pair["symbol"], direction, now.strftime("%I:%M %p"), "PENDING", confidence))

    conn.commit()

# ================= BOT LOOP =================
def bot_loop():
    while True:
        try:
            print("🔥 Bot running...")

            if not in_session():
                print("⏳ Waiting for session...")
                time.sleep(60)
                continue

            signal = generate_signal()

            if signal:
                pair, direction, confidence = signal

                print(f"📊 {pair['symbol']} {direction} {confidence}%")

                send_signal(pair, direction, confidence)
                save_trade(pair, direction, confidence)

                time.sleep(120)
            else:
                print("⚠️ No signal")

            time.sleep(25)

        except Exception as e:
            print("❌ Error:", e)
            time.sleep(10)

# ================= FLASK =================
app = Flask(__name__)

@app.route("/")
def dashboard():
    cursor.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 50")
    trades = cursor.fetchall()

    wins = len([t for t in trades if t[4] == "WIN"])
    losses = len([t for t in trades if t[4] == "LOSS"])

    return render_template(
        "dashboard.html",
        trades=trades,
        wins=wins,
        losses=losses
    )

# ================= RUN =================
if __name__ == "__main__":
    Thread(target=bot_loop).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
