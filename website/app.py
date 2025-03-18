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
import hashlib
from datetime import timedelta

from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect, CSRFError
import cryptography

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Generate a secure random key
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session expires after 7 days
app.config['SESSION_COOKIE_SECURE'] = False  # Set to False for development without HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # CSRF token valid for 1 hour

# Initialize CSRF protection
csrf = CSRFProtect(app)

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
    """User model for authentication and API key storage"""
    __tablename__ = 'users'  # Explicitly name the table to avoid SQLite issues
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)  # Store password hash, not plain password
    api_key = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    
    # Add relationship to scores - we'll use the `backref` approach instead of a complex relationship
    scores = db.relationship('Scoreboard', backref='user_obj', lazy=True, 
                            cascade="all, delete-orphan")

class Scoreboard(db.Model):
    """Scoreboard model for tracking benchmark scores"""
    __tablename__ = 'scoreboard'  # Explicitly name the table
    
    id = db.Column(db.Integer, primary_key=True)
    # Define username as a proper foreign key to users.username
    username = db.Column(db.String(50), db.ForeignKey('users.username'), nullable=False, index=True)
    agent_name = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

# -----------------------------------------------------------------------------
# Database Setup
# -----------------------------------------------------------------------------

def setup_database():
    """
    Set up the database tables. If there's a schema change, 
    this will recreate the tables.
    """
    with app.app_context():
        try:
            # Try to query to check if the schema is compatible
            User.query.first()
            Scoreboard.query.first()
            print("Database schema is compatible")
        except Exception as e:
            print(f"Database schema issue detected: {e}")
            print("Recreating database tables...")
            
            # Load existing users from JSON as backup
            users_data = []
            if os.path.exists(JSON_USERS_PATH):
                try:
                    with open(JSON_USERS_PATH, 'r', encoding='utf-8') as f:
                        users_data = json.load(f)
                except Exception as json_err:
                    print(f"Error loading users.json: {json_err}")
            
            # Try to backup existing scores if any
            existing_scores = []
            try:
                # Connect directly to the database to extract data
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check if the scoreboard table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scoreboard'")
                if cursor.fetchone():
                    cursor.execute("SELECT username, agent_name, score FROM scoreboard")
                    existing_scores = cursor.fetchall()
                    
                conn.close()
            except Exception as db_err:
                print(f"Error backing up existing scores: {db_err}")
            
            # Recreate tables
            db.drop_all()
            db.create_all()
            
            # Restore users from backup first (since they're referenced by foreign keys)
            print("Restoring users from backup...")
            for user_entry in users_data:
                username = user_entry.get('username')
                password_hash = user_entry.get('password_hash')
                api_key = user_entry.get('api_key')
                
                if username and password_hash and api_key:
                    new_user = User(username=username, password=password_hash, api_key=api_key)
                    db.session.add(new_user)
            
            # Commit users to ensure they exist before adding scores that reference them
            db.session.commit()
            
            # Restore scores if any (only for users that exist)
            print("Restoring scores from backup...")
            valid_usernames = [u.username for u in User.query.all()]
            restored_count = 0
            
            for score_entry in existing_scores:
                username, agent_name, score = score_entry
                # Only restore scores for users that exist (to satisfy foreign key)
                if username in valid_usernames:
                    new_score = Scoreboard(username=username, agent_name=agent_name, score=score)
                    db.session.add(new_score)
                    restored_count += 1
            
            db.session.commit()
            print(f"Database tables recreated successfully. Restored {restored_count} scores.")

# -----------------------------------------------------------------------------
# Create DB if not exists
# -----------------------------------------------------------------------------
@app.before_request
def create_tables():
    """Ensure tables exist before handling requests"""
    db.create_all()
    # Also ensure a users.json file exists
    if not os.path.exists(JSON_USERS_PATH):
        with open(JSON_USERS_PATH, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def save_user_to_json(username, password_hash, api_key):
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
        "password_hash": password_hash,
        "api_key": api_key
    }
    users_data.append(new_user_entry)

    # Write back
    with open(JSON_USERS_PATH, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, indent=2)

def generate_secure_api_key():
    """Generate a secure API key for users"""
    return secrets.token_hex(24)  # 48 characters, more secure

def login_required(f):
    """Decorator to require login for certain routes"""
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("Please login to access this page.", "error")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    """About page with information about the benchmark"""
    return render_template('about.html')

@app.route('/register', methods=['GET','POST'])
def register():
    """
    Registers a new user. Also saves to 'users.json' in addition to the DB.
    Uses secure password hashing.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Basic validation
        if not username or not password:
            flash("Username and password are required.", "error")
            return redirect(url_for('register'))
            
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return redirect(url_for('register'))

        # Check if username already exists in DB
        existing = User.query.filter_by(username=username).first()
        if existing:
            flash("Username already taken.", "error")
            return redirect(url_for('register'))

        # Generate an API key
        api_key = generate_secure_api_key()
        
        # Hash the password
        password_hash = generate_password_hash(password)

        # Save to DB
        new_user = User(username=username, password=password_hash, api_key=api_key)
        db.session.add(new_user)
        db.session.commit()

        # Also save to local JSON
        save_user_to_json(username, password_hash, api_key)

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET','POST'])
def login():
    """
    Logs the user in if credentials match an entry in the DB.
    Uses secure password verification.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Basic validation
        if not username or not password:
            flash("Username and password are required.", "error")
            return redirect(url_for('login'))

        # Get the user from DB
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists and password matches
        if user and check_password_hash(user.password, password):
            # Set session to be permanent (respects PERMANENT_SESSION_LIFETIME)
            session.permanent = True
            session['username'] = user.username
            session['user_id'] = user.id
            
            # Redirect to intended page or default to index
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):  # Prevent open redirect vulnerability
                return redirect(next_page)
            
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials. Please try again.", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logs the user out by clearing the session"""
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('index'))


@app.route('/leaderboard')
def leaderboard():
    """
    Shows the top 10 scores in descending order.
    """
    scores = Scoreboard.query.order_by(Scoreboard.score.desc()).limit(10).all()
    return render_template('leaderboard.html', scores=scores)


@app.route('/profile')
@login_required
def profile():
    """
    Displays the logged-in user's info, including API key.
    """
    username = session['username']
    user = User.query.filter_by(username=username).first()
    if not user:
        flash("No user found. Please register.", "error")
        return redirect(url_for('register'))

    return render_template('profile.html', username=user.username, api_key=user.api_key)

# The submit_score route has been removed in favor of using the GitHub library
# for score submissions: https://github.com/LondonWizard/CRM-AI-Agent-Benchmarking

@app.route('/submit_agent_score_api', methods=['POST'])
@csrf.exempt  # API endpoints need CSRF exemption
def submit_agent_score_api():
    """
    This endpoint is for automated posting from your main script or benchmark pipeline.
    It expects 'api_key', 'agent_name', and 'score' in the form data (or JSON).
    We look up the user by the provided API key, and if valid, record the score.
    Returns JSON indicating success/failure.
    """
    # Rate limiting would be implemented here in production
    
    # Get data from form or JSON
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

# Error handlers
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    """Handle CSRF errors by returning to the login page with a flash message"""
    flash("Your session has expired or the form has been tampered with. Please try again.", "error")
    return redirect(url_for('login'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, message="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error_code=500, message="Internal server error"), 500

if __name__ == '__main__':
    # Set up database tables
    setup_database()
    
    # For development only - production would use proper WSGI server
    app.run(debug=True, host='0.0.0.0', port=5000)  # Remove SSL requirement for development
