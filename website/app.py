"""
A simple Flask app that integrates:
 - user signup & login (with local JSON backup of user info)
 - storing a generated API key in a database
 - a scoreboard/leaderboard
 - an API endpoint to POST agent scores using the API key
 - a user profile page to display the API key

Database: SQLite in local file 'leaderboard.db'
Additionally, user registration data is mirrored to 'users.json'.
"""

import os
import json
import secrets

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "super_secret_key_for_demo"

# Using a local SQLite DB
db_path = os.path.join(os.path.dirname(__file__), 'leaderboard.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Path for local JSON user data
JSON_USERS_PATH = os.path.join(os.path.dirname(__file__), "users.json")

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    api_key = db.Column(db.String(100), unique=True, nullable=False)

class Scoreboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    agent_name = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Float, nullable=False)

# -----------------------------------------------------------------------------
# Create DB if not exists
# -----------------------------------------------------------------------------
@app.before_request
def create_tables():
    db.create_all()
    # Also ensure a users.json file exists
    if not os.path.exists(JSON_USERS_PATH):
        with open(JSON_USERS_PATH, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def save_user_to_json(username, password, api_key):
    """
    Mirror the new user's data to 'users.json'.
    """
    # Load existing data
    try:
        with open(JSON_USERS_PATH, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
    except Exception:
        users_data = []

    # Append the new user
    new_user_entry = {
        "username": username,
        "password": password,
        "api_key": api_key
    }
    users_data.append(new_user_entry)

    # Write back
    with open(JSON_USERS_PATH, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, indent=2)

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def register():
    """
    Registers a new user. Also saves to 'users.json' in addition to the DB.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if username already exists in DB
        existing = User.query.filter_by(username=username).first()
        if existing:
            flash("Username already taken.")
            return redirect(url_for('register'))

        # Generate an API key
        api_key = secrets.token_hex(16)

        # Save to DB
        new_user = User(username=username, password=password, api_key=api_key)
        db.session.add(new_user)
        db.session.commit()

        # Also save to local JSON
        save_user_to_json(username, password, api_key)

        flash("Registration successful. Please log in.")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET','POST'])
def login():
    """
    Logs the user in if credentials match an entry in the DB.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = user.username
            flash("Login successful!")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials.")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/leaderboard')
def leaderboard():
    """
    Shows the top 10 scores in descending order.
    """
    scores = Scoreboard.query.order_by(Scoreboard.score.desc()).limit(10).all()
    return render_template('leaderboard.html', scores=scores)


@app.route('/profile')
def profile():
    """
    Displays the logged-in user's info, including API key.
    """
    if 'username' not in session:
        flash("Please login first.")
        return redirect(url_for('login'))

    username = session['username']
    user = User.query.filter_by(username=username).first()
    if not user:
        flash("No user found. Please register.")
        return redirect(url_for('register'))

    return render_template('profile.html', username=user.username, api_key=user.api_key)

@app.route('/submit_score', methods=['POST'])
def submit_score():
    """
    A simple route for submitting scores from a form (example usage).
    For now, it just saves them to the scoreboard with the posted data.
    """
    username = request.form.get('username')
    agent_name = request.form.get('agent_name')
    score_str = request.form.get('score')

    # Validate
    if not (username and agent_name and score_str):
        return "Missing fields", 400
    try:
        score = float(score_str)
    except:
        return "Invalid score", 400

    # Save
    entry = Scoreboard(username=username, agent_name=agent_name, score=score)
    db.session.add(entry)
    db.session.commit()

    return "Score submitted. Check leaderboard!"

@app.route('/submit_agent_score_api', methods=['POST'])
def submit_agent_score_api():
    """
    This endpoint is for automated posting from your main script or benchmark pipeline.
    It expects 'api_key', 'agent_name', and 'score' in the form data (or JSON).
    We look up the user by the provided API key, and if valid, record the score.
    Returns JSON indicating success/failure.
    """
    api_key = request.form.get('api_key') or request.json.get('api_key') if request.is_json else None
    agent_name = request.form.get('agent_name') or request.json.get('agent_name') if request.is_json else None
    score_str = request.form.get('score') or request.json.get('score') if request.is_json else None

    if not (api_key and agent_name and score_str):
        return {"status": "error", "message": "Missing fields (api_key, agent_name, score)."}, 400

    # Validate score
    try:
        score = float(score_str)
    except ValueError:
        return {"status": "error", "message": "Invalid score format."}, 400

    # Find user by API key
    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return {"status": "error", "message": "Invalid API key."}, 403

    # Insert scoreboard record
    entry = Scoreboard(username=user.username, agent_name=agent_name, score=score)
    db.session.add(entry)
    db.session.commit()

    return {"status": "success", "message": "Score saved.", "username": user.username}, 200


if __name__ == '__main__':
    # If you want to run this app directly (not behind gunicorn, etc.):
    app.run(debug=True)
