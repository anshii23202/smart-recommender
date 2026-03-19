from fetch_places import fetch_nearby_places
from ml_model import get_recommended_place_ids
from clustering import assign_clusters, train_kmeans
from weather import get_weather, get_weather_score
import math

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two GPS points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def get_recommendations(lat, lon, mood, user_id, top_n=10):
    """
    Returns top N places — boosted by kNN if user has rating history,
    otherwise falls back to location + mood scoring only.
    """
    mood_to_query = {
        'date':       'romantic restaurant',
        'work':       'cafe wifi',
        'quick bite': 'fast food',
        'casual':     'restaurant',
    }
    query  = mood_to_query.get(mood, 'restaurant')
    PLACES = fetch_nearby_places(lat, lon, mood_query=query)

    # Get place IDs that kNN thinks this user will like
    ml_recommended_ids = get_recommended_place_ids(user_id)
    weather = get_weather(lat, lon)

    nearby = []
    for place in PLACES:
        dist = haversine(lat, lon, place['lat'], place['lon'])
        place['distance_km'] = round(dist, 2)
        place['score'] = compute_score(place, mood, dist, ml_recommended_ids, weather['prefer_indoor'])
        nearby.append(place)

    nearby.sort(key=lambda x: x['score'], reverse=True)
    # Train K-Means on these places and assign cluster labels
    train_kmeans(nearby)
    nearby = assign_clusters(nearby)
    return {
        "places":  nearby[:top_n],
        "weather": {"weather_tip": ""}   
    }

def compute_score(place, mood, distance, ml_recommended_ids=[], prefer_indoor=False):
    rating_score    = place.get('rating', 3.0) / 5.0
    proximity_score = max(0, 1 - distance / 5)

    mood_tags = {
        'date':       ['romantic', 'fine dining', 'bar'],
        'work':       ['cafe', 'wifi', 'quiet'],
        'quick bite': ['fast food', 'street food', 'cafe'],
        'casual':     ['restaurant', 'park', 'cafe'],
    }
    tags       = mood_tags.get(mood, [])
    mood_match = any(t in place.get('tags', []) for t in tags)
    mood_score = 0.2 if mood_match else 0.0

    ml_score      = 0.3 if place.get('id') in ml_recommended_ids else 0.0
    weather_score = get_weather_score(place, prefer_indoor)

    return (rating_score * 0.35) + (proximity_score * 0.25) + mood_score + ml_score + weather_score