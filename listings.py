import requests
from flask import Flask, render_template, request

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
    
    base_url = 'http://localhost/websitesgh1/bcknd/?start=0'
    url = f'{base_url}&page={page}&orderby={orderby}&order={order}'
    
    response = requests.get(url)
    data = response.json()
    posts = data['posts']
    total_posts = data['total_posts']
    max_pages = data['max_pages']
    next_page_id = page + 1 if page < max_pages else None
    previous_page_id = page - 1 if page > 1 else None
    
    return render_template('listings.html', posts=posts, total_posts=total_posts, max_pages=max_pages, next_page_id=next_page_id, previous_page_id=previous_page_id)

if __name__ == '__main__':
    app.run(port=5007)
