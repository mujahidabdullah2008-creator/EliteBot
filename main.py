import time
import requests
import os
from tradingview_ta import TA_Handler, Interval

# =========================
# CONFIG (SECURE)
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise Exception("❌ BOT_TOKEN or CHAT_ID missing")

print("✅ Config loaded successfully")

# =========================
# TELEGRAM FUNCTION
# =========================
def send_signal(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
        print("📤 Signal sent")
    except Exception as e:
        print("❌ Telegram Error:", e)

# =========================
# SETTINGS
# =========================
PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "EURJPY"]
INTERVAL = Interval.INTERVAL_1_MINUTE

# =========================
# ANALYSIS
# =========================
def analyze_pair(pair):
    try:
        print(f"🔍 Checking {pair}")

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

        # CALL CONDITIONS
        if rsi < 35:
            score_call += 2
        if macd > signal:
            score_call += 2
        if close > ema50:
            score_call += 1

        # PUT CONDITIONS
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
        print(f"❌ Error on {pair}: {e}")
        return None, None

# =========================
# MAIN ENGINE
# =========================
def run_bot():
    print("🚀 ELITE AI ENGINE STARTED")

    while True:
        print("🔄 SCANNING MARKET...\n")

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

⚡ Strategy: AI Multi-Indicator
💰 Martingale: x2 optional
"""
                print(f"✅ SIGNAL FOUND: {pair} {signal}")
                send_signal(message)

        print("⏳ Waiting 60 seconds...\n")
        time.sleep(60)

# =========================
# START BOT (IMPORTANT)
# =========================
if __name__ == "__main__":
    run_bot()
