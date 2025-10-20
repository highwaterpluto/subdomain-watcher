import requests
import time
import os
import json

# 🔧 Налаштування (підставимо трохи пізніше через GitHub Secrets)
DOMAINS = ["common.xyz", "neuko.ai"]
CRT_URL = "https://crt.sh/?q={}&output=json"
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT = os.getenv("TG_CHAT")
DATA_FILE = "seen.json"

def load_seen():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(data):
    with open(DATA_FILE, "w") as f:
        json.dump(list(data), f)

def send_telegram(message):
    if not TG_TOKEN or not TG_CHAT:
        print("⚠️ Telegram not configured")
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TG_CHAT, "text": message})

def check_domains():
    seen = load_seen()
    new = set()

    for domain in DOMAINS:
        try:
            resp = requests.get(CRT_URL.format(domain), timeout=15)
            if resp.status_code == 200:
                entries = resp.json()
                subs = {entry["name_value"] for entry in entries}
                for sub in subs:
                    if sub not in seen:
                        new.add(sub)
        except Exception as e:
            print(f"❌ Error with {domain}: {e}")

    if new:
        message = "🚨 New subdomains found:\n" + "\n".join(sorted(new))
        send_telegram(message)
        seen.update(new)
        save_seen(seen)
    else:
        print("✅ No new subdomains found")

if __name__ == "__main__":
    check_domains()
