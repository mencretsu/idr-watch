import requests
import os
from datetime import datetime
import pytz

BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
CHANNEL_ID = os.environ['TELEGRAM_CHANNEL_ID']
THRESHOLD = 1  # alert kalau gerak >= 100 poin

def get_rate():
    url = "https://api.frankfurter.app/latest?from=USD&to=IDR"
    r = requests.get(url, timeout=10)
    return r.json()['rates']['IDR']

def get_last_rate():
    try:
        with open('last_rate.txt', 'r') as f:
            return float(f.read().strip())
    except:
        return None

def save_rate(rate):
    with open('last_rate.txt', 'w') as f:
        f.write(str(rate))

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        'chat_id': CHANNEL_ID,
        'text': msg,
        'parse_mode': 'HTML'
    })

wib = pytz.timezone('Asia/Jakarta')
now = datetime.now(wib)

rate_now = get_rate()
rate_last = get_last_rate()

if rate_last is None:
    save_rate(rate_now)
    exit()

change = rate_now - rate_last
pct = (change / rate_last) * 100

if abs(change) >= THRESHOLD:
    emoji = "🔴" if change > 0 else "🟢"
    sign = "+" if change > 0 else ""

    msg = f"""{emoji} <b>USD/IDR Alert!</b>

Rp {rate_last:,.0f} → Rp {rate_now:,.0f}
{sign}{pct:.2f}%

[{now.strftime('%d %b %Y')}]"""
    print(msg)
    send_telegram(msg)
    save_rate(rate_now)
