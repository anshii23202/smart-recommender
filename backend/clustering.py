import numpy as np
import pickle
import os
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

MODEL_PATH  = os.path.join(os.path.dirname(__file__), '../models/kmeans.pkl')
SCALER_PATH = os.path.join(os.path.dirname(__file__), '../models/scaler.pkl')

# Cluster labels — we decide what each cluster means
CLUSTER_LABELS = {
    0: {"name": "Dining",   "emoji": "🍽️", "moods": ["date", "casual"]},
    1: {"name": "Cafes",    "emoji": "☕",  "moods": ["work", "casual"]},
    2: {"name": "Outdoors", "emoji": "🌳",  "moods": ["casual"]},
    3: {"name": "Fast Food","emoji": "🍔",  "moods": ["quick bite"]},
}

def place_to_features(place):
    """
    Converts a place dict into a numeric feature vector for K-Means.
    K-Means only understands numbers — not text.
    """
    category = place.get("category", "").lower()
    tags     = [t.lower() for t in place.get("tags", [])]

    # Feature 1: is it a cafe?
    is_cafe      = 1 if "cafe" in category or "cafe" in tags else 0
    # Feature 2: is it a restaurant?
    is_restaurant = 1 if "restaurant" in category else 0
    # Feature 3: is it fast food?
    is_fastfood  = 1 if "fast_food" in category or "fast food" in tags else 0
    # Feature 4: is it outdoor?
    is_outdoor   = 1 if any(k in tags for k in ["park", "garden", "outdoor"]) else 0
    # Feature 5: rating (0-5 scale)
    rating       = place.get("rating", 3.0)
    # Feature 6: distance (0-5 km scale)
    distance     = min(place.get("distance_km", 2.5), 5.0)

    return [is_cafe, is_restaurant, is_fastfood, is_outdoor, rating, distance]

def train_kmeans(places, n_clusters=4):
    """
    Trains K-Means on a list of places and saves the model.
    Call this after fetching places.
    """
    if len(places) < n_clusters:
        print("Not enough places to cluster.")
        return False

    # Build feature matrix
    features = np.array([place_to_features(p) for p in places])

    # Scale features so distance and rating don't dominate
    scaler  = StandardScaler()
    scaled  = scaler.fit_transform(features)

    # Train K-Means
    kmeans  = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    kmeans.fit(scaled)

    # Save both model and scaler
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(kmeans, f)
    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)

    print(f"K-Means trained on {len(places)} places into {n_clusters} clusters!")
    return True

def assign_clusters(places):
    """
    Assigns a cluster label to each place.
    If model not trained yet, assigns a basic label from category.
    """
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        # Fallback — simple rule-based clustering
        return assign_clusters_fallback(places)

    with open(MODEL_PATH, 'rb') as f:
        kmeans = pickle.load(f)
    with open(SCALER_PATH, 'rb') as f:
        scaler = pickle.load(f)

    features = np.array([place_to_features(p) for p in places])
    scaled   = scaler.transform(features)
    labels   = kmeans.predict(scaled)

    for i, place in enumerate(places):
        cluster_id           = int(labels[i])
        cluster_info         = CLUSTER_LABELS.get(cluster_id, {"name": "Other", "emoji": "📍", "moods": []})
        place['cluster_id']  = cluster_id
        place['cluster_name']= cluster_info['name']
        place['cluster_emoji']= cluster_info['emoji']

    return places

def assign_clusters_fallback(places):
    """Simple rule-based fallback when model isn't trained yet."""
    for place in places:
        category = place.get("category", "").lower()
        if "cafe" in category:
            place['cluster_id']   = 1
            place['cluster_name'] = "Cafes"
            place['cluster_emoji']= "☕"
        elif "fast_food" in category:
            place['cluster_id']   = 3
            place['cluster_name'] = "Fast Food"
            place['cluster_emoji']= "🍔"
        elif "park" in category or "garden" in category:
            place['cluster_id']   = 2
            place['cluster_name'] = "Outdoors"
            place['cluster_emoji']= "🌳"
        else:
            place['cluster_id']   = 0
            place['cluster_name'] = "Dining"
            place['cluster_emoji']= "🍽️"
    return places