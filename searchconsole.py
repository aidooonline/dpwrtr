import os
import flask
from flask import render_template
import requests
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import json


app = flask.Flask(__name__)
app.secret_key = os.urandom(24)

CLIENT_SECRETS_FILE = "secured/client_secret_2.json"
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
API_SERVICE_NAME = 'webmasters'
API_VERSION = 'v3'

@app.route('/')
def index():
    return print_index_table()

@app.route('/test')
def test_api_request():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    service = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    search_analytics_request = {
        'startDate': '2023-01-01',
        'endDate': '2023-04-31',
        'dimensions': ['page', 'query'],
        'rowLimit': 25000,
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
            siteUrl='websitesgh.com', body=search_analytics_request).execute()
        response_code = response.status_code if 'status_code' in response else None
        response_string = response.text if 'text' in response else None
        return render_template('response.html', response_code=response_code, response_string=response_string)
    except Exception as e:
        
        return render_template('response.html', response_code='Error', response_string=str(e))


@app.route('/keywords')
def show_keywords():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

    credentials = google.oauth2.credentials.Credentials(**flask.session['credentials'])

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

     
    response = service.searchanalytics().query(siteUrl='websitesgh.com', body=search_analytics_request).execute()
    
    response_code = response.get('responseCode')
    response_string = response.get('responseString', '')

    return render_template('keywords.html', keywords=response.get('rows', []), response_code=response_code, response_string=response_string)


@app.route('/authorize')
def authorize():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    flask.session['state'] = state
    return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    state = flask.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
    CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)

    return flask.redirect(flask.url_for('test_api_request'))


@app.route('/revoke')
def revoke():
    if 'credentials' not in flask.session:
        return ('You need to <a href="/authorize">authorize</a> before ' +
                'testing the code to revoke credentials.')

    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    revoke = requests.post('https://oauth2.googleapis.com/revoke',
                           params={'token': credentials.token},
                           headers={'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        return ('Credentials successfully revoked.' + print_index_table())
    else:
        return ('An error occurred.' + print_index_table())


@app.route('/clear')
def clear_credentials():
    if 'credentials' in flask.session:
        del flask.session['credentials']
    return ('Credentials have been cleared.<br><br>' +
            print_index_table())


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}


def print_index_table():
    return ('<table>' +
            '<tr><td><a href="/test">Test an API request</a></td>' +
            '<td>Submit an API request and see a formatted JSON response. ' +
            '    Go through the authorization flow if there are no stored ' +
            '    credentials for the user.</td></tr>' +
            '<tr><td><a href="/keywords">Show URLs with Impressions and Positions</a></td>' +
            '<td>Show a list of URLs with their impressions and positions. ' +
            '    Requires authorization.</td></tr>' +
            '<tr><td><a href="/authorize">Test the auth flow directly</a></td>' +
            '<td>Go directly to the authorization flow. If there are stored ' +
            '    credentials, you still might not be prompted to reauthorize ' +
            '    the application.</td></tr>' +
            '<tr><td><a href="/revoke">Revoke current credentials</a></td>' +
            '<td>Revoke the access token associated with the current user ' +
            '    session. After revoking credentials, if you go to the test ' +
            '    page, you should see an <code>invalid_grant</code> error.' +
            '</td></tr>' +
            '<tr><td><a href="/clear">Clear Flask session credentials</a></td>' +
            '<td>Clear the access token currently stored in the user session. ' +
            '    After clearing the token, if you <a href="/test">test the ' +
            '    API request</a> again, you should go back to the auth flow.' +
            '</td></tr></table>')


if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run('localhost', 8000,debug=True)

