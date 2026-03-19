import requests

def fetch_nearby_places(lat, lon, mood_query="restaurant", radius=5000):
    """
    Fetches real nearby places using OpenStreetMap - FREE, no API key needed!
    """

    # Map mood keywords to OpenStreetMap categories
    mood_to_osm = {
        'restaurant':        'amenity=restaurant',
        'romantic restaurant':'amenity=restaurant',
        'cafe wifi':         'amenity=cafe',
        'fast food':         'amenity=fast_food',
        'cafe':              'amenity=cafe',
    }

    osm_filter = mood_to_osm.get(mood_query, 'amenity=restaurant')
    key, value = osm_filter.split('=')

    # Overpass API query
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    node["{key}"="{value}"](around:{radius},{lat},{lon});
    out 20;
    """

    response = requests.post(overpass_url, data=query)

    if response.status_code != 200:
        print("Error fetching places:", response.status_code)
        return []

    elements = response.json().get("elements", [])

    places = []
    for p in elements:
        tags = p.get("tags", {})
        name = tags.get("name")
        if not name:
            continue  # skip places with no name

        places.append({
            "id": str(p.get("id", "")),
            "name": name,
            "category": tags.get("amenity", "place"),
            "lat": p.get("lat"),
            "lon": p.get("lon"),
            "rating": float(tags.get("stars", 3.5)),
            "tags": [tags.get("amenity", ""), tags.get("cuisine", "")],
            "address": tags.get("addr:street", "New Delhi")
        })

    return places