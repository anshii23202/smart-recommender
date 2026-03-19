from flask import Flask, request, jsonify
from flask_cors import CORS
from recommender import get_recommendations
from auth import register_user, login_user, save_rating, save_visit, get_user_history
from database import init_db
from ml_model import train_model

app = Flask(__name__)
CORS(app)

# Create tables when server starts
init_db()

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    lat = data.get('lat')
    lon = data.get('lon')
    mood = data.get('mood', 'casual')
    user_id = data.get('user_id', 'guest')
    results = get_recommendations(lat, lon, mood, user_id)
    return jsonify(results)

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    result = register_user(
        data.get('name'),
        data.get('email'),
        data.get('password')
    )
    return jsonify(result)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    result = login_user(data.get('email'), data.get('password'))
    return jsonify(result)

@app.route('/rate', methods=['POST'])
def rate():
    data = request.json
    result = save_rating(
        data.get('user_id'),
        data.get('place_id'),
        data.get('place_name'),
        data.get('rating')
    )
    return jsonify(result)

@app.route('/visit', methods=['POST'])
def visit():
    data = request.json
    result = save_visit(
        data.get('user_id'),
        data.get('place_id'),
        data.get('place_name'),
        data.get('mood')
    )
    return jsonify(result)

@app.route('/history/<int:user_id>', methods=['GET'])
def history(user_id):
    result = get_user_history(user_id)
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'running'})

@app.route('/train', methods=['POST'])
def train():
    success = train_model()
    if success:
        return jsonify({'message': 'Model trained successfully!'})
    return jsonify({'message': 'Not enough ratings yet. Rate more places first!'})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)