import json
import os
import requests
import websocket
from datetime import datetime

DOMAINS = ["common.xyz", "neuko.ai", "monad.xyz", "citrea.xyz"]
SEEN_FILE = "seen.json"

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT = os.getenv("TG_CHAT")

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Завантаження seen.json
if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "r") as f:
        seen = json.load(f)
else:
    seen = {}

def send_message(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"[{now()}] ❌ Telegram error: {e}")

def is_live(subdomain):
    try:
        r = requests.head(f"https://{subdomain}", timeout=4)
        return r.status_code in [200, 301, 302, 403, 405]
    except:
        return False

def handle_new_domain(domain, subdomain):
    old = seen.get(domain, [])
    if subdomain in old:
        return  # вже бачили
    seen[domain] = old + [subdomain]

    live = "✅" if is_live(subdomain) else "❌"
    msg = f"🌐 <b>{domain}</b> — new subdomain detected:\n\n{live} {subdomain}"
    send_message(msg)

    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f, indent=2)

def on_message(ws, message):
    data = json.loads(message)
    if "data" not in data:
        return

    cert = data["data"]
    if "leaf_cert" not in cert:
        return

    all_domains = cert["leaf_cert"].get("all_domains", [])
    for d in all_domains:
        d = d.lower()
        for root in DOMAINS:
            if d.endswith(root) and not d.startswith("*"):
                print(f"[{now()}] 🆕 Found: {d}")
                handle_new_domain(root, d)

def on_error(ws, error):
    print(f"[{now()}] ⚠️ WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"[{now()}] 🔁 Connection closed — reconnecting...")
    start_listener()

def on_open(ws):
    print(f"[{now()}] ✅ Connected to CertStream\nListening for domains: {', '.join(DOMAINS)}")

def start_listener():
    ws = websocket.WebSocketApp(
        "wss://certstream.calidog.io/",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    ws.run_forever()

if __name__ == "__main__":
    print("="*31)
    print("   🌐 REAL-TIME SUBDOMAIN WATCHER (CERTSTREAM)")
    print("="*31)
    start_listener()
