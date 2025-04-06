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
    if request.method == 'POST':
        text = request.form['text']
        urls = extract_urls(text)
        results = []

        # Check which servers are already up
        warm_up_status = []
        endpoints_to_wait = []

        # Warm up scraping endpoints
        for keyword, endpoint in SCRAPER_ENDPOINTS.items():
            try:
                r = requests.get(endpoint, timeout=10)
                if r.status_code == 200:
                    warm_up_status.append(f"✅ {keyword} is already up (status {r.status_code})")
                else:
                    warm_up_status.append(f"⚠️ {keyword} responded with status {r.status_code}")
                    endpoints_to_wait.append(endpoint)
            except Exception as e:
                warm_up_status.append(f"⚠️ {keyword} not reachable: {e}")
                endpoints_to_wait.append(endpoint)

        # Warm up the notification server
        try:
            r = requests.get(NOTIF_URL, timeout=10)
            if r.status_code == 200:
                warm_up_status.append(f"✅ Notification server is already up (status {r.status_code})")
            else:
                warm_up_status.append(f"⚠️ Notification server responded with status {r.status_code}")
                endpoints_to_wait.append(NOTIF_URL)
        except Exception as e:
            warm_up_status.append(f"⚠️ Notification server not reachable: {e}")
            endpoints_to_wait.append(NOTIF_URL)

        # Wait only if needed
        if endpoints_to_wait:
            wait_seconds = 60
            for i in range(wait_seconds, 0, -1):
                time.sleep(1)

        # Scrape each URL
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

        # Trigger the notification service with today's date
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            notif_res = requests.post(NOTIF_URL + "send-notifications", json={'date': today}, timeout=15)
            if notif_res.status_code == 200:
                warm_up_status.append(f"🔔 Triggered notifications for {today} (Status: {notif_res.status_code})")
            else:
                warm_up_status.append(f"❌ Notification trigger failed (Status: {notif_res.status_code}) - {notif_res.text}")
        except Exception as e:
            warm_up_status.append(f"❌ Failed to trigger notifications: {str(e)}")


        return render_template('index.html', results=results, completed=True, warm_up_status=warm_up_status)

    return render_template('index.html', results=None, completed=False, warm_up_status=None)

if __name__ == '__main__':
    app.run(debug=True)
