from flask import Flask, render_template, request,jsonify
import requests
import os
import base64

app = Flask(__name__)

WORDPRESS_API_URL = "https://websitesgh.com/wp-json/wp/v2/posts"
IMAGE_FOLDER = "images/"
USERNAME = "info@websitesgh.com"
PASSWORD = "RH4fij2AmUwPduQ"

def create_wordpress_post(title, content, image_filename):
    # Read the image file
    image_path = os.path.join(IMAGE_FOLDER, image_filename)
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()

    # Prepare the data for the WordPress API request
    data = {
        "title": title,
        "content": content,
        "status": "draft",
        "post_type": "post",
    }

    # Create the headers for the API request
    headers = {
        "Content-Disposition": f'attachment; filename="{image_filename}"',
        "Content-Type": "image/png",
        "Authorization": f"Basic {base64.b64encode(f'{USERNAME}:{PASSWORD}'.encode()).decode()}"
    }

    # Send the API request to create the post
    response = requests.post(WORDPRESS_API_URL, data=data, headers=headers, files={"file": image_data})
    if response.status_code == 201:
        return True
    else:
        return response.status_code

@app.route('/')
def index():
    return render_template('wordpress_api_html.html')

@app.route('/create_post', methods=['POST'])
def create_post():
    title = request.form['title']
    content = request.form['content']
    image_file = request.files['image']

    # Save the image file
    image_filename = image_file.filename
    image_path = os.path.join(IMAGE_FOLDER, image_filename)
    image_file.save(image_path)

    success = create_wordpress_post(title, content, image_filename)

    if success:
        return jsonify(success)
    else:
        return jsonify(success)

if __name__ == '__main__':
    app.run(debug=True)
