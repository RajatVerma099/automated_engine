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

    # Step 1: Wake up scraper servers using GET fetch calls
    for name, endpoint in SCRAPER_ENDPOINTS.items():
        try:
            res = requests.get(endpoint, timeout=15)
            if res.status_code == 200:
                warm_up_status.append(f"🟢 {name} is awake ({endpoint})")
            else:
                warm_up_status.append(f"🟡 {name} responded with {res.status_code}")
        except Exception as e:
            warm_up_status.append(f"🔴 Error waking {name}: {str(e)}")

    # Step 2: Warm-up notification server with GET (optional)
    try:
        res = requests.get(NOTIF_URL, timeout=15)
        if res.status_code == 200:
            warm_up_status.append("🔔 Notification server is awake")
        else:
            warm_up_status.append(f"⚠️ Notification server responded with {res.status_code}")
    except Exception as e:
        warm_up_status.append(f"❌ Notification wake-up error: {str(e)}")

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
