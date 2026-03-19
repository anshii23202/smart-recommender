import requests
from config import OPENWEATHER_API_KEY

def get_weather(lat, lon):
    """
    Fetches current weather for a location.
    Returns a simple dict with condition, temp, and indoor suggestion.
    """
    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "lat":   lat,
        "lon":   lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"  # celsius
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code != 200:
            print("Weather API error:", response.status_code)
            return default_weather()

        data       = response.json()
        condition  = data["weather"][0]["main"].lower()
        temp       = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity   = data["main"]["humidity"]
        desc       = data["weather"][0]["description"]

        return {
            "condition":    condition,
            "temp":         round(temp),
            "feels_like":   round(feels_like),
            "humidity":     humidity,
            "description":  desc,
            "prefer_indoor": should_go_indoor(condition, temp, humidity),
            "weather_tip":  get_weather_tip(condition, temp)
        }

    except Exception as e:
        print("Weather fetch failed:", e)
        return default_weather()


def should_go_indoor(condition, temp, humidity):
    """Returns True if weather suggests staying indoors."""
    bad_conditions = ["rain", "drizzle", "thunderstorm", "snow", "fog", "mist", "haze"]
    too_hot  = temp > 38
    too_cold = temp < 10
    return condition in bad_conditions or too_hot or too_cold


def get_weather_tip(condition, temp):
    """Returns a human friendly weather message for the frontend."""
    if condition in ["rain", "drizzle"]:
        return "🌧️ It's raining — showing indoor places"
    if condition == "thunderstorm":
        return "⛈️ Thunderstorm outside — stay safe indoors!"
    if condition in ["fog", "mist", "haze"]:
        return "🌫️ Poor visibility — cozy indoor spots recommended"
    if condition == "snow":
        return "❄️ It's snowing — warm indoor places prioritised"
    if temp > 38:
        return "🥵 Very hot outside — air-conditioned venues recommended"
    if temp < 10:
        return "🥶 It's cold — warm indoor places recommended"
    if condition == "clear" and 20 <= temp <= 32:
        return "☀️ Beautiful weather — great for outdoor spots!"
    if condition == "clouds":
        return "⛅ Cloudy but fine — all places available"
    return f"🌡️ {temp}°C outside — enjoy your outing!"


def default_weather():
    """Fallback if API fails — assume neutral weather."""
    return {
        "condition":    "clear",
        "temp":         25,
        "feels_like":   25,
        "humidity":     50,
        "description":  "weather unavailable",
        "prefer_indoor": False,
        "weather_tip":  "🌡️ Weather data unavailable"
    }


def get_weather_score(place, prefer_indoor):
    """
    Returns a score boost or penalty based on whether
    a place is indoor or outdoor and what the weather is.
    """
    tags     = [t.lower() for t in place.get("tags", [])]
    category = place.get("category", "").lower()

    outdoor_keywords = ["park", "garden", "beach", "rooftop", "outdoor", "terrace"]
    indoor_keywords  = ["cafe", "restaurant", "mall", "museum", "cinema",
                        "fast_food", "bar", "library"]

    is_outdoor = any(k in tags or k in category for k in outdoor_keywords)
    is_indoor  = any(k in tags or k in category for k in indoor_keywords)

    if prefer_indoor:
        if is_outdoor: return -0.3   # penalise outdoor places in bad weather
        if is_indoor:  return +0.2   # boost indoor places in bad weather
    else:
        if is_outdoor: return +0.2   # boost outdoor places in good weather
        if is_indoor:  return  0.0   # neutral for indoor in good weather

    return 0.0