from flask import Flask, request, jsonify, render_template
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.ads.google_ads.errors import GoogleAdsException
from google.ads.google_ads.client import GoogleAdsClient


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('googlesearchvolume.html')

@app.route('/get_search_data', methods=['POST'])
def get_search_data():
    # Get the keywords from the request
    keywords = request.form.get('keywords').split(',')

    # Authenticate with Google Ads API
    credentials = Credentials.from_client_secrets_file(
        'secured/client_secret.json',
        scopes=['https://www.googleapis.com/auth/adwords']
    )
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            return 'Invalid credentials', 401

    # Create a Google Ads API client
    client = GoogleAdsClient(credentials=credentials)

    # Fetch search volume and CPC data for each keyword
    search_data = []
    for keyword in keywords:
        query = f'SELECT search_volume, average_cpc FROM keyword_view WHERE text = "{keyword.strip()}"'
        response = client.service.google_ads.search(query=query)

        for row in response:
            search_volume = row.keyword_view.search_volume.value
            cpc_high = row.keyword_view.average_cpc.high_micros
            cpc_low = row.keyword_view.average_cpc.low_micros
            search_data.append({'keyword': keyword, 'search_volume': search_volume, 'cpc_high': cpc_high, 'cpc_low': cpc_low})

    return jsonify(search_data)

if __name__ == '__main__':
    app.run()
