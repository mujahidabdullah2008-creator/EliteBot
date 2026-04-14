from flask import Flask
import threading
import time
import requests
import os
from tradingview_ta import TA_Handler, Interval

app = Flask(__name__)

# =========================
# SECURE CONFIG (NO HARDCODE)
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("❌ BOT_TOKEN or CHAT_ID not set")

print("✅ Telegram config loaded")

# =========================
# TELEGRAM FUNCTION
# =========================
def send_signal(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
        print("📤 Signal sent to Telegram")
    except Exception as e:
        print("❌ Telegram Error:", e)

# =========================
# SETTINGS
# =========================
PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "EURJPY"]
INTERVAL = Interval.INTERVAL_1_MINUTE

# =========================
# ANALYSIS ENGINE
# =========================
def analyze_pair(pair):
    try:
        print(f"🔍 Analyzing {pair}...")

        handler = TA_Handler(
            symbol=pair,
            screener="forex",
            exchange="FX_IDC",
            interval=INTERVAL
        )

        analysis = handler.get_analysis()
        ind = analysis.indicators

        rsi = ind.get("RSI", 50)
        macd = ind.get("MACD.macd", 0)
        signal = ind.get("MACD.signal", 0)
        ema50 = ind.get("EMA50", 0)
        close = ind.get("close", 0)

        print(f"{pair} | RSI:{rsi:.2f} MACD:{macd:.2f}")

        score_call = 0
        score_put = 0

        # CALL LOGIC
        if rsi < 35:
            score_call += 2
        if macd > signal:
            score_call += 2
        if close > ema50:
            score_call += 1

        # PUT LOGIC
        if rsi > 65:
            score_put += 2
        if macd < signal:
            score_put += 2
        if close < ema50:
            score_put += 1

        if score_call >= 4:
            return "CALL", rsi

        if score_put >= 4:
            return "PUT", rsi

        return None, rsi

    except Exception as e:
        print(f"❌ Error analyzing {pair}:", e)
        return None, None

# =========================
# MAIN ENGINE LOOP
# =========================
def run_engine():
    print("🚀 ELITE AI SIGNAL ENGINE STARTED")

    while True:
        print("🔄 NEW SCAN STARTED")

        for pair in PAIRS:
            signal, rsi = analyze_pair(pair)

            if signal:
                message = f"""
📊 ELITE AI SIGNAL

Pair: {pair}
Direction: {signal}
RSI: {round(rsi,2)}

Timeframe: 1 MIN
Entry: Immediate

⚡ Strategy: Multi-Indicator AI
💰 Martingale: x2 optional
"""
                print(f"✅ SIGNAL: {pair} {signal}")
                send_signal(message)

        print("⏳ Waiting 60 seconds...\n")
        time.sleep(60)

# =========================
# START ENGINE THREAD
# =========================
threading.Thread(target=run_engine, daemon=True).start()

# =========================
# KEEP RENDER ALIVE
# =========================
@app.route('/')
def home():
    return "BOT IS LIVE"
