from flask import Flask
import os
import requests
import time
import threading
from datetime import datetime

app = Flask(__name__)

# ================= ENV VARIABLES =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("❌ Missing BOT_TOKEN or CHAT_ID in environment variables")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


# ================= WEB ROUTE (RENDER CHECK) =================
@app.route("/")
def home():
    return "BOT IS LIVE 🔥"


# ================= SEND MESSAGE FUNCTION =================
def send_message(text):
    try:
        requests.post(API_URL, json={
            "chat_id": CHAT_ID,
            "text": text
        })
    except Exception as e:
        print("Telegram error:", e)


# ================= SIGNAL LOGIC =================
def generate_signal():
    hour = datetime.now().hour

    # Simple working logic (you can upgrade later)
    if 7 <= hour < 12:
        return "📈 MORNING SIGNAL ACTIVE"
    elif 13 <= hour < 18:
        return "📉 AFTERNOON SIGNAL ACTIVE"
    else:
        return None


# ================= BOT LOOP =================
def bot_loop():
    print("🚀 Bot started successfully")

    while True:
        try:
            signal = generate_signal()

            if signal:
                send_message(signal)
                print("Sent:", signal)
            else:
                print("⏳ No active session")

            time.sleep(60)

        except Exception as e:
            print("Loop error:", e)
            time.sleep(10)


# ================= START SERVER =================
if __name__ == "__main__":
    import threading

    threading.Thread(target=bot_loop).start()

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
