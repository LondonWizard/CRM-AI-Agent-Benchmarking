from app import app, db, User, Scoreboard
import os

def init_database():
    with app.app_context():
        # Drop all tables first
        db.drop_all()
        # Create all tables
        db.create_all()
        print("Database initialized successfully!")

if __name__ == '__main__':
    # Delete the database file if it exists
    db_path = os.path.join(os.path.dirname(__file__), 'leaderboard.db')
    if os.path.exists(db_path):
        os.remove(db_path)
    init_database() 