from flask import Flask, render_template, request
import re
import time
import requests

app = Flask(__name__)

SCRAPER_ENDPOINTS = {
    "fresheropenings.com": "https://job-scraper-backend-1.onrender.com",
    "fresherscareers.com": "https://job-scraper-2.onrender.com",
    "fresherscamp.com": "https://job-scraper-3.onrender.com"
}

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

        # Wait only if any endpoint needs warming
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

        return render_template('index.html', results=results, completed=True, warm_up_status=warm_up_status)

    return render_template('index.html', results=None, completed=False, warm_up_status=None)

if __name__ == '__main__':
    app.run(debug=True)


# from flask import Flask, render_template, request, jsonify
# import re
# import csv
# import time
# import requests

# app = Flask(__name__)

# SCRAPER_ENDPOINTS = {
#     "fresheropenings.com": "https://job-scraper-backend-1.onrender.com",
#     "fresherscareers.com": "https://job-scraper-2.onrender.com",
#     "fresherscamp.com": "https://job-scraper-3.onrender.com"
# }

# # Extract all URLs using regex
# def extract_urls(text):
#     return list(set(re.findall(r'https?://[^\s]+', text)))

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

#         # Warm up servers (ping them)
#         for endpoint in SCRAPER_ENDPOINTS.values():
#             try:
#                 requests.get(endpoint, timeout=10)
#             except:
#                 pass

#         # Wait 60 seconds for warm-up
#         time.sleep(60)

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

#         return render_template('index.html', results=results, completed=True)

#     return render_template('index.html', results=None, completed=False)

# if __name__ == '__main__':
#     app.run(debug=True)
