from flask import Flask, render_template, request
import requests

app = Flask(__name__)
apikey = 'AIzaSyBepiIpYOYPhI2xA5cPB07iMpXrcxRdR5Q'


def get_video_transcript(video_id):
    # Set the parameters for the API request
    api_key = 'YOUR_API_KEY'  # Replace with your actual API key
    params = {
        'part': 'snippet',
        'videoId': video_id,
        'key': api_key
    }

    # Make the API request to retrieve the caption tracks
    url = 'https://www.googleapis.com/youtube/v3/captions'
    response = requests.get(url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        # Extract the caption track ID from the API response
        captions = response.json()['items']
        if len(captions) > 0:
            caption_id = captions[0]['id']
        else:
            return 'No captions found for video ' + video_id

        # Construct the URL for downloading the transcript
        download_url = f'https://www.googleapis.com/youtube/v3/captions/{caption_id}'

        # Return the download URL
        return download_url
    else:
        # Handle the case when the API request fails
        return 'Failed to retrieve captions for video ' + video_id

# Home route
@app.route('/')
def home():
    return render_template('youtube.html')

# Search route
@app.route('/search', methods=['POST'])
def search():
    api_key = apikey
    query = request.form['query']  # Get the search query from the form

    # Make a request to the YouTube API search endpoint
    url = f'https://www.googleapis.com/youtube/v3/search?key={api_key}&part=snippet&type=video&q={query}'
    response = requests.get(url).json()

    # Extract the video information from the API response
    videos = []
    for item in response['items']:
        video = {
            'title': item['snippet']['title'],
            'description': item['snippet']['description'],
            'thumbnail': item['snippet']['thumbnails']['default']['url'],
            'video_id': item['id']['videoId']
        }
        videos.append(video)

    return render_template('results.html', videos=videos)

@app.route('/trending')
def get_trending_videos():
    # Set the parameters for the API request
    api_key = apikey  # Replace with your actual API key
    params = {
        'part': 'snippet',
        'chart': 'mostPopular',
        'maxResults': 5  # You can adjust the number of results as needed
    }

    # Make the API request to retrieve trending videos
    url = f'https://www.googleapis.com/youtube/v3/videos?key={api_key}'
    response = requests.get(url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        # Extract the relevant information from the API response
        videos = response.json()['items']

        # Get the transcript for each video
        for video in videos:
            transcript = get_video_transcript(video['id'])
            video['transcript'] = transcript

             

        # Render the template with the trending videos
        return render_template('trending.html', videos=videos)
    else:
        # Handle the case when the API request fails
        return 'Failed to retrieve trending videos', 500

if __name__ == '__main__':
    app.run(debug=True)
