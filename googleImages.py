from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import requests

app = Flask(__name__)
CORS(app)

def get_image_links(keyword):
    api_key = "AIzaSyBepiIpYOYPhI2xA5cPB07iMpXrcxRdR5Q"  # Replace with your own Google API key
    search_engine_id = "9559cb25da51941b9"  # Replace with your own Custom Search Engine ID

    url = f"https://customsearch.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": keyword + " ghana " + " -facebook.com -instagram.com -twitter.com -youtube.com -tiktok.com -ghanabusinessweb.com -licdn.com",
        "searchType": "image",
        "num": 5
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if 'items' in data:
            image_links = [item['link'] for item in data['items']]
            return '***'.join(image_links)
        else:
            print("No image results found.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return None

@app.route('/getimages', methods=['GET'])
def get_images():
    keyword = request.args.get('keyword')  # Get the keyword from the query parameters
    
    if keyword:
        image_links = get_image_links(keyword)
        
        if image_links:
            return image_links
        else:
            return jsonify({'error': 'Failed to fetch image links.'}), 500
    else:
        return jsonify({'error': 'Keyword parameter is missing.'}), 400

if __name__ == '__main__':
    app.run(port=5006)