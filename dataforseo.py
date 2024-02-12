from flask import Flask, jsonify

# Import the necessary libraries and create a Flask app
from rest_client.async import RESTClient
app = Flask(__name__)

# Define the route function
@app.route('/search_volume', methods=['GET'])
def get_search_volume():
    # Create a RestClient instance
    client = RestClient("kasqo2004@gmail.com", "94c27d7ff62ddb02")

    # Prepare the post data
    post_data = {
        0: {
            "keywords": [
                "china mall ghana",
                "china mall",
                "kpeshie"
            ],
            "date_from": "2023-01-01",
            "search_partners": True
        }
    }

    # Make the API call
    response = client.post("/v3/keywords_data/google_ads/search_volume/live", post_data)

    # Process the response
    if response["status_code"] == 20000:
        # Return the response as JSON
        return jsonify(response)
    else:
        # Return an error message
        return jsonify({"error": f"Code: {response['status_code']} Message: {response['status_message']}"})

# Run the Flask app
if __name__ == '__main__':
    app.run()
