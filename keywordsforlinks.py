from flask import Flask, request, jsonify
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.collocations import BigramCollocationFinder
from nltk.corpus import wordnet
from flask_cors import CORS
import re
import pymysql
import requests
from yake import KeywordExtractor
import json
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from multiprocessing import Pool

# MySQL Database Configuration
host = 'localhost'
user = 'root'
password = ''
database = 'websuinf_wp807'
table_prefix = 'wpyd_'

app = Flask(__name__)
CORS(app)


def classify_word_to_category(word):
    word = word.strip().lower()
    synsets = wordnet.synsets(word)
    if synsets:
        return synsets[0].name().split('.')[0]
    return None

def extract_keywords(content):
    # Tokenize the content into individual words
    tokens = word_tokenize(content)

    # Remove stopwords (common words that don't carry much meaning)
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [token for token in tokens if token.lower() not in stop_words]

    # Find bigram collocations (multi-word phrases)
    finder = BigramCollocationFinder.from_words(filtered_tokens)

    # Filter out collocations containing stopwords
    finder.apply_word_filter(lambda w: w in stop_words)

    # Filter out collocations with unwanted characters or length
    filtered_collocations = []
    for collocation in finder.nbest(nltk.collocations.BigramAssocMeasures().likelihood_ratio, 5):
        collocation_text = ' '.join(collocation)
        # Remove collocations with unwanted characters or length
        if re.match(r'^[a-zA-Z\s]+$', collocation_text) and len(collocation_text) > 2:
            filtered_collocations.append(collocation_text.lower())

    # Remove duplicates while preserving the original order
    unique_keywords = list(dict.fromkeys(filtered_collocations))

    return unique_keywords

@app.route('/extract_keywords', methods=['GET'])
def process_content():
    content = request.args.get('content')

    if content:
        keywords = extract_keywords(content)
        return jsonify({'keywords': keywords})
    else:
        return jsonify({'error': 'No content provided'})

@app.route('/semantic_keywords', methods=['GET'])
def generate_keywords():
    text = request.args.get('content')
    # Create a Yake extractor with English as the language
    kw_extractor = KeywordExtractor(lan="en", n=3, dedupLim=0.9, top=15, features=None)
    #kw_extractor = KeywordExtractor(lan="en", n=2, dedupLim=0.9, top=70, features=["CI"])

    # Extract keywords from the text
    keywords = kw_extractor.extract_keywords(text)

    # Sort the keywords by score in descending order
    keywords.sort(key=lambda x: x[1])

    # Extract the keyword text and score from the Yake results
    keywords_list = [keyword[0] for keyword in keywords]

    return jsonify(keywords_list)

@app.route('/serprelatedkeywords', methods=['GET'])
def autocomplete():
    query = request.args.get('query')

    url = 'http://suggestqueries.google.com/complete/search'
    params = {'client': 'firefox', 'q': query}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0'}
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        suggestions = response.json()[1]
        return ', '.join(suggestions)
    else:
        return ''

@app.route('/youtubeapi', methods=['GET'])
def get_youtube_video_data():
    search_query = request.args.get('query')
    try:
        # Make a GET request to the YouTube Data API search endpoint
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "maxResults": 3,  # Adjust the maximum number of results as needed
            "q": search_query,
            "key": 'AIzaSyBepiIpYOYPhI2xA5cPB07iMpXrcxRdR5Q'
        }
        response = requests.get(url, params=params)
        response.raise_for_status()

        video_data = []
        transcript_text = ""
        # Parse the JSON response and extract video URLs and transcript texts
        response_json = response.json()
        for item in response_json.get("items", []):
            if item["id"]["kind"] == "youtube#video":
                video_id = item["id"]["videoId"]
                video_url = "https://www.youtube.com/watch?v=" + video_id

                try:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                    for item in transcript_list:
                        transcript_text += item["text"] + " "

                except Exception as e:
                    # Handle the exception here
                    print("An error occurred while retrieving the transcript:", str(e))

        return transcript_text

    except requests.exceptions.RequestException as e:
        print(f"A request exception occurred: {e}")
        return json.dumps({"transcript": "", "videos": []})
    except KeyError as e:
        print(f"An error occurred while parsing the response: {e}")
        return json.dumps({"transcript": "", "videos": []})



@app.route('/generatecategories', methods=['GET'])
def remove_stopwords():
    nltk.download('stopwords')  # Download the stopwords data if you haven't already
    stop_words = set(stopwords.words('english'))  # Create a set of English stopwords


    search_query = request.args.get('words')

    # Split the input word_string into individual words
    words = search_query.strip().split()

    # Remove stopwords from the list of words
    filtered_words = [word.lower() for word in words if word.lower() not in stop_words]

    # Convert the filtered words into a comma-separated string
    comma_separated_words = ', '.join(filtered_words)

    return comma_separated_words


@app.route('/listingcategories', methods=['GET'])
def get_listingcategories():
    # Get the GET parameters
    post_type = request.args.get('post_type')
    post_id = request.args.get('post_id')
    taxonomy_category = request.args.get('taxonomy_category')

    # Establish a connection to the database
    conn = pymysql.connect(host=host, user=user, password=password, database=database)
    cursor = conn.cursor()

    # Prepare the SQL query
    sql = f'''
        SELECT t.name AS category_name
        FROM {table_prefix}posts p
        JOIN {table_prefix}term_relationships tr ON p.ID = tr.object_id
        JOIN {table_prefix}term_taxonomy tt ON tr.term_taxonomy_id = tt.term_taxonomy_id
        JOIN {table_prefix}terms t ON tt.term_id = t.term_id
        WHERE p.post_type = %s
          AND p.ID = %s
          AND tt.taxonomy = %s
    '''

    try:
        # Execute the query with the provided parameters
        cursor.execute(sql, (post_type, post_id, taxonomy_category))
        results = cursor.fetchall()

        # Prepare the JSON response
        categories = [result[0] for result in results]
        response = {'categories': categories}

        # Return the response as JSON
        return json.dumps(response)

    except Exception as e:
        return str(e)

    finally:
        # Close the database connection
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(port=5005)
