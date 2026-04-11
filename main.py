import os
import time
import requests
from flask import Flask
from tradingview_ta import TA_Handler, Interval

app = Flask(__name__)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY"]
TIMEFRAME = Interval.INTERVAL_1_MINUTE

# ================= TELEGRAM =================
def send_signal(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Missing BOT_TOKEN or CHAT_ID")
        return
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram Error:", e)

# ================= ANALYSIS =================
def get_signal(symbol):
    try:
        handler = TA_Handler(
            symbol=symbol,
            screener="forex",
            exchange="FX_IDC",
            interval=TIMEFRAME
        )
        
        analysis = handler.get_analysis()
        recommendation = analysis.summary["RECOMMENDATION"]
        
        return recommendation
    except:
        return None

# ================= BOT LOOP =================
def bot_loop():
    print("🚀 Bot started...")
    
    while True:
        for symbol in SYMBOLS:
            signal = get_signal(symbol)
            
            if signal == "BUY":
                msg = f"🟢 BUY SIGNAL\nPair: {symbol}\nTimeframe: 1M"
                send_signal(msg)
            
            elif signal == "SELL":
                msg = f"🔴 SELL SIGNAL\nPair: {symbol}\nTimeframe: 1M"
                send_signal(msg)
        
        time.sleep(60)

# ================= FLASK ROUTE =================
@app.route("/")
def home():
    return "✅ Bot is running!"

# ================= START =================
if __name__ == "__main__":
    from threading import Thread
    
    Thread(target=bot_loop).start()
    
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
