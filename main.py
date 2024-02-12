from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from multi_rake import Rake
import requests  
from bs4 import BeautifulSoup           
import re
import csv
import time
from flask_cors import CORS
from yake import KeywordExtractor 
from youtube_transcript_api import YouTubeTranscriptApi

 
 
 
app = Flask(__name__)
api = Api(app)
CORS(app, resources={r"/*": {"origins": "*"}})


def get_youtube_video_data(search_query):
    
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


def generate_keywords(text):
    # Create a Yake extractor with English as the language
    kw_extractor = KeywordExtractor(lan="en", n=3, dedupLim=0.9, top=70, features=None)
    #kw_extractor = KeywordExtractor(lan="en", n=2, dedupLim=0.9, top=70, features=["CI"])
    
    # Extract keywords from the text
    keywords = kw_extractor.extract_keywords(text)
    
    # Sort the keywords by score in descending order
    keywords.sort(key=lambda x: x[1])
    
    # Extract the keyword text and score from the Yake results
    keywords_list = [keyword[0] for keyword in keywords]
    
    return keywords_list


def clean_text(text):
    # remove unwanted characters
    cleaned_text = re.sub('[^a-zA-Z0-9 \n\.]', '', text)
    # replace new lines with spaces
    cleaned_text = cleaned_text.replace('\n', ' ')
    # remove extra spaces
    cleaned_text = re.sub(' +', ' ', cleaned_text)
    return cleaned_text

def autocomplete(query): 
    if not query:
        return jsonify([])

    url = 'http://suggestqueries.google.com/complete/search'
    params = {'client': 'firefox', 'q': query}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0'}
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        suggestions = response.json()[1]
        return jsonify(suggestions)
    else:
        return jsonify([])

  

def generate_prompt(main_keyword,instruction,content_keywords,related_keywords):
    
    prompt = ''
    if instruction == '1':
        prompt += f'Write a comprehensive article not less than 1000 words using "{main_keyword}" as the title and make sure the provided keywords are at least 90% part of the article ideas and present in the sentences. Create subtopics from the keywords and Dont repeat main title keyword more than 3 times:\n\n'
        prompt += f"- {', '.join(content_keywords)}\n"
        prompt += '\nCreate subtopics as necessary.'
    elif instruction == '2':
        prompt += f'Write related contents using the following keywords as subtopics. Use the following tag formats: <h3>Keyword</h3> and <p>Related contents to write</p>. Dont add conclusion and dont add introduction. Just describe and write a great content on each related keyword. IMPORTANT: Ignore the first keyword in the keyword list:\n\n'
        prompt += f"- {', '.join(related_keywords)}\n"
    elif instruction == '3':
        prompt += f'Write a Glossary related contents using "{main_keyword} Glossary" as the title and the following. Return a tag results with the keywords in the Glossary in bold like <strong>Keyword</strong>: and definition of keyword in <p>Definition of Glossary</p> paragraphs elements. The following are the Glossary Keywords:\n\n'
        prompt += f"- {', '.join(content_keywords)}\n"
    return prompt

class HelloWorld(Resource):
    def get(self, query):
        # Get links from Google search API
        response = requests.get(f'https://www.googleapis.com/customsearch/v1?key=AIzaSyBepiIpYOYPhI2xA5cPB07iMpXrcxRdR5Q&cx=9559cb25da51941b9&q={query}&num=20')
        results = response.json().get('items', [])

        url = 'http://suggestqueries.google.com/complete/search'
        params = {'client': 'firefox', 'q': query}
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0'}
        response2 = requests.get(url, params=params, headers=headers)
        results2 = response2.json()[1]

        links = [result['link'] for result in results]

        filename = f"keywords/{query}.csv"
        contentfilename = f"scrapedcontents/{query}.txt"
        relatedkeywordsfilename = f"relatedkeywords/{query}.csv"
        prompt1filename = f"prompts/{query}_prompt1.txt"
        prompt2filename = f"prompts/{query}_prompt2.txt"
        prompt3filename = f"prompts/{query}_prompt3.txt"

        # Scrape and clean text from links
        full_text = ""
        exception =""
        for link in links[:20]:
            try:
                start_time = time.time()
                page = requests.get(link, allow_redirects=False, timeout=50)
                elapsed_time = time.time() - start_time
                if elapsed_time > 40:
                    # log the delay or return an error message to the user
                    continue
                page.raise_for_status()  # raise an error for any HTTP error status codes
            except (requests.exceptions.RequestException, TimeoutError) as e:
                # log the error or return an error message to the user
                continue
            except Exception as e:
                # log any other type of error
                excepton = str(e)
                continue
            if page.status_code >= 300 and page.status_code < 400:
                # Skip redirect links
                continue
            if page.status_code == 110:
                # Skip redirect links
                continue

            soup = BeautifulSoup(page.content, 'html.parser')
            paragraphs = soup.find_all(['p'])

            text = '\n\n'.join([p.get_text(separator=' ') for p in paragraphs])
            cleaned_text = clean_text(text)
            full_text += cleaned_text + "\n\n"    

            
            
            
        #now get the youtube transcripts
        youtubetranscript = get_youtube_video_data(query)
        pattern = r"\[[^\]]+\]"
        updated_string = re.sub(pattern, "", youtubetranscript)
         
         

        full_text += clean_text(updated_string) 



        # Write full text to file
        #with open(contentfilename, 'w') as f:
            #f.write(full_text)

        # Extract keywords and weights from full text
        rake = Rake()
        keywords = rake.apply(full_text)
        keywords_with_weights = [{"keyword": keyword[0], "weight": keyword[1]} for keyword in keywords[:100]]
        prompt_keywords = [keyword["keyword"] for keyword in keywords_with_weights]

        """ with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Keyword", "Weight"])
            
            for keyword in keywords_with_weights:
                writer.writerow([keyword["keyword"], keyword["weight"]]) """
             
        # Clean keywords and write to CSV file
        cleaned_results = [clean_text(result2) for result2 in results2]

        # with open(relatedkeywordsfilename, "w", newline="") as f:
        #     writer = csv.writer(f)
        #     writer.writerow(cleaned_results)

        prompt1 = generate_prompt(query, "1", prompt_keywords, cleaned_results)   
        prompt2 = generate_prompt(query, "2", prompt_keywords, cleaned_results)  
        prompt3 = generate_prompt(query, "3", prompt_keywords, cleaned_results)   

        # Write full prompts to file
        # with open(prompt1filename, 'w') as f:
        #     f.write(prompt1)

        # # Write full prompts to file
        # with open(prompt2filename, 'w') as f:
        #     f.write(prompt2)   

        # # Write full prompts to file
        # with open(prompt3filename, 'w') as f:
        #     f.write(prompt3)      

        # Return comma-separated keywords
        comma_separated_keywords = ", ".join(prompt_keywords)
        related = ", ".join(results2)

        
        #return jsonify({"keywords": comma_separated_keywords,"related": related,"youtubetranscript": updated_string})
        return jsonify({"keywords": comma_separated_keywords,"related": related})


api.add_resource(HelloWorld, "/helloworld/<string:query>")

if __name__ == "__main__":
    app.run(debug=True,port=2000)
