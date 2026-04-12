import os
import time
import requests
from flask import Flask
from threading import Thread
from tradingview_ta import TA_Handler, Interval
from datetime import datetime
import pytz

app = Flask(__name__)

# ================= ENV =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("❌ Missing BOT_TOKEN or CHAT_ID")

# ================= MARKETS =================
MARKETS = [
    ("EURUSD", "forex"),
    ("GBPUSD", "forex"),
    ("USDJPY", "forex"),
    ("BTCUSDT", "crypto"),
    ("ETHUSDT", "crypto"),
    ("XAUUSD", "forex")  # GOLD
]

COOLDOWN = 120
last_signal_time = {}

# ================= SESSION =================
def is_active_session():
    nigeria = pytz.timezone("Africa/Lagos")
    now = datetime.now(nigeria)
    hour = now.hour

    # London + NY sessions
    return (8 <= hour <= 12) or (13 <= hour <= 18)

# ================= TELEGRAM =================
def send_signal(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
        print("📩 Sent:", message)
    except Exception as e:
        print("❌ Telegram Error:", e)

# ================= ANALYSIS =================
def get_analysis(symbol, market, interval):
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener=market,
            exchange="BINANCE" if market == "crypto" else "FX_IDC",
            interval=interval
        )
        return handler.get_analysis()
    except Exception as e:
        print(f"❌ Error {symbol}:", e)
        return None

# ================= AI SCORE =================
def ai_score(trend, confidence, rsi, volatility):
    score = 0

    if trend in ["STRONG_BUY", "STRONG_SELL"]:
        score += 25
    elif trend in ["BUY", "SELL"]:
        score += 15

    score += int(confidence * 35)

    if 45 <= rsi <= 65:
        score += 20
    elif 35 <= rsi <= 75:
        score += 10

    if volatility > 0.3:
        score += 10

    return score

# ================= AI SIGNAL =================
def ai_signal(symbol, market):
    a1 = get_analysis(symbol, market, Interval.INTERVAL_1_MINUTE)
    a5 = get_analysis(symbol, market, Interval.INTERVAL_5_MINUTES)
    a15 = get_analysis(symbol, market, Interval.INTERVAL_15_MINUTES)

    if not a1 or not a5 or not a15:
        return None

    s1 = a1.summary
    s5 = a5.summary
    s15 = a15.summary

    trend = s15["RECOMMENDATION"]

    buy_power = s1["BUY"] + s5["BUY"]
    sell_power = s1["SELL"] + s5["SELL"]
    total = buy_power + sell_power + s1["NEUTRAL"] + s5["NEUTRAL"]

    confidence = max(buy_power, sell_power) / total

    ind = a1.indicators
    rsi = ind.get("RSI", 50)
    volatility = abs(ind.get("close", 0) - ind.get("open", 0))

    # less strict filter
    if abs(buy_power - sell_power) < 1:
        return None

    # BUY
    if trend in ["BUY", "STRONG_BUY"] and buy_power > sell_power:
        if 35 < rsi < 75:
            score = ai_score(trend, confidence, rsi, volatility)
            return "BUY", confidence, rsi, score

    # SELL
    if trend in ["SELL", "STRONG_SELL"] and sell_power > buy_power:
        if 25 < rsi < 65:
            score = ai_score(trend, confidence, rsi, volatility)
            return "SELL", confidence, rsi, score

    return None

# ================= FORMAT =================
def format_signal(symbol, direction, confidence, rsi, score):
    return f"""
🔥 ELITE MULTI-MARKET SIGNAL

Asset: {symbol}
Direction: {'🟢 BUY' if direction == 'BUY' else '🔴 SELL'}

AI Score: {score}/100
Confidence: {round(confidence*100)}%
RSI: {round(rsi)}

Timeframe: 1M Entry | 15M Trend

⚡ Fast Trade Opportunity
"""

# ================= BOT LOOP =================
def bot_loop():
    print("🚀 ELITE BOT STARTED")
    send_signal("🔥 ELITE BOT IS LIVE")

    while True:
        if not is_active_session():
            print("⏸ Outside trading session")
            time.sleep(60)
            continue

        for symbol, market in MARKETS:
            now = time.time()

            if symbol in last_signal_time and now - last_signal_time[symbol] < COOLDOWN:
                continue

            result = ai_signal(symbol, market)

            if result:
                direction, confidence, rsi, score = result

                print(f"{symbol} | Score:{score} | Conf:{confidence}")

                if score >= 60:
                    msg = format_signal(symbol, direction, confidence, rsi, score)
                    send_signal(msg)
                    last_signal_time[symbol] = now

        time.sleep(15)

# ================= ROUTE =================
@app.route("/")
def home():
    return "🔥 ELITE BOT RUNNING"

# ================= START =================
Thread(target=bot_loop).start()
