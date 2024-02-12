from flask import Flask, jsonify, request, render_template
import random
import numpy as np
import tensorflow as tf
import json

app = Flask(__name__)

# Step 1: Data Preparation from JSON
def prepare_data_from_json():
    with open('lottogen/your_data.json', 'r') as file:
        data = json.load(file)

    data = np.array(data)

    # Select 25 numbers from 5 sequential rows as input
    X = data[:5, :25]

    # Select the first 5 fields of the 6th row as output
    y = data[5, :5]

    return X, y

# Step 2: TensorFlow Model Development
def build_model(input_dim, output_dim):
    model = tf.keras.models.Sequential()
    model.add(tf.keras.layers.Dense(64, activation='relu', input_shape=(input_dim,)))
    model.add(tf.keras.layers.Dense(32, activation='relu'))
    model.add(tf.keras.layers.Dense(output_dim, activation='linear'))
    model.compile(loss='mean_squared_error', optimizer='adam')
    return model

# Step 3: Training the Model
def train_model(model, X, y):
    model.fit(X, y, epochs=10, batch_size=32)

# Step 4: Saving the Trained Model
def save_model(model):
    model.save('trained_model.h5')

# Step 5: Loading the Trained Model
def load_model():
    loaded_model = tf.keras.models.load_model('trained_model.h5')
    return loaded_model

# Step 6: Prediction Using the Loaded Model
def make_prediction(model, data):
    predictions = model.predict(data)
    return predictions.tolist()

def generate_random_numbers(num_rows):
    rows = []
    for _ in range(num_rows):
        row = random.sample(range(1, 91), 10)
        rows.append(row)
    return rows

def insert_data_into_json(rows):
    with open('lottogen/your_data.json', 'r') as file:
        data = json.load(file)

    data.extend(rows)

    with open('lottogen/your_data.json', 'w') as file:
        json.dump(data, file)

@app.route('/generate/<int:num_rows>', methods=['GET'])
def generate_and_insert_data(num_rows):
    # Step 1: Generate Random Numbers
    random_rows = generate_random_numbers(num_rows)

    # Step 2: Insert Data into JSON
    insert_data_into_json(random_rows)

    return f'Random {num_rows} rows generated and inserted into the JSON data.'

@app.route('/train', methods=['GET'])
def train_and_save_model():
    # Step 1: Data Preparation from JSON
    X, y = prepare_data_from_json()

    # Step 2: TensorFlow Model Development
    model = build_model(input_dim=X.shape[1], output_dim=y.shape[0])

    # Step 3: Training the Model
    train_model(model, X, y)

    # Step 4: Saving the Trained Model
    save_model(model)

    return 'Model trained and saved.'

@app.route('/predict', methods=['GET'])
def predict():
    # Step 5: Loading the Trained Model
    loaded_model = load_model()

    # Step 6: Prediction Using the Loaded Model
    data = request.get_json()
    data = np.array(data)
    predictions = make_prediction(loaded_model, data)

    return jsonify(predictions)

@app.route('/getall', methods=['GET'])
def get_all_numbers():
    with open('lottogen/your_data.json', 'r') as file:
        data = json.load(file)

    return render_template('numbers.html', data=data)

@app.route('/getlast/<int:num_rows>', methods=['GET'])
def get_last_numbers(num_rows):
    with open('lottogen/your_data.json', 'r') as file:
        data = json.load(file)

    data = data[-num_rows:]

    return render_template('numbers.html', data=data)

@app.route('/search/<string:numbers>', methods=['GET'])
def search_numbers(numbers):
    search_list = [int(number) for number in numbers.split(',')]

    with open('lottogen/your_data.json', 'r') as file:
        data = json.load(file)

    filtered_data = []
    for row in data:
        if all(number in row for number in search_list):
            filtered_data.append(row)

    return render_template('numbers.html', data=filtered_data)

if __name__ == '__main__':
    app.run()
