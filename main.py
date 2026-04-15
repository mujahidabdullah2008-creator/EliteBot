import time
import requests
import os
from tradingview_ta import TA_Handler, Interval

print("✅ Bot booting...")

# =========================
# ENV VARIABLES (RENDER SAFE)
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise Exception("❌ BOT_TOKEN or CHAT_ID missing")

# Prevent duplicate signals
LAST_SIGNAL = {}

# =========================
# TELEGRAM FUNCTION
# =========================
def send_signal(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(
            url,
            data={"chat_id": CHAT_ID, "text": message},
            timeout=10
        )
        print("📤 Signal sent")
    except Exception as e:
        print("❌ Telegram Error:", e)

# =========================
# PAIRS TO SCAN (15 pairs)
# =========================
PAIRS = [
    "EURUSD","GBPUSD","USDJPY","AUDUSD","EURJPY",
    "GBPJPY","EURGBP","USDCAD","USDCHF","AUDJPY",
    "NZDUSD","CADJPY","GBPCHF","EURAUD","AUDCAD"
]

INTERVAL = Interval.INTERVAL_1_MINUTE

# =========================
# MARKET ANALYSIS
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

        # Safe indicator loading
        rsi = ind.get("RSI") or 50
        macd = ind.get("MACD.macd") or 0
        macd_signal = ind.get("MACD.signal") or 0
        ema20 = ind.get("EMA20") or 0
        ema50 = ind.get("EMA50") or 0
        close = ind.get("close") or 0

        print(f"{pair} | RSI:{rsi:.2f} MACD:{macd:.2f}")

        score_call = 0
        score_put = 0

        # ===== CALL CONDITIONS (RELAXED) =====
        if rsi < 45:
            score_call += 1
        if macd > macd_signal:
            score_call += 1
        if close > ema20:
            score_call += 1
        if close > ema50:
            score_call += 1

        # ===== PUT CONDITIONS (RELAXED) =====
        if rsi > 55:
            score_put += 1
        if macd < macd_signal:
            score_put += 1
        if close < ema20:
            score_put += 1
        if close < ema50:
            score_put += 1

        print(f"{pair} Scores -> CALL:{score_call} PUT:{score_put}")

        # Strong signals 🔥
        if score_call >= 3:
            return "CALL 🔥", rsi
        if score_put >= 3:
            return "PUT 🔥", rsi

        # Weak signals
        if score_call >= 2:
            return "CALL", rsi
        if score_put >= 2:
            return "PUT", rsi

        return None, rsi

    except Exception as e:
        print(f"❌ Error on {pair}: {e}")
        return None, None

# =========================
# MAIN ENGINE (RENDER SAFE)
# =========================
def run_bot():
    print("🚀 ELITE AI ENGINE STARTED")
    send_signal("🤖 Forex bot started successfully")

    while True:
        try:
            print("🔄 SCANNING MARKET...\n")

            for pair in PAIRS:
                signal, rsi = analyze_pair(pair)

                # Send only new signals
                if signal and LAST_SIGNAL.get(pair) != signal:
                    LAST_SIGNAL[pair] = signal

                    message = (
                        "📊 ELITE AI SIGNAL\n\n"
                        f"Pair: {pair}\n"
                        f"Direction: {signal}\n"
                        f"RSI: {round(rsi,2)}\n\n"
                        "Timeframe: 1 MIN\n"
                        "Entry: Immediate\n\n"
                        "⚡ Strategy: Multi-Indicator\n"
                        "💰 Martingale: x2 optional"
                    )

                    print(f"✅ SIGNAL FOUND: {pair} {signal}")
                    send_signal(message)

                # Anti TradingView rate-limit
                time.sleep(2)

            print("⏳ Waiting 60 seconds...\n")
            time.sleep(60)

        except Exception as e:
            print("🔥 MAIN LOOP ERROR:", e)
            time.sleep(30)

# =========================
# START BOT
# =========================
if __name__ == "__main__":
    run_bot()
