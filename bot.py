import requests
import os
from datetime import datetime
import pytz

PAIRS = [
    {
        "from": "USD", "to": "IDR",
        "channel": os.environ["CHANNEL_USD_IDR"],
        "file": "last_rate/usd.txt",
        "threshold": 20,  # was 45 — USD/IDR gerak 20-50/hari normal
    },
    {
        "from": "CNY", "to": "IDR",
        "channel": os.environ["CHANNEL_CNY_IDR"],
        "file": "last_rate/cny.txt",
        "threshold": 5,   # was 10
    },
    {
        "from": "SGD", "to": "IDR",
        "channel": os.environ["CHANNEL_SGD_IDR"],
        "file": "last_rate/sgd.txt",
        "threshold": 10,  # was 20
    },
    {
        "from": "JPY", "to": "IDR",
        "channel": os.environ["CHANNEL_JPY_IDR"],
        "file": "last_rate/jpy.txt",
        "threshold": 0.5, # was 1
    },
    {
        "from": "EUR", "to": "IDR",
        "channel": os.environ["CHANNEL_EUR_IDR"],
        "file": "last_rate/eur.txt",
        "threshold": 30,  # was 60
    },
    {
        "from": "MYR", "to": "IDR",
        "channel": os.environ["CHANNEL_MYR_IDR"],
        "file": "last_rate/myr.txt",
        "threshold": 10,  # was 20
    },
]

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

def get_rate(frm, to):
    url = f"https://api.frankfurter.app/latest?from={frm}&to={to}"
    r = requests.get(url, timeout=10)
    return r.json()["rates"][to]

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
for pair in PAIRS:
    frm, to = pair["from"], pair["to"]
    rate_now = get_rate(frm, to)
    rate_last = get_last_rate(pair["file"])

    if rate_last is None:
        save_rate(pair["file"], rate_now)
        continue

    change = rate_now - rate_last
    pct = (change / rate_last) * 100

    if abs(change) >= pair["threshold"]:
        emoji = "🔴" if change > 0 else "🟢"
        sign = "+" if change > 0 else ""
        msg = (
            f"{emoji} <b>{frm}/{to} </b>[ {sign}{pct:.2f}% ]\n\n"
            f"Rp {rate_last:,.0f} → Rp {rate_now:,.0f}\n\n"
            f"<i>{now.strftime('%d %b %Y')}</i>"
        )
        print(f"[{frm}/{to}] {msg}")
        send_telegram(pair["channel"], msg)
        save_rate(pair["file"], rate_now)
