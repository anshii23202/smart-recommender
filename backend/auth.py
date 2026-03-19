from werkzeug.security import generate_password_hash, check_password_hash
from database import get_connection

def register_user(name, email, password):
    """Creates a new user. Returns success or error message."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check if email already exists
    existing = cursor.execute(
        'SELECT id FROM users WHERE email = ?', (email,)
    ).fetchone()

    if existing:
        conn.close()
        return {'success': False, 'message': 'Email already registered'}

    # Hash the password — never store plain text!
    hashed = generate_password_hash(password)

    cursor.execute(
        'INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
        (name, email, hashed)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    return {'success': True, 'user_id': user_id, 'name': name}

def login_user(email, password):
    """Checks credentials. Returns user info or error."""
    conn = get_connection()
    cursor = conn.cursor()

    user = cursor.execute(
        'SELECT * FROM users WHERE email = ?', (email,)
    ).fetchone()
    conn.close()

    if not user:
        return {'success': False, 'message': 'Email not found'}

    if not check_password_hash(user['password'], password):
        return {'success': False, 'message': 'Wrong password'}

    return {
        'success': True,
        'user_id': user['id'],
        'name': user['name'],
        'favourite_mood': user['favourite_mood']
    }

def save_rating(user_id, place_id, place_name, rating):
    """Saves a user's rating for a place."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO ratings (user_id, place_id, place_name, rating) VALUES (?, ?, ?, ?)',
        (user_id, place_id, place_name, rating)
    )
    conn.commit()
    conn.close()
    return {'success': True}

def save_visit(user_id, place_id, place_name, mood):
    """Records that a user visited a place."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO history (user_id, place_id, place_name, mood) VALUES (?, ?, ?, ?)',
        (user_id, place_id, place_name, mood)
    )
    conn.commit()
    conn.close()
    return {'success': True}

def get_user_history(user_id):
    """Returns all places a user has visited."""
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute(
        'SELECT * FROM history WHERE user_id = ? ORDER BY visited_at DESC',
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]