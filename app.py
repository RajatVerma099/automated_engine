import os
import re
import time
import random
import requests
from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)

SCRAPER_ENDPOINTS = {
    "fresheropenings.com": "https://job-scraper-backend-1.onrender.com",
    "fresherscareers.com": "https://job-scraper-2.onrender.com",
    "fresherscamp.com": "https://job-scraper-3.onrender.com"
}

NOTIF_URL = "https://notifs-harbour.onrender.com/"

# Max retries and wait time for cold starts
MAX_RETRIES = 5
RETRY_WAIT = 3  # seconds

# Rotating User-Agents (30 examples)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...Safari/537.3',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...Safari/605.1.15',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64)...Firefox/89.0',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64)...Chrome/90.0.4430.212 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6)...Chrome/88.0.4324.96 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64)...Chrome/85.0.4183.83 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64)...Trident/7.0; rv:11.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6)...Firefox/78.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64)...Firefox/82.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 13_5_1)...Safari/604.1',
    'Mozilla/5.0 (Linux; Android 9; SM-G960F)...Chrome/77.0.3865.92 Mobile Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...Edge/18.19041',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6)...Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 6.1; WOW64)...Firefox/77.0',
    'Mozilla/5.0 (Linux; Android 10; Pixel 3)...Chrome/89.0.4389.105 Mobile Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...Chrome/91.0.4472.101 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64)...Chrome/88.0.4324.150 Safari/537.36',
    'Mozilla/5.0 (iPad; CPU OS 13_6 like Mac OS X)...Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3)...Chrome/90.0.4430.212 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...Firefox/89.0',
    'Mozilla/5.0 (X11; Linux x86_64)...Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6)...Firefox/79.0',
    'Mozilla/5.0 (Linux; Android 8.0.0; SM-G935F)...Chrome/86.0.4240.110 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_4)...Safari/604.1',
    'Mozilla/5.0 (Windows NT 10.0; WOW64)...Edge/91.0.864.41',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6)...Chrome/76.0.3809.100 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64)...Firefox/88.0',
    'Mozilla/5.0 (iPad; CPU OS 12_4_1 like Mac OS X)...Safari/604.1',
    'Mozilla/5.0 (Linux; Android 11; Pixel 4 XL)...Chrome/90.0.4430.91 Mobile Safari/537.36',
]

def extract_urls(text):
    return list(set(re.findall(r'https?://[\w./\-]+', text)))

def get_scraper_endpoint(url):
    for keyword, endpoint in SCRAPER_ENDPOINTS.items():
        if keyword in url:
            return endpoint
    return None

def wake_servers(endpoints_dict):
    warm_up_status = []
    for name, url in endpoints_dict.items():
        success = False
        wait = RETRY_WAIT
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                headers = {'User-Agent': random.choice(USER_AGENTS)}
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200:
                    warm_up_status.append(f"✅ {name} is up (status {r.status_code})")
                    success = True
                    break
                elif 500 <= r.status_code < 600:
                    warm_up_status.append(f"⚠️ {name} returned {r.status_code}, retrying in {wait}s...")
                else:
                    warm_up_status.append(f"❌ {name} returned non-retryable status {r.status_code}")
                    break
            except Exception as e:
                warm_up_status.append(f"🔥 {name} connection error: {e}, retrying in {wait}s...")
            time.sleep(wait)
            wait *= 2  # exponential backoff
        if not success:
            warm_up_status.append(f"❌ {name} failed after {MAX_RETRIES} retries.")
    return warm_up_status

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = request.form['text']
        urls = extract_urls(text)
        results = []

        # Wake up job scraper servers
        warm_up_status = wake_servers(SCRAPER_ENDPOINTS)

        # Wake up notification server
        warm_up_status += wake_servers({"Notification server": NOTIF_URL})

        # Scrape each URL
        for url in urls:
            endpoint = get_scraper_endpoint(url)
            if not endpoint:
                results.append({'url': url, 'status': '❓ No matching server'})
                continue

            headers = {'User-Agent': random.choice(USER_AGENTS)}
            try:
                res = requests.post(endpoint, data={'url': url}, headers=headers, timeout=15)
                if res.status_code == 200:
                    results.append({'url': url, 'status': '✅ Success'})
                else:
                    results.append({'url': url, 'status': f'❌ Failed ({res.status_code})'})
            except Exception as e:
                results.append({'url': url, 'status': f'🔥 Error: {str(e)}'})

        # Trigger notification
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            notif_res = requests.post(NOTIF_URL + "send-notifications", json={'date': today}, headers=headers, timeout=15)
            if notif_res.status_code == 200:
                warm_up_status.append(f"🔔 Triggered notifications for {today} (Status: {notif_res.status_code})")
            else:
                warm_up_status.append(f"❌ Notification trigger failed (Status: {notif_res.status_code}) - {notif_res.text}")
        except Exception as e:
            warm_up_status.append(f"❌ Failed to trigger notifications: {str(e)}")

        return render_template('index.html', results=results, completed=True, warm_up_status=warm_up_status)

    return render_template('index.html', results=None, completed=False, warm_up_status=None)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))


# import os
# from flask import Flask, render_template, request
# import re
# import time
# import requests
# from datetime import datetime

# app = Flask(__name__)

# SCRAPER_ENDPOINTS = {
#     "fresheropenings.com": "https://job-scraper-backend-1.onrender.com",
#     "fresherscareers.com": "https://job-scraper-2.onrender.com",
#     "fresherscamp.com": "https://job-scraper-3.onrender.com"
# }

# NOTIF_URL = "https://notifs-harbour.onrender.com/"

# # Extract all URLs using regex
# def extract_urls(text):
#     return list(set(re.findall(r'https?://[\w./\-]+', text)))

# # Get scraper based on URL domain
# def get_scraper_endpoint(url):
#     for keyword, endpoint in SCRAPER_ENDPOINTS.items():
#         if keyword in url:
#             return endpoint
#     return None

# @app.route('/', methods=['GET', 'POST'])
# def index():
#     if request.method == 'POST':
#         text = request.form['text']
#         urls = extract_urls(text)
#         results = []

#         # Check which servers are already up
#         warm_up_status = []
#         endpoints_to_wait = []

#         # Warm up scraping endpoints
#         for keyword, endpoint in SCRAPER_ENDPOINTS.items():
#             try:
#                 r = requests.get(endpoint, timeout=10)
#                 if r.status_code == 200:
#                     warm_up_status.append(f"✅ {keyword} is already up (status {r.status_code})")
#                 else:
#                     warm_up_status.append(f"⚠️ {keyword} responded with status {r.status_code}")
#                     endpoints_to_wait.append(endpoint)
#             except Exception as e:
#                 warm_up_status.append(f"⚠️ {keyword} not reachable: {e}")
#                 endpoints_to_wait.append(endpoint)

#         # Warm up the notification server
#         try:
#             r = requests.get(NOTIF_URL, timeout=10)
#             if r.status_code == 200:
#                 warm_up_status.append(f"✅ Notification server is already up (status {r.status_code})")
#             else:
#                 warm_up_status.append(f"⚠️ Notification server responded with status {r.status_code}")
#                 endpoints_to_wait.append(NOTIF_URL)
#         except Exception as e:
#             warm_up_status.append(f"⚠️ Notification server not reachable: {e}")
#             endpoints_to_wait.append(NOTIF_URL)

#         # Wait only if needed
#         if endpoints_to_wait:
#             wait_seconds = 60
#             for i in range(wait_seconds, 0, -1):
#                 time.sleep(1)

#         # Scrape each URL
#         for url in urls:
#             endpoint = get_scraper_endpoint(url)
#             if not endpoint:
#                 results.append({'url': url, 'status': '❓ No matching server'})
#                 continue

#             try:
#                 res = requests.post(endpoint, data={'url': url}, timeout=15)
#                 if res.status_code == 200:
#                     results.append({'url': url, 'status': '✅ Success'})
#                 else:
#                     results.append({'url': url, 'status': f'❌ Failed ({res.status_code})'})
#             except Exception as e:
#                 results.append({'url': url, 'status': f'🔥 Error: {str(e)}'})

#         # Trigger the notification service with today's date
#         try:
#             today = datetime.now().strftime('%Y-%m-%d')
#             notif_res = requests.post(NOTIF_URL + "send-notifications", json={'date': today}, timeout=15)
#             if notif_res.status_code == 200:
#                 warm_up_status.append(f"🔔 Triggered notifications for {today} (Status: {notif_res.status_code})")
#             else:
#                 warm_up_status.append(f"❌ Notification trigger failed (Status: {notif_res.status_code}) - {notif_res.text}")
#         except Exception as e:
#             warm_up_status.append(f"❌ Failed to trigger notifications: {str(e)}")


#         return render_template('index.html', results=results, completed=True, warm_up_status=warm_up_status)

#     return render_template('index.html', results=None, completed=False, warm_up_status=None)

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=os.environ['PORT'])
