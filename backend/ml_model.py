import numpy as np
import pickle
import os
from sklearn.neighbors import NearestNeighbors
from database import get_connection

MODEL_PATH = os.path.join(os.path.dirname(__file__), '../models/knn_model.pkl')
MATRIX_PATH = os.path.join(os.path.dirname(__file__), '../models/matrix.pkl')

def build_ratings_matrix():
    """
    Reads all ratings from DB and builds a users x places matrix.
    Each row = one user, each column = one place, value = rating (0 if not rated).
    """
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute('SELECT user_id, place_id, rating FROM ratings').fetchall()
    conn.close()

    if len(rows) < 2:
        return None, None, None  # not enough data yet

    # Get unique users and places
    user_ids  = list(set(r['user_id']  for r in rows))
    place_ids = list(set(r['place_id'] for r in rows))

    # Map them to matrix indices
    user_index  = {uid: i for i, uid in enumerate(user_ids)}
    place_index = {pid: i for i, pid in enumerate(place_ids)}

    # Build empty matrix
    matrix = np.zeros((len(user_ids), len(place_ids)))

    # Fill in ratings
    for r in rows:
        u = user_index[r['user_id']]
        p = place_index[r['place_id']]
        matrix[u][p] = r['rating']

    return matrix, user_index, place_index

def train_model():
    """Trains the kNN model and saves it to disk."""
    matrix, user_index, place_index = build_ratings_matrix()

    if matrix is None:
        print("Not enough ratings data to train yet.")
        return False

    # Train kNN — finds the 3 most similar users for any given user
    model = NearestNeighbors(n_neighbors=min(3, len(user_index)),
                             metric='cosine',
                             algorithm='brute')
    model.fit(matrix)

    # Save model and matrix info to disk
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)

    with open(MATRIX_PATH, 'wb') as f:
        pickle.dump({
            'matrix':      matrix,
            'user_index':  user_index,
            'place_index': place_index
        }, f)

    print(f"Model trained on {len(user_index)} users and {len(place_index)} places!")
    return True

def get_recommended_place_ids(user_id, top_n=10):
    """
    Returns place IDs that similar users liked but this user hasn't rated yet.
    Falls back to empty list if model not trained yet.
    """
    if not os.path.exists(MODEL_PATH) or not os.path.exists(MATRIX_PATH):
        return []  # model not trained yet, no problem

    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)

    with open(MATRIX_PATH, 'rb') as f:
        data = pickle.load(f)

    matrix      = data['matrix']
    user_index  = data['user_index']
    place_index = data['place_index']

    # If this user has no ratings yet, can't personalise
    if user_id not in user_index:
        return []

    # Get this user's row in the matrix
    u_idx       = user_index[user_id]
    user_vector = matrix[u_idx].reshape(1, -1)

    # Find similar users
    distances, indices = model.kneighbors(user_vector)
    similar_user_indices = indices[0]

    # Collect place IDs that similar users rated highly (4 or 5 stars)
    # but that THIS user has NOT rated yet
    my_rated = set(i for i, v in enumerate(matrix[u_idx]) if v > 0)

    recommended = {}
    for sim_idx in similar_user_indices:
        if sim_idx == u_idx:
            continue  # skip self
        for place_idx, rating in enumerate(matrix[sim_idx]):
            if rating >= 4 and place_idx not in my_rated:
                place_id = [k for k, v in place_index.items() if v == place_idx]
                if place_id:
                    recommended[place_id[0]] = recommended.get(place_id[0], 0) + rating

    # Sort by combined score from similar users
    sorted_places = sorted(recommended.items(), key=lambda x: x[1], reverse=True)
    return [pid for pid, _ in sorted_places[:top_n]]