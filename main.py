import requests
import json
import time
import os

# ====== CONFIG ======
DOMAINS = ["monad.xyz", "common.xyz", "pharosnetwork.xyz"]
SEEN_FILE = "seen.json"

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT = os.getenv("TG_CHAT")

# ====== FUNCTIONS ======
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {"chat_id": TG_CHAT, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_subdomains(domain):
    try:
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        response = requests.get(url, timeout=20)
        data = response.json()
        subs = {entry["name_value"].lower() for entry in data if domain in entry["name_value"]}
        clean = sorted(set(s.replace("*.", "") for s in subs))
        return clean
    except Exception as e:
        print(f"Error fetching {domain}: {e}")
        return []

def is_live(subdomain):
    try:
        res = requests.head(f"https://{subdomain}", timeout=5)
        return res.status_code < 400
    except:
        return False

# ====== MAIN LOOP ======
if not os.path.exists(SEEN_FILE):
    seen = {}
else:
    with open(SEEN_FILE, "r") as f:
        try:
            seen = json.load(f)
        except:
            seen = {}

print("🚀 Subdomain watcher started on Render...")

while True:
    for domain in DOMAINS:
        print(f"🔍 Checking {domain}...")
        new_subs = get_subdomains(domain)
        old_subs = set(seen.get(domain, []))
        new_found = sorted(set(new_subs) - old_subs)

        if new_found:
            formatted = []
            for s in new_found:
                live = "✅" if is_live(s) else "❌"
                formatted.append(f"{live} {s}")

            msg = (
                f"🌐 {domain} — new subdomain(s) detected:\n\n"
                + "\n".join(formatted)
                + f"\n\n🧩 Total found: {len(new_found)}"
            )

            send_telegram_message(msg)
            seen[domain] = new_subs

    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f, indent=2)

    print("⏳ Sleeping for 5 minutes...\n")
    time.sleep(300)
