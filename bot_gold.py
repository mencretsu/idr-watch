import requests
import os
from datetime import datetime
import pytz

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
METALS_API_KEY = os.environ["METALS_API_KEY"]
CHANNEL_GOLD_IDR = os.environ["CHANNEL_GOLD_IDR"]
GOLD_FILE = "last_rate/gold.txt"


def get_rate(frm, to):
    url = f"https://api.frankfurter.app/latest?from={frm}&to={to}"
    r = requests.get(url, timeout=10)
    return r.json()["rates"][to]


def get_gold_idr_per_gram():
    r = requests.get(
        "https://api.metals.dev/v1/latest",
        params={
            "api_key": METALS_API_KEY,
            "base": "USD",
            "currencies": "XAU",
        },
        timeout=10,
    )
    data = r.json()
    xau_per_usd = data["metals"]["XAU"]
    usd_per_oz = 1 / xau_per_usd
    usd_idr = get_rate("USD", "IDR")
    idr_per_oz = usd_per_oz * usd_idr
    idr_per_gram = idr_per_oz / 31.1035
    return idr_per_gram


def get_last_rate(filepath):
    try:
        with open(filepath) as f:
            return float(f.read().strip())
    except:
        return None


def save_rate(filepath, rate):
    with open(filepath, "w") as f:
        f.write(str(rate))


def send_telegram(channel, msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": channel, "text": msg, "parse_mode": "HTML"})


wib = pytz.timezone("Asia/Jakarta")
now = datetime.now(wib)
os.makedirs("last_rate", exist_ok=True)

try:
    gold_now = get_gold_idr_per_gram()
    gold_last = get_last_rate(GOLD_FILE)

    if gold_last is None:
        save_rate(GOLD_FILE, gold_now)
        print(f"[GOLD] Init: Rp {gold_now:,.0f}/gram")
    else:
        change = gold_now - gold_last
        pct = (change / gold_last) * 100
        emoji = "🔴" if change > 0 else "🟢"
        sign = "+" if change > 0 else ""
        msg = (
            f"{emoji} <b>GOLD/IDR</b> | {sign}{pct:.2f}%\n\n"
            f"Rp {gold_last:,.0f} → Rp {gold_now:,.0f} /gram\n\n"
            f"📆 {now.strftime('%d %b %Y')}"
        )
        print(f"[GOLD] {msg}")
        send_telegram(CHANNEL_GOLD_IDR, msg)
        save_rate(GOLD_FILE, gold_now)

except Exception as e:
    print(f"[GOLD] Error: {e}")
