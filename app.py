from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import date

from runner.code_runner import evaluate_code

# ======================================================
# APP CONFIG
# ======================================================

from dotenv import load_dotenv
from models import db, Problem

# Load env variables
load_dotenv()

# ======================================================
# APP CONFIG
# ======================================================

app = Flask(__name__)

# Verify Database URL
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("❌ DATABASE_URL missing in environment variables")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize DB with App
db.init_app(app)

import logging

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Connect Gunicorn logger if available
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    logging.getLogger().handlers = gunicorn_logger.handlers
    logging.getLogger().setLevel(gunicorn_logger.level)

logger = logging.getLogger(__name__)

# ======================================================
# PROBLEM SERVICES
# ======================================================

def load_problem(problem_id):
    """Fetch specific problem from DB."""
    problem = db.session.get(Problem, problem_id)
    if not problem:
        raise Exception(f"Problem {problem_id} not found")
    # Return as dictionary for compatibility with runner and template
    return problem.to_dict()

def load_problem_index():
    """Build sidebar from all DB problems."""
    # Note: In a real app, you might want to categorize by a 'group' column.
    # Current DB schema doesn't have 'day' or 'group'. 
    # For now, we'll put everything in "All Problems" or categorize by difficulty.
    # OR, we can just return a flat list.
    
    problems = Problem.query.order_by(Problem.id).all()
    
    # Ideally we should have migrated the 'group' info. 
    # Since we didn't, let's group by Difficulty or just one big list.
    
    # Grouping by Difficulty for better UX
    groups = {}
    for p in problems:
        diff = p.difficulty or "Unknown"
        if diff not in groups:
            groups[diff] = []
        
        groups[diff].append({
            "id": p.id,
            "title": p.title,
            "difficulty": p.difficulty,
            "tags": p.tags
        })

    index = []
    # Sort order: Easy, Medium, Hard
    for diff in ["Easy", "Medium", "Hard"]:
        if diff in groups:
            index.append({"day": f"{diff} Problems", "problems": groups[diff]})
            
    # Add any others
    for diff in groups:
        if diff not in ["Easy", "Medium", "Hard"]:
            index.append({"day": f"{diff} Problems", "problems": groups[diff]})
            
    return index

# ======================================================
# ROUTES – PROBLEM VIEW
# ======================================================

@app.route("/")
@app.route("/problem/<problem_id>")
def show_problem(problem_id=None):
    sidebar = load_problem_index()

    if not sidebar:
        return "❌ No problems found in Database."

    if problem_id is None:
        # Pick first problem of first group
        try:
            problem_id = sidebar[0]["problems"][0]["id"]
        except:
             return "❌ No problems available."
    
    logger.info(f"👀 View Problem: {problem_id}")
    
    try:
        problem = load_problem(problem_id)
    except Exception as e:
        return f"❌ {str(e)}"

    return render_template(
        "problem.html",
        problem=problem,
        sidebar=sidebar
    )

# ======================================================
# ROUTES – RUN CODE
# ======================================================

@app.route("/run", methods=["POST"])
def run_code():
    data = request.json
    code = data.get("code")
    problem_id = data.get("problem_id")
    
    if not code or not problem_id:
         return jsonify({"passed": False, "details": [{"status": "error", "error": "Missing code or problem_id"}]})
    
    logger.info(f"🚀 Run Code: {problem_id}")

    try:
        problem = load_problem(problem_id)
        passed, details = evaluate_code(code, problem)
        
        if passed:
            logger.info(f"✅ Solved: {problem_id}")
        else:
            logger.info(f"❌ Failed: {problem_id}")

        return jsonify({
            "passed": passed,
            "details": details
        })
    except Exception as e:
        logger.error(f"Execution Error: {e}")
        return jsonify({
            "passed": False,
            "details": [{"status": "error", "error": str(e)}]
        })


# ======================================================
# ROUTES – DASHBOARD
# ======================================================

@app.route("/dashboard")
def dashboard():
    sidebar = load_problem_index()
    return render_template("dashboard.html", sidebar=sidebar)

# ======================================================
# ENTRY POINT
# ======================================================
@app.route("/")
def hello():
    return "Hello from DO App Platform!"

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080))
    )