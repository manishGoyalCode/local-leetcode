from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import date

from runner.code_runner import evaluate_code

# ======================================================
# APP CONFIG
# ======================================================

app = Flask(__name__)

PROBLEMS_DIR = "problems"
import logging
# PROGRESS_FILE = "progress.json"  <-- Deprecated
# Database removed in favor of LocalStorage (Client-side progress)

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
# FILE & JSON UTILITIES
# ======================================================
def read_json(path):
    with open(path) as f:
        return json.load(f)

def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ======================================================
# PROBLEM SERVICES
# ======================================================

def load_problem(problem_id):
    for day in os.listdir(PROBLEMS_DIR):
        day_path = os.path.join(PROBLEMS_DIR, day)
        if not os.path.isdir(day_path):
            continue
        for file in os.listdir(day_path):
            if file.endswith(".json"):
                problem = read_json(os.path.join(day_path, file))
                if problem["id"] == problem_id:
                    return problem
    raise Exception(f"Problem {problem_id} not found")

def load_problem_index():
    index = []
    for day in sorted(os.listdir(PROBLEMS_DIR)):
        day_path = os.path.join(PROBLEMS_DIR, day)
        if not os.path.isdir(day_path):
            continue
        problems = []
        for file in sorted(os.listdir(day_path)):
            if file.endswith(".json"):
                p = read_json(os.path.join(day_path, file))
                problems.append({
                    "id": p["id"], 
                    "title": p["title"],
                    "difficulty": p.get("difficulty", "Easy"),
                    "tags": p.get("tags", [])
                })
        if problems:
            index.append({"day": day.replace("_", " ").title(), "problems": problems})
    return index

# ======================================================
# ROUTES – PROBLEM VIEW
# ======================================================

@app.route("/")
@app.route("/problem/<problem_id>")
def show_problem(problem_id=None):
    sidebar = load_problem_index()

    if not sidebar:
        return "❌ No problems found. Check problems/ folder."

    if problem_id is None:
        problem_id = sidebar[0]["problems"][0]["id"]
    
    logger.info(f"👀 View Problem: {problem_id}")
    problem = load_problem(problem_id)

    return render_template(
        "problem.html",
        problem=problem,
        sidebar=sidebar
        # Solved list is now handled by client-side JS
    )

# ======================================================
# ROUTES – RUN CODE
# ======================================================

@app.route("/run", methods=["POST"])
def run_code():
    data = request.json
    code = data["code"]
    problem_id = data["problem_id"]
    
    logger.info(f"🚀 Run Code: {problem_id}")

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