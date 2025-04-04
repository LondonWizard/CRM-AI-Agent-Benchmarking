"""
A simple Flask app that integrates:
 - user signup & login (with local JSON backup of user info)
 - storing a generated API key in a database
 - a scoreboard/leaderboard
 - an API endpoint to POST agent scores using the API key
 - a user profile page to display the API key
 - email verification and password reset functionality
 - social login options
 - RESTful API endpoints for accessing leaderboard data

Database: SQLite in local file 'leaderboard.db'
Additionally, user registration data is mirrored to 'users.json'.
"""

import os
import json
import secrets
import hashlib
from datetime import timedelta, datetime
import jwt
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, current_app, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_mail import Mail, Message
import cryptography
from sqlalchemy.sql import func, and_
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_url_path='/static')

# Configure Flask app
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['WTF_CSRF_TIME_LIMIT'] = 3600

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Initialize extensions
csrf = CSRFProtect(app)
mail = Mail(app)

# Add rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["60 per minute"],
    storage_uri="memory://"
)

# Database configuration
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
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    api_key = db.Column(db.String(100), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100), unique=True)
    password_reset_token = db.Column(db.String(100), unique=True)
    password_reset_expires = db.Column(db.DateTime)
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
    """About page with benchmark information"""
    return render_template('about.html')

@app.route('/faq')
def faq():
    """FAQ page with commonly asked questions"""
    return render_template('faq.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('register.html')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')
        
        # Create new user
        hashed_password = generate_password_hash(password)
        api_key = secrets.token_urlsafe(32)
        
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            api_key=api_key
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Send verification email
            if send_verification_email(new_user):
                flash('Registration successful! Please check your email to verify your account and access your API key.', 'success')
            else:
                flash('Registration successful! However, we could not send the verification email. Please contact support.', 'warning')
            
            # Auto-login the user
            session['user_id'] = new_user.id
            session['username'] = new_user.username
            session.permanent = True
            
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            if not user.email_verified:
                flash('Please verify your email before logging in.', 'error')
                return render_template('login.html')
            
            session['user_id'] = user.id
            session['username'] = user.username
            session.permanent = True
            
            return redirect(url_for('profile'))
        else:
            flash('Invalid username or password.', 'error')
    
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
    """Display user profile and API key"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    # Only show API key if email is verified
    api_key = user.api_key if user.email_verified else None
    
    # Get latest submission for each agent with their dataset scores
    agent_scores = db.session.query(
        Scoreboard.agent_name,
        func.max(Scoreboard.score).label('best_score'),
        func.count(Scoreboard.id).label('submission_count'),
        # Get the dataset_scores from the latest submission
        Scoreboard.dataset_scores
    ).filter_by(username=user.username)\
     .group_by(Scoreboard.agent_name)\
     .order_by(func.max(Scoreboard.score).desc())\
     .all()
    
    # Convert SQLAlchemy objects to dictionaries
    submissions = []
    for score in agent_scores:
        submissions.append({
            'agent_name': score.agent_name,
            'score': score.best_score,
            'submission_count': score.submission_count,
            'dataset_scores': score.dataset_scores or {}
        })
    
    return render_template(
        'profile.html',
        username=user.username,
        api_key=api_key,
        email_verified=user.email_verified,
        submissions=submissions
    )

@app.route('/agent/<agent_name>')
def agent_details(agent_name):
    """Display detailed history for a specific agent."""
    # Get all submissions for this agent, ordered by date
    submissions = Scoreboard.query.filter_by(agent_name=agent_name)\
        .order_by(Scoreboard.created_at.desc()).all()
    
    if not submissions:
        abort(404)
    
    # Get latest submission
    latest_submission = submissions[0]
    dataset_scores = latest_submission.dataset_scores or {}
    
    # Get username from the latest submission
    username = latest_submission.username
    
    # Get rank of this agent
    subquery = db.session.query(
        Scoreboard.agent_name,
        func.max(Scoreboard.score).label('max_score')
    ).group_by(Scoreboard.agent_name).subquery()
    
    rank_query = db.session.query(
        func.count('*') + 1
    ).filter(
        subquery.c.max_score > latest_submission.score
    )
    
    rank = rank_query.scalar() or 1
    
    # Calculate additional metrics
    submission_count = len(submissions)
    best_score = max(sub.score for sub in submissions)
    
    # Prepare first and latest submission dates
    first_submission = submissions[-1].created_at
    latest_submission_date = latest_submission.created_at
    
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
        history=history_data,
        username=username,
        rank=rank,
        submission_history=submissions,
        submission_count=submission_count,
        best_score=best_score,
        first_submission=first_submission,
        latest_submission=latest_submission_date,
        latest_submission_id=latest_submission.id
    )

@app.route('/submit_agent_score_api', methods=['POST'])
@limiter.limit("10/hour")
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

def send_verification_email(user):
    """Send verification email to user"""
    token = secrets.token_urlsafe(32)
    user.email_verification_token = token
    db.session.commit()
    
    verification_url = url_for('verify_email', token=token, _external=True)
    
    msg = Message('Welcome to CRM AI Agent Challenge!',
                  recipients=[user.email])
    msg.body = f'''Welcome to CRM AI Agent Challenge!

Thank you for registering. To complete your registration and access your API key, please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

Best regards,
The CRM AI Agent Challenge Team

If you did not create an account, please ignore this email.
'''
    msg.html = f'''
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #2563eb; text-align: center;">Welcome to CRM AI Agent Challenge!</h1>
        <p>Hi {user.username},</p>
        <p>Thank you for registering with CRM AI Agent Challenge. We're excited to have you on board!</p>
        <p>To complete your registration and access your API key, please verify your email address by clicking the button below:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{verification_url}" 
               style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                Verify Email Address
            </a>
        </div>
        <p style="color: #666; font-size: 14px;">This link will expire in 24 hours.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #666; font-size: 14px;">Best regards,<br>The CRM AI Agent Challenge Team</p>
        <p style="color: #999; font-size: 12px; text-align: center;">If you did not create an account, please ignore this email.</p>
    </div>
    '''
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send verification email: {str(e)}")
        return False

def send_password_reset_email(user):
    """Send password reset email to user"""
    token = secrets.token_urlsafe(32)
    user.password_reset_token = token
    user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
    db.session.commit()
    
    reset_url = url_for('reset_password', token=token, _external=True)
    
    msg = Message('Password Reset Request',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request then simply ignore this email.
'''
    msg.html = f'''
    <h1>Password Reset Request</h1>
    <p>To reset your password, click the following link:</p>
    <p><a href="{reset_url}">Reset Password</a></p>
    <p>If you did not make this request then simply ignore this email.</p>
    '''
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send password reset email: {str(e)}")
        return False

@app.route('/verify-email/<token>')
def verify_email(token):
    """Verify user's email address"""
    user = User.query.filter_by(email_verification_token=token).first()
    if user is None:
        flash('Invalid or expired verification token.', 'error')
        return redirect(url_for('login'))
    
    user.email_verified = True
    user.email_verification_token = None
    db.session.commit()
    
    flash('Your email has been verified. You can now log in.', 'success')
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password request"""
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            if send_password_reset_email(user):
                flash('Password reset instructions have been sent to your email.', 'success')
            else:
                flash('An error occurred. Please try again later.', 'error')
        else:
            flash('Email address not found.', 'error')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset"""
    user = User.query.filter_by(password_reset_token=token).first()
    if user is None or user.password_reset_expires < datetime.utcnow():
        flash('Invalid or expired password reset token.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('reset_password.html')
        
        user.password = generate_password_hash(password)
        user.password_reset_token = None
        user.password_reset_expires = None
        db.session.commit()
        
        flash('Your password has been reset. You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html')

@app.route('/api/leaderboard')
@limiter.limit("60/minute")
@csrf.exempt
def api_leaderboard():
    """API endpoint to get leaderboard data"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)  # Max 50 per page

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

    # Format the data for API response
    leaderboard_data = []
    for entry in entries:
        leaderboard_data.append({
            'username': entry.username,
            'agent_name': entry.agent_name,
            'score': entry.score,
            'created_at': entry.created_at.isoformat()
        })

    # Build the pagination info
    pagination_info = {
        'current_page': page,
        'total_pages': pagination.pages,
        'total_entries': pagination.total,
        'per_page': per_page
    }

    return jsonify({
        'status': 'success',
        'leaderboard': leaderboard_data,
        'pagination': pagination_info
    })

@app.route('/api/agent/<agent_name>')
@limiter.limit("60/minute")
@csrf.exempt
def api_agent_details(agent_name):
    """API endpoint to get detailed info about a specific agent"""
    # Get all submissions for this agent, ordered by date
    submissions = Scoreboard.query.filter_by(agent_name=agent_name)\
        .order_by(Scoreboard.created_at.desc()).all()
    
    if not submissions:
        return jsonify({
            'status': 'error',
            'message': f'Agent "{agent_name}" not found'
        }), 404
    
    # Get latest submission
    latest_submission = submissions[0]
    dataset_scores = latest_submission.dataset_scores or {}
    
    # Get username from the latest submission
    username = latest_submission.username
    
    # Get rank of this agent
    subquery = db.session.query(
        Scoreboard.agent_name,
        func.max(Scoreboard.score).label('max_score')
    ).group_by(Scoreboard.agent_name).subquery()
    
    rank_query = db.session.query(
        func.count('*') + 1
    ).filter(
        subquery.c.max_score > latest_submission.score
    )
    
    rank = rank_query.scalar() or 1
    
    # Calculate additional metrics
    submission_count = len(submissions)
    best_score = max(sub.score for sub in submissions)
    
    # Prepare first and latest submission dates
    first_submission = submissions[-1].created_at
    latest_submission_date = latest_submission.created_at
    
    # Prepare historical data
    history_data = [{
        'date': sub.created_at.isoformat(),
        'score': sub.score,
        'dataset_scores': sub.dataset_scores or {}
    } for sub in submissions]
    
    agent_data = {
        'agent_name': agent_name,
        'username': username,
        'latest_score': latest_submission.score,
        'rank': rank,
        'submission_count': submission_count,
        'best_score': best_score,
        'first_submission': first_submission.isoformat(),
        'latest_submission': latest_submission_date.isoformat(),
        'dataset_scores': dataset_scores,
        'history': history_data
    }
    
    return jsonify({
        'status': 'success',
        'agent': agent_data
    })

if __name__ == '__main__':
    # Set up database tables
    setup_database()
    
    # For development only - production would use proper WSGI server
    app.run(debug=True, host='0.0.0.0', port=5000)  # Remove SSL requirement for development
