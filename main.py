import requests
import json
import os
import time
from datetime import datetime

# --- CONFIG ---
DOMAINS = ["common.xyz", "neuko.ai", "monad.xyz", "citrea.xyz"]
SEEN_FILE = "seen.json"

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT = os.getenv("TG_CHAT")

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- Завантаження seen.json ---
if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "r") as f:
        seen = json.load(f)
else:
    seen = {}

# --- Відправка повідомлення в Telegram ---
def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        payload = {"chat_id": TG_CHAT, "text": text, "parse_mode": "HTML"}
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"[{now()}] ❌ Telegram error: {e}")

# --- Перевірка, чи сайт живий ---
def is_live(subdomain):
    try:
        r = requests.head(f"https://{subdomain}", timeout=5)
        return r.status_code in [200, 301, 302, 403, 405]
    except:
        return False

# --- Основна функція отримання сабдоменів ---
def fetch_subdomains(domain):
    crt_url = f"https://crt.sh/?q=%25.{domain}&output=json"
    proxy_url = f"https://api.allorigins.win/get?url={crt_url}"

    try:
        r = requests.get(proxy_url, timeout=20)
        if r.status_code != 200:
            print(f"[{now()}] ⚠️ Proxy returned {r.status_code} for {domain}")
            return []

        data = r.json()
        if "contents" not in data:
            print(f"[{now()}] ⚠️ No contents in response for {domain}")
            return []

        try:
            json_data = json.loads(data["contents"])
        except json.JSONDecodeError:
            print(f"[{now()}] ⚠️ Could not parse JSON for {domain}")
            return []

        subs = set()
        for entry in json_data:
            if "name_value" in entry:
                for s in entry["name_value"].split("\n"):
                    s = s.strip()
                    if s and not s.startswith("*"):
                        subs.add(s)
        print(f"[{now()}] ✅ Found {len(subs)} total subdomains for {domain}")
        return sorted(subs)
    except Exception as e:
        print(f"[{now()}] ⚠️ Error fetching {domain}: {e}")
        return []

# --- Основний запуск ---
print("="*31)
print("   🛰️ SUBDOMAIN WATCHER STARTED (GitHub Proxy Mode)")
print("="*31)
print(f"🕒 {now()} | Domains loaded: {len(DOMAINS)}\n")

for domain in DOMAINS:
    print(f"🌐 Checking domain: {domain} ...")
    subs = fetch_subdomains(domain)
    if not subs:
        print(f"⚠️ No data for {domain}")
        continue

    old = set(seen.get(domain, []))
    new = sorted(set(subs) - old)

    if new:
        msg = [f"🌐 <b>{domain}</b> — new subdomain(s) detected:\n"]
        for s in new:
            icon = "✅" if is_live(s) else "❌"
            msg.append(f"{icon} {s}")
        msg.append(f"\n🧩 Total found: {len(new)}")

        send_message("\n".join(msg))
        seen[domain] = subs
    else:
        print(f"ℹ️ No new subdomains for {domain}")

# --- Зберігаємо seen.json ---
with open(SEEN_FILE, "w") as f:
    json.dump(seen, f, indent=2)

print(f"\n✅ [{now()}] Scan complete.")
