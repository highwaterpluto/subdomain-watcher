import requests
import json
import os

DOMAINS = ["common.xyz", "neuko.ai", "monad.xyz"]  # свої домени сюди
IGNORE_PATTERNS = ["test", "staging", "dev", "demo"]  # щоб не спамив “сміттям”

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT = os.getenv("TG_CHAT")
SEEN_FILE = "seen.json"


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return json.load(f)
    return {}


def save_seen(data):
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f, indent=2)


def send_tg_message(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TG_CHAT, "text": text})


def get_subdomains(domain):
    try:
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        r = requests.get(url, timeout=20)
        if r.status_code == 200 and r.text.strip():
            data = r.json()
            return sorted(set(d["name_value"] for d in data))
    except Exception:
        pass
    return []


def check_live(subdomain):
    try:
        r = requests.head(f"http://{subdomain}", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def main():
    seen = load_seen()
    updated_seen = dict(seen)

    for domain in DOMAINS:
        subs = get_subdomains(domain)
        if not subs:
            continue

        old_subs = set(seen.get(domain, []))
        new_subs = [s for s in subs if s not in old_subs]

        # фільтруємо “сміття”
        new_subs = [
            s for s in new_subs
            if not any(bad in s.lower() for bad in IGNORE_PATTERNS)
        ]

        if new_subs:
            updated_seen[domain] = subs

            # перевірка чи живий
            results = []
            for s in new_subs:
                alive = check_live(s)
                mark = "✅" if alive else "❌"
                results.append(f"{mark} {s}")

            message = (
                f"🌐 <b>{domain}</b> — new subdomain(s) detected:\n\n"
                + "\n".join(f"• {r}" for r in results)
                + f"\n\n🧩 Total found: {len(new_subs)}"
            )
            send_tg_message(message)

    save_seen(updated_seen)


if __name__ == "__main__":
    main()
