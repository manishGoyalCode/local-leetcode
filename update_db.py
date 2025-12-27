from app import app, db
from models import User

# Context ensures app config is loaded
with app.app_context():
    print("Updating database schema...")
    db.create_all()
    print("Database schema updated! 'users' table created.")
