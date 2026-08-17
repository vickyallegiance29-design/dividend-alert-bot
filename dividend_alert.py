import requests
import json
import os
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

SEEN_FILE = "seen_dividends.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/"
}


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=20
    )

    print("Telegram:", response.status_code)
    return response.ok


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()

    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f)


def check_dividends():
    session = requests.Session()
    session.headers.update(HEADERS)

    session.get(
        "https://www.nseindia.com/",
        timeout=20
    )

    response = session.get(
        "https://www.nseindia.com/api/corporate-announcements",
        params={"index": "equities"},
        timeout=20
    )

    print("NSE response:", response.status_code)

    data = response.json()
    seen = load_seen()

    new_count = 0

    for item in data:

        symbol = item.get("symbol", "").strip()
        subject = item.get("subject", "").strip()
        details = item.get("details", "").strip()
        broadcast = item.get("broadcastDateTime", "").strip()

        combined = f"{subject} {details}".lower()

        if "dividend" not in combined:
            continue

        unique_id = f"{symbol}|{subject}|{broadcast}"

        if unique_id in seen:
            continue

        message = (
            "🚨 DIVIDEND ALERT 🚨\n\n"
            f"🏢 Company/Symbol: {symbol}\n"
            f"📢 Announcement: {subject}\n"
            f"📅 Date: {broadcast}\n\n"
            "🔗 Source: NSE India"
        )

        if send_telegram(message):
            seen.add(unique_id)
            new_count += 1

    save_seen(seen)

    print(f"New dividend alerts: {new_count}")


print(
    "Checking NSE:",
    datetime.now().strftime("%d-%m-%Y %H:%M:%S")
)

try:
    check_dividends()
except Exception as e:
    print("ERROR:", e)
