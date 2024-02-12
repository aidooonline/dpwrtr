from flask import Flask
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.exceptions import GoogleAuthError
from googleapiclient.errors import HttpError
from requests.exceptions import RequestException

app = Flask(__name__)

@app.route('/')
def get_keywords():
    try:
        # Set the API credentials.
        credentials = service_account.Credentials.from_service_account_file("secured/gglaccount-156823-99c8928648b1.json")

        # Build the Search Console API client.
        service = build('webmasters', 'v3', credentials=credentials)

        # Set the API endpoint.
        endpoint = "https://searchconsole.googleapis.com/v1/sites/https://websitesgh.com/searches"

        # Call the API method to get the list of keywords.
        response = service.searchanalytics().query(
            siteUrl="https://websitesgh.com/",
            body={"dimensions": ["query"]}
        ).execute()

        # Parse the JSON response.
        keywords = response.get('rows', [])

        # Prepare the response string with the list of keywords.
        response_str = ""
        for keyword in keywords:
            response_str += f"Query: {keyword['keys'][0]}, Clicks: {keyword['clicks']}, Impressions: {keyword['impressions']}, Position: {keyword['position']}\n"

        return response_str

    except GoogleAuthError as auth_error:
        return "Google Authentication Error: " + str(auth_error), 500  # Return status code 500 for internal server error
    except HttpError as http_error:
        error_message = http_error._get_reason() if hasattr(http_error, '_get_reason') else str(http_error)
        return "HTTP Error: " + error_message, http_error.resp.status
    except RequestException as request_error:
        return "Request Error: " + str(request_error), 500  # Return status code 500 for internal server error
    except KeyError:
        return "Error: Response did not contain the expected data.", 500  # Return status code 500 for internal server error
    except Exception as e:
        return "An unexpected error occurred: " + str(e), 500  # Return status code 500 for internal server error

if __name__ == '__main__':
    app.run()
