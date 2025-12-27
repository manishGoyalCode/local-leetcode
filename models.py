from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

db = SQLAlchemy()

class Problem(db.Model):
    __tablename__ = 'problems'
    
    id = db.Column(db.String(100), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    difficulty = db.Column(db.String(50))
    tags = db.Column(JSONB, default=[]) 
    hints = db.Column(JSONB, default=[])
    signature = db.Column(db.Text, nullable=True) # function_signature
    description = db.Column(db.Text, nullable=True)
    sample_input = db.Column(db.Text, nullable=True)
    sample_output = db.Column(db.Text, nullable=True)
    test_cases = db.Column(JSONB, default=[]) # The actual test cases for evaluation
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "difficulty": self.difficulty,
            "tags": self.tags,
            "hints": self.hints,
            "function_signature": self.signature,
            "description": self.description,
            "sample_input": self.sample_input,
            "sample_output": self.sample_output,
            "test_cases": self.test_cases 
        }
