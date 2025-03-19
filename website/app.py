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
from sqlalchemy.sql import func, and_

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
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    api_key = db.Column(db.String(100), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # New admin column
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    
    # Add relationship to scores
    scores = db.relationship('Scoreboard', backref='user_obj', lazy=True, 
                           cascade="all, delete-orphan")

class Scoreboard(db.Model):
    """Scoreboard model for tracking benchmark scores"""
    __tablename__ = 'scoreboard'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), db.ForeignKey('users.username'), nullable=False, index=True)
    agent_name = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    dataset_scores = db.Column(db.JSON)  # Store individual dataset scores
    
    __table_args__ = (
        db.Index('idx_agent_score', 'agent_name', 'score'),  # Index for faster leaderboard queries
    )

# -----------------------------------------------------------------------------
# Database Setup
# -----------------------------------------------------------------------------

def setup_database():
    """Set up the database tables and ensure admin user exists."""
    with app.app_context():
        try:
            db.create_all()
            
            # Make maxsmeyer an admin if they exist
            admin_user = User.query.filter_by(username='maxsmeyer').first()
            if admin_user:
                admin_user.is_admin = True
                db.session.commit()
                
                # Update users.json to reflect admin status
                with open(JSON_USERS_PATH, 'r', encoding='utf-8') as f:
                    users_data = json.load(f)
                
                for user in users_data:
                    if user['username'] == 'maxsmeyer':
                        user['is_admin'] = True
                        break
                
                with open(JSON_USERS_PATH, 'w', encoding='utf-8') as f:
                    json.dump(users_data, f, indent=2)
                    
            print("Database setup complete")
            
        except Exception as e:
            print(f"Error during database setup: {e}")
            db.session.rollback()

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

def save_user_to_json(username, password_hash, api_key, is_admin=False):
    """Mirror the new user's data to 'users.json'."""
    try:
        with open(JSON_USERS_PATH, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
    except Exception:
        users_data = []

    new_user_entry = {
        "username": username,
        "password_hash": password_hash,
        "api_key": api_key,
        "is_admin": is_admin
    }
    users_data.append(new_user_entry)

    with open(JSON_USERS_PATH, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, indent=2)

def generate_secure_api_key():
    """Generate a secure API key for users"""
    return f"crm-{secrets.token_hex(24)}"  # 48 characters plus prefix

def login_required(f):
    """Decorator to require login for certain routes"""
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("Please login to access this page.", "error")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Add admin required decorator
def admin_required(f):
    """Decorator to require admin access for certain routes"""
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("Please login to access this page.", "error")
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=session['username']).first()
        if not user or not user.is_admin:
            flash("Admin access required.", "error")
            return redirect(url_for('index'))
            
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
        api_key = generate_secure_api_key()  # This generates a 48-char hex key

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
    """Display the leaderboard with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Use a subquery to get the latest submission for each agent per user
    latest_scores = db.session.query(
        Scoreboard.username,
        Scoreboard.agent_name,
        func.max(Scoreboard.created_at).label('max_created_at')
    ).group_by(Scoreboard.username, Scoreboard.agent_name).subquery()

    # Join with the original table to get the full records
    scores = db.session.query(Scoreboard)\
        .join(
            latest_scores,
            db.and_(
                Scoreboard.username == latest_scores.c.username,
                Scoreboard.agent_name == latest_scores.c.agent_name,
                Scoreboard.created_at == latest_scores.c.max_created_at
            )
        )\
        .order_by(Scoreboard.score.desc())

    # Paginate the results
    pagination = scores.paginate(page=page, per_page=per_page, error_out=False)
    entries = pagination.items

    return render_template(
        'leaderboard.html',
        scores=entries,
        pagination=pagination
    )


@app.route('/profile')
@login_required
def profile():
    """Displays the logged-in user's info and scores."""
    username = session['username']
    user = User.query.filter_by(username=username).first()
    if not user:
        flash("No user found. Please register.", "error")
        return redirect(url_for('register'))
    
    # Get latest submission for each agent with their dataset scores
    agent_scores = db.session.query(
        Scoreboard.agent_name,
        func.max(Scoreboard.score).label('best_score'),
        func.count(Scoreboard.id).label('submission_count'),
        # Get the dataset_scores from the latest submission
        Scoreboard.dataset_scores
    ).filter_by(username=username)\
     .group_by(Scoreboard.agent_name)\
     .order_by(func.max(Scoreboard.score).desc())\
     .all()
    
    # Convert SQLAlchemy objects to dictionaries
    agent_scores_list = []
    for score in agent_scores:
        agent_scores_list.append({
            'agent_name': score.agent_name,
            'best_score': score.best_score,
            'submission_count': score.submission_count,
            'latest_dataset_scores': score.dataset_scores or {}
        })
    
    return render_template(
        'profile.html',
        username=user.username,
        api_key=user.api_key,
        agent_scores=agent_scores_list
    )

@app.route('/agent/<agent_name>')
def agent_details(agent_name):
    """Display detailed history for a specific agent."""
    # Get all submissions for this agent, ordered by date
    submissions = Scoreboard.query.filter_by(agent_name=agent_name)\
        .order_by(Scoreboard.created_at.desc()).all()
    
    if not submissions:
        abort(404)
    
    # Prepare data for charts
    latest_submission = submissions[0]
    dataset_scores = latest_submission.dataset_scores or {}
    
    # Prepare historical data
    history_data = [{
        'date': sub.created_at.strftime('%Y-%m-%d %H:%M'),
        'score': sub.score,
        'dataset_scores': sub.dataset_scores or {}
    } for sub in submissions]
    
    return render_template(
        'agent_details.html',
        agent_name=agent_name,
        latest_score=latest_submission.score,
        dataset_scores=dataset_scores,
        history=history_data
    )

@app.route('/submit_agent_score_api', methods=['POST'])
@csrf.exempt
def submit_agent_score_api():
    """Submit agent score with dataset details."""
    if not request.is_json:
        return {"status": "error", "message": "Content-Type must be application/json"}, 400
    
    data = request.json
    api_key = data.get('api_key')
    agent_name = data.get('agent_name')
    score = data.get('score')
    dataset_scores = data.get('dataset_scores', {})

    if not all([api_key, agent_name, score]):
        return {"status": "error", "message": "Missing required fields"}, 400

    try:
        score = float(score)
    except ValueError:
        return {"status": "error", "message": "Invalid score format"}, 400

    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return {"status": "error", "message": "Invalid API key"}, 403

    # Create new score entry with dataset scores
    entry = Scoreboard(
        username=user.username,
        agent_name=agent_name,
        score=score,
        dataset_scores=dataset_scores
    )
    db.session.add(entry)
    db.session.commit()

    return {
        "status": "success",
        "message": "Score saved",
        "username": user.username
    }, 200

# Add delete submission route
@app.route('/delete_submission/<int:submission_id>', methods=['POST'])
@admin_required
@csrf.exempt
def delete_submission(submission_id):
    """Delete a submission from the leaderboard (admin only)"""
    submission = Scoreboard.query.get_or_404(submission_id)
    
    try:
        db.session.delete(submission)
        db.session.commit()
        return {"status": "success", "message": "Submission deleted"}, 200
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}, 500

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
