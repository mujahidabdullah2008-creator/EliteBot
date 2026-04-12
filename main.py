import os
import time
import requests
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta
import pytz
from tradingview_ta import TA_Handler, Interval

app = Flask(__name__)

# ================= ENV =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ================= MARKETS =================
MARKETS = [
    ("EURUSD", "forex", "🇪🇺 🇺🇸 EUR/USD"),
    ("GBPUSD", "forex", "🇬🇧 🇺🇸 GBP/USD"),
    ("USDJPY", "forex", "🇺🇸 🇯🇵 USD/JPY"),
    ("BTCUSDT", "crypto", "₿ BTC/USDT"),
    ("ETHUSDT", "crypto", "Ξ ETH/USDT"),
    ("XAUUSD", "forex", "🥇 GOLD (XAU/USD)")
]

# ================= STATE =================
last_signal_time = {}
last_trend = {}
martingale_step = {}  # 🔥 LEVEL 5 ENGINE
COOLDOWN = 120

# ================= TIME =================
def now_ng():
    return datetime.now(pytz.timezone("Africa/Lagos"))

# ================= TELEGRAM =================
def send_signal(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print("Telegram error:", e)

# ================= ANALYSIS =================
def get_analysis(symbol, market_type):
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener="forex" if market_type == "forex" else "crypto",
            exchange="FX_IDC" if market_type == "forex" else "BINANCE",
            interval=Interval.INTERVAL_1_MINUTE
        )
        return handler.get_analysis()
    except:
        return None

# ================= CORE SIGNAL ENGINE =================
def evaluate(symbol, market_type):
    a = get_analysis(symbol, market_type)
    if not a:
        return None

    s = a.summary
    rsi = a.indicators.get("RSI", 50)

    buy = s.get("BUY", 0)
    sell = s.get("SELL", 0)
    total = buy + sell + s.get("NEUTRAL", 0)

    if total == 0:
        return None

    confidence = max(buy, sell) / total

    if confidence < 0.63:
        return None

    if buy > sell and rsi < 70:
        return "BUY", confidence, rsi

    if sell > buy and rsi > 30:
        return "SELL", confidence, rsi

    return None

# ================= SMART MARTINGALE CHECK =================
def martingale_allowed(symbol, direction, confidence, rsi):
    """
    🔥 LEVEL 5 LOGIC:
    Only allow re-entry if trend is STILL STRONG
    """

    # weak market → block martingale
    if confidence < 0.66:
        return False

    # BUY rules
    if direction == "BUY":
        if rsi > 72:  # overbought reversal risk
            return False

    # SELL rules
    if direction == "SELL":
        if rsi < 28:  # oversold reversal risk
            return False

    return True

# ================= FORMAT =================
def format_signal(name, direction, confidence, rsi, step=0):
    now = now_ng()
    entry = now.strftime("%I:%M %p")

    return f"""
🤖 AlphaSignalsBot (LEVEL 5 GOD MODE)
🚨 SIGNAL ALERT  

📉 {name}
⏰ Expiry: 2 minutes
📍 Entry Time: {entry}

📈 Direction: {direction} {"🟢" if direction=='BUY' else '🟥'}
💯 Confidence: {int(confidence*100)}%
📉 RSI: {round(rsi)}

🔁 Martingale Step: {step}
⚡ Smart Re-entry Enabled
"""

# ================= BOT LOOP (LEVEL 5 ENGINE) =================
def bot():
    print("🚀 LEVEL 5 GOD MODE ACTIVE")
    send_signal("🤖 LEVEL 5 GOD MODE LIVE 🚀")

    while True:
        for symbol, market, name in MARKETS:

            now = time.time()

            if symbol in last_signal_time and now - last_signal_time[symbol] < COOLDOWN:
                continue

            result = evaluate(symbol, market)

            if result:
                direction, confidence, rsi = result

                # 🔥 NEW TREND = RESET MARTINGALE
                if symbol not in last_trend or last_trend[symbol] != direction:
                    martingale_step[symbol] = 0

                last_trend[symbol] = direction

                # 🔁 MARTINGALE RE-ENTRY LOGIC
                step = martingale_step.get(symbol, 0)

                if step == 0:
                    send_signal(format_signal(name, direction, confidence, rsi, step=1))
                    martingale_step[symbol] = 1
                    last_signal_time[symbol] = now
                    continue

                # STEP 1 → STEP 2 → STEP 3 (SMART CHECK)
                if step < 3:
                    if martingale_allowed(symbol, direction, confidence, rsi):
                        send_signal(format_signal(name, direction, confidence, rsi, step=step+1))
                        martingale_step[symbol] += 1
                        last_signal_time[symbol] = now

        time.sleep(15)

# ================= FLASK =================
@app.route("/")
def home():
    return "🤖 LEVEL 5 GOD MODE ACTIVE"

# ================= START =================
Thread(target=bot).start()
