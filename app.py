import os
from flask import Flask, render_template, request, jsonify
import re
import time
import requests
from datetime import datetime

app = Flask(__name__)

SCRAPER_ENDPOINTS = {
    "fresheropenings.com": "https://job-scraper-backend-1.onrender.com",
    "fresherscareers.com": "https://job-scraper-2.onrender.com",
    "fresherscamp.com": "https://job-scraper-3.onrender.com"
}

NOTIF_URL = "https://notifs-harbour.onrender.com/"

def extract_urls(text):
    return list(set(re.findall(r'https?://[\w./\-]+', text)))

def get_scraper_endpoint(url):
    for keyword, endpoint in SCRAPER_ENDPOINTS.items():
        if keyword in url:
            return endpoint
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    warm_up_status = []
    results = []

    # Wake notification server (client wakes scrapers)
    try:
        res = requests.get(NOTIF_URL, timeout=15)
        if res.status_code == 200:
            warm_up_status.append("🔔 Notification server is awake")
        else:
            warm_up_status.append(f"⚠️ Notification server responded with {res.status_code}")
    except Exception as e:
        warm_up_status.append(f"❌ Notification wake-up error: {str(e)}")

    if request.method == 'POST':
        text = request.form['text']
        urls = extract_urls(text)

        time.sleep(60)  # Let Render wake up endpoints

        for url in urls:
            endpoint = get_scraper_endpoint(url)
            if not endpoint:
                results.append({'url': url, 'status': '❓ No matching server'})
                continue

            try:
                res = requests.post(endpoint, data={'url': url}, timeout=15)
                if res.status_code == 200:
                    results.append({'url': url, 'status': '✅ Success'})
                else:
                    results.append({'url': url, 'status': f'❌ Failed ({res.status_code})'})
            except Exception as e:
                results.append({'url': url, 'status': f'🔥 Error: {str(e)}'})

        try:
            today = datetime.now().strftime('%Y-%m-%d')
            notif_res = requests.post(NOTIF_URL + "send-notifications", json={'date': today}, timeout=15)
            if notif_res.status_code == 200:
                warm_up_status.append(f"🔔 Notifications triggered for {today}")
            else:
                warm_up_status.append(f"❌ Notification trigger failed ({notif_res.status_code})")
        except Exception as e:
            warm_up_status.append(f"❌ Notification error: {str(e)}")

        return render_template('index.html', results=results, completed=True,
                               warm_up_status=warm_up_status, SCRAPER_ENDPOINTS=SCRAPER_ENDPOINTS)

    return render_template('index.html', results=None, completed=False,
                           warm_up_status=warm_up_status, SCRAPER_ENDPOINTS=SCRAPER_ENDPOINTS)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
