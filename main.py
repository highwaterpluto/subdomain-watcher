import requests
import os
import json

# Налаштування
DOMAINS = ["common.xyz", "neuko.ai", "monad.xyz"]
CRT_URL = "https://crt.sh/?q={}&output=json"
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT = os.getenv("TG_CHAT")
DATA_FILE = "seen.json"


def load_seen():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_seen(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def send_telegram(message):
    if not TG_TOKEN or not TG_CHAT:
        print("⚠️ Telegram not configured")
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TG_CHAT, "text": message})


def check_domains():
    seen = load_seen()
    updated = False

    for domain in DOMAINS:
        try:
            resp = requests.get(CRT_URL.format(domain), timeout=15)
            if resp.status_code != 200:
                print(f"❌ Error loading {domain}")
                continue

            entries = resp.json()
            subs = sorted({entry["name_value"] for entry in entries})
            old = set(seen.get(domain, []))
            new = [s for s in subs if s not in old]

            if new:
                message = f"{domain} — new subdomain(s) found:\n" + "\n".join(new)
                send_telegram(message)
                print(f"🚨 Sent new subs for {domain}: {len(new)} found")
                seen[domain] = subs
                updated = True
            else:
                print(f"✅ No new subs for {domain}")

        except Exception as e:
            print(f"❌ Error with {domain}: {e}")

    if updated:
        save_seen(seen)


if __name__ == "__main__":
    check_domains()
