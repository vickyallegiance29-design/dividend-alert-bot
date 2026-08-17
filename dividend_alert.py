import requests
import json
import os
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

SEEN_FILE = "seen_dividends.json"
BASELINE_FILE = "baseline_done.txt"

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


def get_nse_announcements():
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

    response.raise_for_status()

    return response.json()


def check_dividends():

    data = get_nse_announcements()

    seen = load_seen()
    found = []

    for item in data:

        symbol = item.get("symbol", "").strip()
        subject = item.get("subject", "").strip()
        details = item.get("details", "").strip()
        broadcast = item.get("broadcastDateTime", "").strip()

        combined = f"{subject} {details}".lower()

        if "dividend" not in combined:
            continue

        unique_id = f"{symbol}|{subject}|{broadcast}"

        found.append(
            (
                unique_id,
                symbol,
                subject,
                details,
                broadcast
            )
        )

    print("Dividend records found:", len(found))

    # First run:
    # Existing announcements ko alert nahi karna.
    # Sirf baseline save karna.
    if not os.path.exists(BASELINE_FILE):

        for unique_id, symbol, subject, details, broadcast in found:
            seen.add(unique_id)

        save_seen(seen)

        with open(BASELINE_FILE, "w", encoding="utf-8") as f:
            f.write("baseline created")

        print("Initial NSE data saved.")
        print("No alerts sent on first run.")

        return

    new_count = 0

    for unique_id, symbol, subject, details, broadcast in found:

        if unique_id in seen:
            continue

        message = (
            "🚨 DIVIDEND ALERT 🚨\n\n"
            f"🏢 Company/Symbol: {symbol}\n\n"
            f"📢 Announcement:\n{subject}\n\n"
            f"📅 Announcement Date:\n{broadcast}\n\n"
            f"📝 Details:\n{details[:1500]}\n\n"
            "🔗 Source: NSE India"
        )

        if send_telegram(message):
            seen.add(unique_id)
            new_count += 1

    save_seen(seen)

    print("New dividend alerts:", new_count)


print("=" * 35)
print("      DIVIDEND ALERT BOT")
print("=" * 35)

print(
    "Checking NSE:",
    datetime.now().strftime("%d-%m-%Y %H:%M:%S")
)

try:
    check_dividends()
except Exception as e:
    print("ERROR:", e)
    raise
