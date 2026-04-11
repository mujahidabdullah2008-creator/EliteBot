from flask import Flask
import os
import requests
import time
from datetime import datetime

app = Flask(__name__)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


# ================= FLASK ROUTE =================
@app.route("/")
def home():
    return "BOT IS LIVE 🔥"


# ================= SEND MESSAGE FUNCTION =================
def send_message(text):
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    try:
        requests.post(TELEGRAM_URL, json=payload)
    except Exception as e:
        print("Error sending message:", e)


# ================= SIGNAL LOGIC (FIXED) =================
def get_signal():
    now = datetime.now()

    hour = now.hour

    # SIMPLE SESSION FIX (NO MORE WRONG TIME)
    if 8 <= hour < 12:
        return "📈 MORNING SESSION SIGNAL"
    elif 14 <= hour < 18:
        return "📉 AFTERNOON SESSION SIGNAL"
    else:
        return None


# ================= BOT LOOP =================
def bot_loop():
    print("Bot started...")

    while True:
        try:
            signal = get_signal()

            if signal:
                send_message(signal)
                print("Signal sent:", signal)
            else:
                print("No active session right now")

            time.sleep(60)  # check every minute

        except Exception as e:
            print("Loop error:", e)
            time.sleep(10)


# ================= START BOT =================
if __name__ == "__main__":
    import threading
    threading.Thread(target=bot_loop).start()

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))import os
import time
import requests
from flask import Flask
from datetime import datetime
import pytz
import threading

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # put in Render ENV
CHAT_ID = os.getenv("CHAT_ID")      # put in Render ENV

app = Flask(__name__)

# ================= TELEGRAM SEND =================
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    requests.post(url, data=payload)

# ================= SESSION CHECK =================
def in_session():
    nigeria = pytz.timezone("Africa/Lagos")
    now = datetime.now(nigeria)
    hour = now.hour

    # OTC session logic
    if 8 <= hour < 12 or 14 <= hour < 18:
        return True
    return False

# ================= SIGNAL ENGINE (DUMMY FOR NOW) =================
def generate_signal():
    return "📊 SIGNAL: BUY EURUSD 🔥 (demo)"

# ================= BOT LOOP =================
def bot_loop():
    while True:
        try:
            if not in_session():
                print("Waiting for session...")
                time.sleep(60)
                continue

            signal = generate_signal()
            print("Sending signal:", signal)
            send_message(signal)

            time.sleep(300)  # every 5 minutes

        except Exception as e:
            print("Error:", e)
            time.sleep(10)

# ================= FLASK ROUTE =================
@app.route("/")
def home():
    return "BOT IS LIVE 🔥"

# ================= START BACKGROUND THREAD =================
threading.Thread(target=bot_loop, daemon=True).start()
