from flask import Flask, jsonify
from flask_restful import Api, Resource
from multi_rake import Rake
import requests
from bs4 import BeautifulSoup           
import re
import csv
import time
from flask_cors import CORS
from yake import KeywordExtractor
 
 
app = Flask(__name__)
api = Api(app)
CORS(app, resources={r"/*": {"origins": "*"}})


def generate_keywords(text):
     # Create a Yake extractor with English as the language
    kw_extractor = KeywordExtractor(lan="en", n=3, dedupLim=0.9, top=70, features=None)
    #kw_extractor = KeywordExtractor(lan="en", n=2, dedupLim=0.9, top=70, features=["CI"])
    
    # Extract keywords from the text
    keywords = kw_extractor.extract_keywords(text)
    
    # Sort the keywords by score in descending order
    keywords.sort(key=lambda x: x[1])
    
    # Extract the keyword text and score from the Yake results
    keywords_list = [{"keyword": keyword[0], "score": keyword[1]} for keyword in keywords]
    
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
        prompt += f'As a content creator, you understand the importance of incorporating keywords into your articles to attract organic traffic. However, it is equally essential to maintain a healthy keyword density and avoid excessive repetition.Your task is to write an SEO-optimized article that adheres to the recommended keyword density guidelines, limiting the repetition of main keywords to no more than 0.7% of the content. Dive deep into the topic of your choice, be it a trending industry, a current event, or a niche subject that resonates with your audience.Ensure that your article flows naturally, provides valuable information, and engages readers. Employ creative writing techniques, use synonyms, and explore related terms to maintain keyword diversity without compromising on readability. Your ultimate goal is to captivate both search engine algorithms and human readers. Remember, the success of your article lies in striking a balance between optimizing for search engines and delivering high-quality content. Emphasize the value you can provide to your audience while staying within the specified keyword density limit. Use the following title for the article: "{main_keyword}". Write more than 1500 words. Create subtopics from the following: {related_keywords}\n\n Use the following as keywords for the article: KEYWORDS:'
        prompt += f"- {content_keywords}\n"
    elif instruction == '2':
        prompt += f'Write related contents using the following keywords as subtopics. Use the following tag formats: <h3>Keyword</h3> and <p>Related contents to write</p>. Dont add conclusion and dont add introduction. Just describe and write a great content on each related keyword. IMPORTANT: Ignore the first keyword in the keyword list:\n\n'
        prompt += f"- {related_keywords}\n"
    elif instruction == '3':
        prompt += f'Write a Glossary related contents using "{main_keyword} Glossary" as the title and the following. Return a tag results with the keywords in the Glossary in bold like <strong>Keyword</strong>: and definition of keyword in <p>Definition of Glossary</p> paragraphs elements. The following are the Glossary Keywords:\n\n'
        prompt += f"- {content_keywords}\n"
    return prompt

class kasai(Resource):
    def get(self, query):
        # Get links from Google search API
        response = requests.get(f'https://www.googleapis.com/customsearch/v1?key=AIzaSyBepiIpYOYPhI2xA5cPB07iMpXrcxRdR5Q&cx=9559cb25da51941b9&q={query}&num=10')
        results = response.json().get('items', [])

        page2 = requests.get(f'https://www.googleapis.com/customsearch/v1?key=AIzaSyBepiIpYOYPhI2xA5cPB07iMpXrcxRdR5Q&cx=9559cb25da51941b9&q={query}&num=10&start=11')
        page2results = response.json().get('items', [])

        page3 = requests.get(f'https://www.googleapis.com/customsearch/v1?key=AIzaSyBepiIpYOYPhI2xA5cPB07iMpXrcxRdR5Q&cx=9559cb25da51941b9&q={query}&num=10&start=21')
        page3results = response.json().get('items', [])

        # Get links from Google autocomplete API
        # response2 = requests.get(f'https://suggestqueries.google.com/complete/search?client=firefox&q={query}')
        # results2 = response2.json()[1]
        #https://www.googleapis.com/customsearch/v1?key=YOUR_API_KEY&cx=YOUR_SEARCH_ENGINE_ID&q=SEARCH_QUERY&dateRestrict=d1
        #https://www.googleapis.com/customsearch/v1?key=YOUR_API_KEY&cx=YOUR_CX&q=your+query&dateRestrict=h2
        #https://www.googleapis.com/customsearch/v1?key=AIzaSyBepiIpYOYPhI2xA5cPB07iMpXrcxRdR5Q&cx=9559cb25da51941b9&q=news&tbm=nws&cr=gh&dateRestrict=d1
        #




        url = 'http://suggestqueries.google.com/complete/search'
        params = {'client': 'firefox', 'q': query}
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0'}
        response2 = requests.get(url, params=params, headers=headers)
        results2 = response2.json()[1]

        links = [result['link'] for result in results]
        link2 = [page2result['link'] for page2result in page2results]
        link3 = [page3result['link'] for page3result in page3results]

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
            paragraphs = soup.find_all(['p'])

            text = '\n\n'.join([p.get_text(separator=' ') for p in paragraphs])
            cleaned_text = clean_text(text)
            full_text += cleaned_text + "\n\n"    
            
            """ soup = BeautifulSoup(page.content, 'html.parser')
            text = soup.get_text(separator='\n\n')
            cleaned_text = clean_text(text)
            full_text += cleaned_text + "\n\n" """

        for link in link2[:10]:
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
            
            """ soup = BeautifulSoup(page.content, 'html.parser')
            text = soup.get_text(separator='\n\n')
            cleaned_text = clean_text(text)
            full_text += cleaned_text + "\n\n" """


        for link in link3[:10]:
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

            """ soup = BeautifulSoup(page.content, 'html.parser')
            text = soup.get_text(separator='\n\n')
            cleaned_text = clean_text(text)
            full_text += cleaned_text + "\n\n" """
            
            
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
                 

            

        prompt1 = generate_prompt(query,"1",prompt_keywords,cleaned_results)   
        prompt2 = generate_prompt(query,"2",prompt_keywords,cleaned_results)  
        prompt3 = generate_prompt(query,"3",prompt_keywords,cleaned_results)   

            # Write full prompts to file
        with open(prompt1filename, 'w') as f:
                f.write(prompt1)

            # Write full prompts to file
        with open(prompt2filename, 'w') as f:
                f.write(prompt2)   

            # Write full prompts to file
        with open(prompt3filename, 'w') as f:
                f.write(prompt3)      

        #keywords = generate_keywords(full_text)
        prompt_keywords_with_weights = keywords_with_weights.copy()
        #prompt_keywords_with_weights.append({"keyword": "prompt1", "weight": 1})
        return jsonify({"articleprompt": prompt1,"relatedkeywordsprompt":prompt2,"glossaryprompt":prompt3})

            

        #return jsonify(keywords_with_weights) 
        #return jsonify(keywords)
api.add_resource(kasai, "/kasai/<string:query>")

 

if __name__ == "__main__":
    app.run(debug=True)
