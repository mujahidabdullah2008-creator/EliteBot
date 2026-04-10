import time, sqlite3, requests, random, os
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask, render_template
from tradingview_ta import TA_Handler, Interval
import pytz

# ================= SETTINGS =================
TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

PAIRS = [
    {"symbol": "EURUSD", "exchange": "OANDA", "flag1": "🇪🇺", "flag2": "🇺🇸"},
    {"symbol": "GBPUSD", "exchange": "OANDA", "flag1": "🇬🇧", "flag2": "🇺🇸"},
    {"symbol": "USDJPY", "exchange": "OANDA", "flag1": "🇺🇸", "flag2": "🇯🇵"},
    {"symbol": "AUDUSD", "exchange": "OANDA", "flag1": "🇦🇺", "flag2": "🇺🇸"},
    {"symbol": "NZDUSD", "exchange": "OANDA", "flag1": "🇳🇿", "flag2": "🇺🇸"},
]

# ================= OTC SESSION =================
OTC_TZ = pytz.timezone("America/New_York")

def in_session():
    hour = datetime.now(OTC_TZ).hour
    return (3 <= hour < 12) or (8 <= hour < 17)

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
level1 TEXT,
level2 TEXT,
level3 TEXT,
profit REAL DEFAULT 0
)
''')
conn.commit()

# ================= SIGNAL ENGINE (ANTI-429) =================
pair_index = 0  # rotate pairs

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

        analysis = handler.get_analysis()
        data = analysis.indicators

        ema9 = data.get("EMA9")
        ema21 = data.get("EMA21")
        rsi = data.get("RSI")

        if not ema9 or not ema21 or not rsi:
            return None

        confidence = int(rsi)

        if ema9 > ema21 and rsi > 55:
            return pair, "BUY 🟩", confidence

        elif ema9 < ema21 and rsi < 45:
            return pair, "SELL 🟥", confidence

    except Exception as e:
        print("Signal error:", e)
        time.sleep(10)  # pause if TradingView blocks

    return None

# ================= TELEGRAM =================
def send_signal(pair, direction, confidence):
    now = datetime.now(OTC_TZ)

    entry = now.strftime("%I:%M %p")
    l1 = (now + timedelta(minutes=2)).strftime("%I:%M %p")
    l2 = (now + timedelta(minutes=4)).strftime("%I:%M %p")
    l3 = (now + timedelta(minutes=6)).strftime("%I:%M %p")

    msg = f"""
🔥 SIGNAL ALERT

{pair['flag1']} {pair['symbol']} {pair['flag2']}
📈 {direction}

⏰ Entry: {entry} OTC
💯 Confidence: {confidence}%

🎯 Martingale:
🔁 {l1}
🔁 {l2}
🔁 {l3}
"""

    try:
        requests.get(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            params={"chat_id": CHAT_ID, "text": msg}
        )
    except Exception as e:
        print("Telegram error:", e)

# ================= SAVE =================
def save_trade(pair, direction, confidence):
    now = datetime.now(OTC_TZ)

    entry = now.strftime("%I:%M %p")
    l1 = (now + timedelta(minutes=2)).strftime("%I:%M %p")
    l2 = (now + timedelta(minutes=4)).strftime("%I:%M %p")
    l3 = (now + timedelta(minutes=6)).strftime("%I:%M %p")

    cursor.execute("""
    INSERT INTO trades (symbol, direction, entry_time, result, confidence, level1, level2, level3)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (pair["symbol"], direction, entry, "PENDING", confidence, l1, l2, l3))

    conn.commit()
    return cursor.lastrowid

# ================= RESULT =================
def update_trade(trade_id):
    result = random.choice(["WIN", "LOSS"])
    profit = 10 if result == "WIN" else -5

    cursor.execute(
        "UPDATE trades SET result=?, profit=? WHERE id=?",
        (result, profit, trade_id)
    )
    conn.commit()

# ================= BOT LOOP =================
def bot_loop():
    while True:
        try:
            if not in_session():
                print("Waiting for OTC session...")
                time.sleep(60)
                continue

            signal = generate_signal()

            if signal:
                pair, direction, confidence = signal
                send_signal(pair, direction, confidence)
                trade_id = save_trade(pair, direction, confidence)

                time.sleep(120)
                update_trade(trade_id)

            time.sleep(90)  # 🔥 MAIN DELAY (ANTI-429)

        except Exception as e:
            print("Bot error:", e)
            time.sleep(10)

# ================= FLASK =================
app = Flask(__name__)

@app.route('/')
def dashboard():
    cursor.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 50")
    trades = cursor.fetchall()

    wins = len([t for t in trades if t[4] == "WIN"])
    losses = len([t for t in trades if t[4] == "LOSS"])
    total_profit = sum([t[9] for t in trades])

    return render_template("dashboard.html", trades=trades, wins=wins, losses=losses, total_profit=total_profit)

# ================= RUN =================
if __name__ == "__main__":
    Thread(target=bot_loop).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))