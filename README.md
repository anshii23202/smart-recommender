# 🗺️ Smart Nearby Places Recommender

A full-stack AI-powered web application that recommends nearby restaurants, cafes, and venues based on your **live location**, **mood**, and **personal rating history** — using machine learning to get smarter with every use.

---

## 🌟 Features

- 📍 **Live location detection** — uses GPS to find places near you in real time
- 🎭 **Mood-based filtering** — choose from Casual, Date Night, Work/Study, or Quick Bite
- 🤖 **ML-powered recommendations** — kNN collaborative filtering learns from user ratings
- ⭐ **Rate places** — 1–5 star ratings stored and used to improve future suggestions
- 🕐 **Visit history** — tracks everywhere you've been
- 👤 **User accounts** — secure registration and login with hashed passwords
- 🌦️ **Weather context** *(coming soon)* — suggests indoor/outdoor spots based on live weather
- 🗺️ **Interactive map** *(coming soon)* — see all recommendations as pins on a map

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Flask, Flask-CORS |
| Database | SQLite |
| Machine Learning | scikit-learn (kNN, K-Means) |
| Places Data | OpenStreetMap via Overpass API |
| Weather | OpenWeatherMap API |
| Distance | Haversine formula |

---

## 🧠 How the ML Works

This app uses **collaborative filtering** with k-Nearest Neighbours (kNN):

1. Every time a user rates a place, it's stored in a `ratings` table
2. When `/train` is called, the app builds a **users × places matrix**
3. The kNN model finds users with similar taste to the current user
4. Places those similar users loved — but the current user hasn't visited — get a **score boost**
5. New users with no history are handled gracefully with location + mood scoring only (cold start solution)

---

## 📁 Project Structure

```
smart-recommender/
│
├── backend/
│   ├── app.py              # Flask API — all routes
│   ├── recommender.py      # Scoring and ranking logic
│   ├── ml_model.py         # kNN model training and prediction
│   ├── fetch_places.py     # OpenStreetMap place fetching
│   ├── auth.py             # Register, login, ratings, history
│   ├── database.py         # SQLite setup and connection
│   ├── weather.py          # OpenWeatherMap integration
│   ├── config.py           # API keys (never commit this!)
│   └── requirements.txt    # Python dependencies
│
├── frontend/
│   ├── index.html          # Main UI
│   ├── app.js              # All frontend logic
│   └── style.css           # Styling
│
├── data/
│   └── users.db            # SQLite database (auto-created)
│
├── models/
│   ├── knn_model.pkl       # Trained kNN model (auto-created)
│   └── matrix.pkl          # Ratings matrix (auto-created)
│
└── notebooks/
    └── explore.ipynb       # Data exploration (optional)
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js (for serving the frontend)

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/smart-recommender.git
cd smart-recommender
```

### 2. Set up the backend
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Add your API key
Create `backend/config.py`:
```python
OPENWEATHER_API_KEY = "your_openweathermap_key_here"
```
Get a free key at [openweathermap.org](https://openweathermap.org)

### 4. Start the backend
```bash
python app.py
```
You should see: `Database ready!` and `Running on http://127.0.0.1:5000`

### 5. Start the frontend
Open a new terminal:
```bash
cd frontend
npx serve .
```
Visit `http://localhost:3000` in your browser.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/register` | Create a new user account |
| POST | `/login` | Login with email and password |
| POST | `/recommend` | Get personalised place recommendations |
| POST | `/rate` | Save a star rating for a place |
| POST | `/visit` | Record a place visit |
| POST | `/train` | Train the kNN ML model on current ratings |
| GET | `/history/<user_id>` | Get a user's visit history |
| GET | `/health` | Check if server is running |

---

## 🔒 Security Notes

- Passwords are **hashed** using Werkzeug — never stored as plain text
- `config.py` containing API keys is excluded from version control
- Always add `config.py` to your `.gitignore` before pushing to GitHub

---

## 🗺️ Roadmap

- [x] Live place data from OpenStreetMap
- [x] User accounts with secure authentication
- [x] kNN collaborative filtering
- [x] Mood-based recommendation filtering
- [x] Visit history and star ratings
- [ ] Weather-aware indoor/outdoor suggestions
- [ ] Interactive map with place pins
- [ ] K-Means place clustering
- [ ] Deployment to Render / Railway

---

## 👨‍💻 Built With

This project was built from scratch as a learning exercise covering:
- Full-stack web development
- RESTful API design
- Machine learning with scikit-learn
- Geospatial data and the Haversine formula
- SQLite database design
- User authentication and password hashing

---

## 📄 License

MIT License — free to use and modify.