import requests
import os
from datetime import datetime
import pytz
import time

PAIRS = [
    {
        "from": "USD", "to": "IDR",
        "channel": os.environ["CHANNEL_USD_IDR"],
        "file": "last_rate/usd.txt",
        "threshold": 20,
    },
    {
        "from": "CNY", "to": "IDR",
        "channel": os.environ["CHANNEL_CNY_IDR"],
        "file": "last_rate/cny.txt",
        "threshold": 5,
    },
    {
        "from": "SGD", "to": "IDR",
        "channel": os.environ["CHANNEL_SGD_IDR"],
        "file": "last_rate/sgd.txt",
        "threshold": 10,
    },
    {
        "from": "JPY", "to": "IDR",
        "channel": os.environ["CHANNEL_JPY_IDR"],
        "file": "last_rate/jpy.txt",
        "threshold": 0.5,
    },
    {
        "from": "EUR", "to": "IDR",
        "channel": os.environ["CHANNEL_EUR_IDR"],
        "file": "last_rate/eur.txt",
        "threshold": 30,
    },
    {
        "from": "MYR", "to": "IDR",
        "channel": os.environ["CHANNEL_MYR_IDR"],
        "file": "last_rate/myr.txt",
        "threshold": 10,
    },
]

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
EXCHANGERATE_API_KEY = os.environ["EXCHANGERATE_API_KEY"]

def get_rate(frm, to):
    """Fetch rate from ExchangeRate-API (hourly update, accurate)"""
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/latest/{frm}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        if data.get("result") == "success":
            return data["conversion_rates"][to]
        else:
            print(f"API Error: {data.get('error-type')}")
            return None
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

print(f"\n{'='*60}")
print(f"FOREX MONITOR - ExchangeRate-API")
print(f"Time: {now.strftime('%d %b %Y %H:%M WIB')}")
print(f"{'='*60}\n")

# Monitor each pair
for pair in PAIRS:
    frm, to = pair["from"], pair["to"]
    print(f"[{frm}/{to}] Fetching rate...", end=" ")
    
    rate_now = get_rate(frm, to)
    
    if rate_now is None:
        print(f"❌ Failed to fetch")
        continue
    
    print(f"✓ {rate_now:,.2f}")
    
    rate_last = get_last_rate(pair["file"])
    
    if rate_last is None:
        # First run, just save the rate
        save_rate(pair["file"], rate_now)
        print(f"  → Initialized")
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
            f"Δ {sign}{change:,.2f}\n\n"
            f"<i>{now.strftime('%d %b %Y %H:%M WIB')}</i>"
        )
        print(f"  → ALERT! Change: {sign}{pct:.2f}%")
        send_telegram(pair["channel"], msg)
    else:
        print(f"  → Change: {pct:+.2f}% (below threshold)")
    
    save_rate(pair["file"], rate_now)
    time.sleep(0.5)  # Small delay between requests

print(f"\n{'='*60}")
print(f"Monitor selesai. Next run: +4 jam")
print(f"{'='*60}\n")
