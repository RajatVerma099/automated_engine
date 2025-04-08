import os
from flask import Flask, render_template, request
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

# Extract all URLs using regex
def extract_urls(text):
    return list(set(re.findall(r'https?://[\w./\-]+', text)))

# Get scraper based on URL domain
def get_scraper_endpoint(url):
    for keyword, endpoint in SCRAPER_ENDPOINTS.items():
        if keyword in url:
            return endpoint
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    warm_up_status = []
    results = []

    # Step 1: Warm-up using fake payloads to each scraper
    FAKE_PAYLOADS = [
        ("https://fresheropenings.com/abc/", SCRAPER_ENDPOINTS["fresheropenings.com"]),
        ("https://fresherscamp.com/abc/", SCRAPER_ENDPOINTS["fresherscamp.com"]),
        ("https://fresherscareers.com/abc/", SCRAPER_ENDPOINTS["fresherscareers.com"]),
    ]

    for fake_url, endpoint in FAKE_PAYLOADS:
        try:
            res = requests.post(endpoint, data={'url': fake_url}, timeout=15)
            if res.status_code == 200:
                warm_up_status.append(f"🟢 Warm-up success for {endpoint}")
            else:
                warm_up_status.append(f"🟡 Warm-up failed ({res.status_code}) for {endpoint}")
        except Exception as e:
            warm_up_status.append(f"🔴 Error warming up {endpoint}: {str(e)}")

    # Step 2: Warm-up notification server with fake date
    try:
        notif_res = requests.post(NOTIF_URL + "send-notifications", json={'date': '2001-02-27'}, timeout=15)
        if notif_res.status_code == 200:
            warm_up_status.append("🔔 Notification server warmed up with fake date 2001-02-27")
        else:
            warm_up_status.append(f"⚠️ Notification warm-up failed (Status: {notif_res.status_code})")
    except Exception as e:
        warm_up_status.append(f"❌ Notification warm-up error: {str(e)}")

    # Step 3: If POST request, handle user-submitted URLs
    if request.method == 'POST':
        text = request.form['text']
        urls = extract_urls(text)

        # Wait 60 seconds to let servers fully wake up (matches JS countdown)
        time.sleep(60)

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

        # Trigger actual notification for today's date
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            notif_res = requests.post(NOTIF_URL + "send-notifications", json={'date': today}, timeout=15)
            if notif_res.status_code == 200:
                warm_up_status.append(f"🔔 Notifications triggered for {today}")
            else:
                warm_up_status.append(f"❌ Notification trigger failed ({notif_res.status_code})")
        except Exception as e:
            warm_up_status.append(f"❌ Notification error: {str(e)}")

        return render_template('index.html', results=results, completed=True, warm_up_status=warm_up_status)

    return render_template('index.html', results=None, completed=False, warm_up_status=warm_up_status)

# if __name__ == '__main__':
#     app.run(host='127.0.0.1', port=int(os.environ.get('PORT', 5000)))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ['PORT'])

