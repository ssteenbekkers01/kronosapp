import os
import requests

def load_env_file(env_path=".telegram_alerts.env"):
    if not os.path.exists(env_path):
        return

    with open(env_path) as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                os.environ[key] = value


load_env_file()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_alert(message):
    if not TOKEN or not CHAT_ID:
        print("Telegram alerts not configured")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
    }

    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Failed to send alert: {e}")
