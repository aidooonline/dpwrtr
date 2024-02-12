import os
import flask
from flask import render_template
import googleapiclient.discovery
from google.oauth2 import service_account

app = flask.Flask(__name__)
app.secret_key = os.urandom(24)

# Service Account credentials
SERVICE_ACCOUNT_FILE = "secret/gglaccount-156823-8d7cfef2ca88.json"
API_SERVICE_NAME = 'webmasters'
API_VERSION = 'v3'

@app.route('/')
def index():
    return print_index_table()

@app.route('/test')
def test_api_request():
    # ...

@app.route('/keywords')
def show_keywords():
    if 'credentials' not in flask.session:
    return flask.redirect('authorize')

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/webmasters.readonly'])

    service = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

    search_analytics_request = {
        'startDate': '2023-01-01',
        'endDate': '2023-04-31',
        'dimensions': ['page', 'query'],
        'rowLimit': 100,
        'startRow': 0,
        'aggregationType': 'byPage',
        'searchType': 'web',
        'dimensionFilterGroups': [
            {'filters': [{'dimension': 'device', 'expression': 'mobile'}]},
            {'filters': [{'dimension': 'device', 'expression': 'desktop'}]},
            {'filters': [{'dimension': 'country', 'operator': 'equals', 'expression': 'country:us'}]}
        ]
    }

    try:
        response = service.searchanalytics().query(
            siteUrl='https://websitesgh.com', body=search_analytics_request).execute()
        response_code = response.get('responseCode')
        response_string = response.get('responseString', '')
        return render_template('response.html', response_code=response_code, response_string=response_string)
    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('response.html', response_code='Error', response_string=str(e))


if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run('localhost', 8000, debug=True)
