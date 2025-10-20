import requests
import json
import os

# --- ДОМЕНИ ДЛЯ ПЕРЕВІРКИ ---
DOMAINS = ["common.xyz", "neuko.ai", "monad.xyz"]

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT = os.getenv("TG_CHAT")
SEEN_FILE = "seen.json"


# --- ЗАВАНТАЖЕННЯ ВЖЕ БАЧЕНИХ САБДОМЕНІВ ---
if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "r") as f:
        seen = json.load(f)
else:
    seen = {}


# --- ПЕРЕВІРКА ЧИ САЙТ ЖИВИЙ ---
def is_live(subdomain):
    try:
        resp = requests.head(
            f"https://{subdomain}",
            timeout=5,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        return resp.status_code in [200, 301, 302, 403, 405]
    except requests.RequestException:
        return False


# --- НАДСИЛАННЯ ПОВІДОМЛЕННЯ В TELEGRAM ---
def send_telegram_message(message):
    requests.post(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
        data={
            "chat_id": TG_CHAT,
            "text": message,
            "parse_mode": "HTML",
        },
    )


# --- ЗАПИТ ДО CRT.SH ДЛЯ ОТРИМАННЯ САБДОМЕНІВ ---
def get_subdomains(domain):
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return []
        data = r.json()
        subs = set()
        for entry in data:
            name = entry["name_value"]
            for sub in name.split("\n"):
                sub = sub.strip()
                if sub and not sub.startswith("*"):
                    subs.add(sub)
        return sorted(subs)
    except Exception:
        return []


# --- ОСНОВНА ЛОГІКА ---
for domain in DOMAINS:
    new_subs = get_subdomains(domain)
    old_subs = set(seen.get(domain, []))
    new_found = sorted(set(new_subs) - old_subs)

    if new_found:
        formatted = []
        for s in new_found:
            live = "✅" if is_live(s) else "❌"
            formatted.append(f"{live} {s}")

        msg = (
            f"🌐 <b>{domain}</b> — new subdomain(s) detected:\n\n"
            + "\n".join(formatted)
            + f"\n\n🧩 Total found: {len(new_found)}"
        )

        send_telegram_message(msg)
        seen[domain] = new_subs


# --- ОНОВЛЕННЯ ФАЙЛУ З БАЧЕНИМИ ---
with open(SEEN_FILE, "w") as f:
    json.dump(seen, f, indent=2)
