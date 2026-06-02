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
    """Fetch rate from Frankfurter API v2"""
    url = f"https://api.frankfurter.dev/v2/rate/{frm}/{to}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()["rate"]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {frm}/{to}: {e}")
        return None

def get_last_rate(filepath):
    """Get last stored rate from file"""
    try:
        with open(filepath) as f:
            return float(f.read().strip())
    except:
        return None

def save_rate(filepath, rate):
    """Save current rate to file"""
    with open(filepath, "w") as f:
        f.write(str(rate))

def send_telegram(channel, msg):
    """Send message to Telegram channel"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": channel, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}")

# Setup
wib = pytz.timezone("Asia/Jakarta")
now = datetime.now(wib)
os.makedirs("last_rate", exist_ok=True)

# Monitor each pair
for pair in PAIRS:
    frm, to = pair["from"], pair["to"]
    rate_now = get_rate(frm, to)
    
    if rate_now is None:
        print(f"[{frm}/{to}] Failed to fetch rate, skipping...")
        continue
    
    rate_last = get_last_rate(pair["file"])
    
    if rate_last is None:
        # First run, just save the rate
        save_rate(pair["file"], rate_now)
        print(f"[{frm}/{to}] Initialized with rate: {rate_now:,.0f}")
        continue
    
    change = rate_now - rate_last
    pct = (change / rate_last) * 100
    
    # Check threshold
    if abs(change) >= pair["threshold"]:
        emoji = "🔴" if change > 0 else "🟢"
        sign = "+" if change > 0 else ""
        msg = (
            f"{emoji} <b>{frm}/{to}</b> [{sign}{pct:.2f}%]\n\n"
            f"Rp {rate_last:,.0f} → Rp {rate_now:,.0f}\n"
            f"Δ {sign}{change:,.0f}\n\n"
            f"<i>{now.strftime('%d %b %Y %H:%M WIB')}</i>"
        )
        print(f"[{frm}/{to}] Change detected: {sign}{pct:.2f}%")
        send_telegram(pair["channel"], msg)
    
    save_rate(pair["file"], rate_now)
