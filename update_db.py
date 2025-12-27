from app import app, db
from models import User, Submission

# Context ensures app config is loaded
with app.app_context():
    print("Updating database schema...")
    db.create_all()
    print("Database schema updated! 'submissions' table created.")
