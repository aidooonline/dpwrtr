import requests
from flask import Flask, render_template, request
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/listings')
def listings():
    page = int(request.args.get('page', 1))
    category = request.args.get('category', None)
    location = request.args.get('location', None)
    min_word_count = int(request.args.get('min_word_count', 1))
    max_word_count = int(request.args.get('max_word_count', 1))
    orderby = request.args.get('orderby', 'date')
    order = request.args.get('order', 'DESC')
    
    base_url = 'https://websitesgh.com/bcknd/listingsingle.php?start=0'
    url = f'{base_url}&page={page}&orderby={orderby}&order={order}'
    
    response = requests.get(url)
    data = response.json()
    posts = data['posts']
    
    # Extract text from HTML strings in post content
    
    
    for post in posts:
        content_html = post['content']
        soup = BeautifulSoup(content_html, 'html.parser')
    
        # Remove all button elements from the soup
        buttons = soup.find_all('button')
        for button in buttons:
            button.decompose()

        div = soup.find('div', id='getemailid')
    
        # Remove the div if it exists
        if div:
            div.decompose()
    
    # Get the text from the modified soup
    content_text = soup.get_text()
    
    # Store the content text in the post dictionary
    post['content_text'] = content_text


    
    
    total_posts = data['total_posts']
    max_pages = data['max_pages']
    next_page_id = page + 1 if page < max_pages else None
    previous_page_id = page - 1 if page > 1 else None
    
    return render_template('listingsingle.html', posts=posts, total_posts=total_posts, max_pages=max_pages, next_page_id=next_page_id, previous_page_id=previous_page_id)

if __name__ == '__main__':
    app.run(port=5002)
