import os
import json
import logging
from flask import Flask
from models import db, Problem
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
CURRICULUMS_DIR = "curriculums"

def create_app():
    app = Flask(__name__)
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("❌ DATABASE_URL not found in environment variables.")
        raise ValueError("DATABASE_URL is missing")
        
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    db.init_app(app)
    return app

def normalize_problem_data(p):
    """Refined logic to convert curriculum schema to DB schema."""
    data = p.copy()
    
    # 1. Signature
    if "function_signature" not in data and "signature" in data:
        data["function_signature"] = f"{data['signature']}\n    \"\"\"\n    Write your code here\n    \"\"\"\n    pass"
    
    # 2. Test Cases (Simple -> Complex)
    if "test_cases" not in data and "tests" in data:
        new_tests = []
        for t in data["tests"]:
            # Format: [input_args, expected_output]
            raw_input = t[0]
            raw_output = t[1]
            
            if isinstance(raw_input, list):
                # Join args with comma
                input_str = ", ".join([json.dumps(arg) for arg in raw_input])
            else:
                input_str = json.dumps(raw_input)
                
            output_str = json.dumps(raw_output)
            
            new_tests.append({
                "input": input_str,
                "output": output_str
            })
        data["test_cases"] = new_tests

    # 3. Sample Data
    if "sample_input" not in data and "test_cases" in data and data["test_cases"]:
        first = data["test_cases"][0]
        data["sample_input"] = first["input"]
        data["sample_output"] = first["output"]
        
    return data

def migrate():
    app = create_app()
    
    with app.app_context():
        logger.info("🔌 Connecting to Database...")
        db.create_all()
        logger.info("✅ Database Tables Created.")
        
        # Sources to migrate
        sources = []
        
        # 1. Main Config
        if os.path.exists("questions_config.json"):
            sources.append("questions_config.json")
            
        # 2. Curriculums Folder
        if os.path.exists(CURRICULUMS_DIR):
            for f in os.listdir(CURRICULUMS_DIR):
                if f.endswith(".json"):
                    sources.append(os.path.join(CURRICULUMS_DIR, f))
        
        if not sources:
             logger.warning("⚠️ No problem sources found (questions_config.json or curriculums/). Skipping data import.")
             return

        count = 0
        for path in sources:
            filename = os.path.basename(path)
            logger.info(f"📖 Processing {filename}...")
            
            try:
                with open(path) as f:
                    file_data = json.load(f)
                
                # Iterate groups
                for group_key, group_data in file_data.items():
                    problems = group_data.get("problems", [])
                    
                    for p in problems:
                        # Normalize
                        p_norm = normalize_problem_data(p)
                        
                        # Check exist
                        existing = Problem.query.get(p_norm["id"])
                        if existing:
                            logger.info(f"   🔄 Updating {p_norm['id']}")
                            existing.title = p_norm.get("title")
                            existing.difficulty = p_norm.get("difficulty")
                            existing.tags = p_norm.get("tags", [])
                            existing.hints = p_norm.get("hints", [])
                            existing.signature = p_norm.get("function_signature")
                            existing.description = p_norm.get("description")
                            existing.sample_input = p_norm.get("sample_input")
                            existing.sample_output = p_norm.get("sample_output")
                            existing.test_cases = p_norm.get("test_cases", [])
                        else:
                            logger.info(f"   ➕ Adding {p_norm['id']}")
                            new_problem = Problem(
                                id=p_norm["id"],
                                title=p_norm.get("title"),
                                difficulty=p_norm.get("difficulty"),
                                tags=p_norm.get("tags", []),
                                hints=p_norm.get("hints", []),
                                signature=p_norm.get("function_signature"),
                                description=p_norm.get("description"),
                                sample_input=p_norm.get("sample_input"),
                                sample_output=p_norm.get("sample_output"),
                                test_cases=p_norm.get("test_cases", [])
                            )
                            db.session.add(new_problem)
                        
                        count += 1
                
                db.session.commit()
                
            except Exception as e:
                logger.error(f"❌ Failed to process {filename}: {e}")
                db.session.rollback()
        
        logger.info(f"🚀 Migration Complete. Processed {count} problems.")

if __name__ == "__main__":
    migrate()
