from flask import Flask, jsonify
from flask_restful import Api, Resource
from multi_rake import Rake
import requests
from bs4 import BeautifulSoup           
import re
import csv
import time
from flask_cors import CORS
 
 
app = Flask(__name__)
api = Api(app)
CORS(app, resources={r"/*": {"origins": "*"}})

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
         
        prompt += f'Acting as a news journalist, Write creative news story titles from the following data. Put the titles in an <ul><li>title</li></ul> list format. Dont plagiarize the titles. Create your own unique story titles from the data:\n\n{content_keywords}\n'
       
    elif instruction == '3':
        prompt += f'Write a Glossary related contents" Return a tag results with the keywords in the Glossary in bold like <strong>Keyword</strong>: and definition of keyword in <p>Definition of Glossary</p> paragraphs elements. The following are the Glossary Keywords:\n\n'
        prompt += f"- {content_keywords}\n"
    return prompt

class HelloWorld(Resource):
    def get(self, query):
        # Get links from Google search API
        response = requests.get(f'https://www.googleapis.com/customsearch/v1?key=AIzaSyBepiIpYOYPhI2xA5cPB07iMpXrcxRdR5Q&cx=9559cb25da51941b9&q={query}&num=4&cr=gh&dateRestrict=d1')
        results = response.json().get('items', [])

        #page2 = requests.get(f'https://www.googleapis.com/customsearch/v1?key=AIzaSyBepiIpYOYPhI2xA5cPB07iMpXrcxRdR5Q&cx=9559cb25da51941b9&q={query}&num=10&start=11&cr=gh&dateRestrict=d1')
        #page2results = response.json().get('items', [])

        #page3 = requests.get(f'https://www.googleapis.com/customsearch/v1?key=AIzaSyBepiIpYOYPhI2xA5cPB07iMpXrcxRdR5Q&cx=9559cb25da51941b9&q={query}&num=10&start=21&cr=gh&dateRestrict=d1')
        #page3results = response.json().get('items', [])

        # Get links from Google autocomplete API
        # response2 = requests.get(f'https://suggestqueries.google.com/complete/search?client=firefox&q={query}')
        # results2 = response2.json()[1]
        #https://www.googleapis.com/customsearch/v1?key=YOUR_API_KEY&cx=YOUR_SEARCH_ENGINE_ID&q=SEARCH_QUERY&dateRestrict=d1
        #https://www.googleapis.com/customsearch/v1?key=YOUR_API_KEY&cx=YOUR_CX&q=your+query&dateRestrict=h2
        #https://www.googleapis.com/customsearch/v1?key=AIzaSyBepiIpYOYPhI2xA5cPB07iMpXrcxRdR5Q&cx=9559cb25da51941b9&q=news&tbm=nws&cr=gh&dateRestrict=d1
        #https://www.googleapis.com/customsearch/v1?key=AIzaSyBepiIpYOYPhI2xA5cPB07iMpXrcxRdR5Q&cx=9559cb25da51941b9&q=ghana%20news&cr=gh&dateRestrict=d1




        url = 'http://suggestqueries.google.com/complete/search'
        params = {'client': 'firefox', 'q': query}
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0'}
        response2 = requests.get(url, params=params, headers=headers)
        results2 = response2.json()[1]

        links = [result['link'] for result in results]
        #link2 = [page2result['link'] for page2result in page2results]
        #link3 = [page3result['link'] for page3result in page3results]

        filename = f"keywords/{query}.csv"
        contentfilename = f"scrapedcontents/{query}.txt"
        relatedkeywordsfilename = f"relatedkeywords/{query}.csv"
        prompt1filename = f"prompts/{query}_prompt1.txt"
        prompt2filename = f"prompts/{query}_prompt2.txt"
        prompt3filename = f"prompts/{query}_prompt3.txt"

        # Scrape and clean text from links
        full_text = ""
        exception =""
        for link in links[:10]:
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
            text = soup.get_text(separator='\n\n')
            cleaned_text = clean_text(text)
            full_text += cleaned_text + "\n\n"

        
        # Write full text to file
        with open(contentfilename, 'w') as f:
            f.write(full_text)

        # Extract keywords and weights from full text
        rake = Rake()
        keywords = rake.apply(full_text)
        keywords_with_weights = [{"keyword": keyword[0], "weight": keyword[1]} for keyword in keywords[:70]]
        prompt_keywords = keywords_with_weights

        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Keyword", "Weight"])
            
            for keyword in keywords_with_weights:
                writer.writerow([keyword["keyword"], keyword["weight"]])
                # prompt_keywords.append(keyword)
             
        # Clean keywords and write to CSV file
        cleaned_results = [clean_text(result2) for result2 in results2]
        cleaned_related_keywords2 = []
         
        with open(contentfilename, 'w') as f:
                f.write(full_text)

            # Extract keywords and weights from full text
        rake = Rake()
        keywords = rake.apply(full_text)
        keywords_with_weights = [{"keyword": keyword[0], "weight": keyword[1]} for keyword in keywords[:70]]
        prompt_keywords = keywords_with_weights

        with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Keyword", "Weight"])
                
                for keyword in keywords_with_weights:
                    writer.writerow([keyword["keyword"], keyword["weight"]])
                # prompt_keywords.append(keyword)
                
        
            # Clean keywords and write to CSV file
        cleaned_results = [clean_text(result2) for result2 in results2]
        cleaned_related_keywords2 = []
            
        with open(relatedkeywordsfilename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(cleaned_results)

            

        prompt1 = generate_prompt(query,"1",full_text,cleaned_results)   
        #prompt2 = generate_prompt(query,"2",prompt_keywords,cleaned_results)  
        prompt3 = generate_prompt(query,"3",prompt_keywords,cleaned_results)   

            # Write full prompts to file
        with open(prompt1filename, 'w') as f:
                f.write(prompt1)

            # Write full prompts to file
        #with open(prompt2filename, 'w') as f:
                #f.write(prompt2)   

            # Write full prompts to file
        with open(prompt3filename, 'w') as f:
                f.write(prompt3)      
            

        #return jsonify(keywords_with_weights) 
        return jsonify({"articleprompt": prompt1,"keywords": keywords_with_weights})
api.add_resource(HelloWorld, "/helloworld/<string:query>")

 





if __name__ == "__main__":
    app.run(debug=True)
