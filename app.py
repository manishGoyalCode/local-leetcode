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
from database import init_db, mark_solved, get_solved_problems, get_solve_stats

# Configure Logging globally (captures app.py, code_runner.py, etc.)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# If running in Gunicorn, wire up the handlers to stdout/stderr if not already done
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    logging.getLogger().handlers = gunicorn_logger.handlers
    logging.getLogger().setLevel(gunicorn_logger.level)

logger = logging.getLogger(__name__)

# Initialize DB
init_db()

# ======================================================
# FILE & JSON UTILITIES
# ======================================================

def read_json(path):
    with open(path) as f:
        return json.load(f)

def write_json(path, data):
    # Only used for problems generation if needed, but we keep it for now
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ======================================================
# PROBLEM SERVICES
# ======================================================

def load_problem(problem_id):
    """
    Find and return a problem JSON by ID.
    """
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
    """
    Build sidebar structure:
    [
      {
        day: "Day 1",
        problems: [{ id, title }]
      }
    ]
    """
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
                    "title": p["title"]
                })

        if problems:
            index.append({
                "day": day.replace("_", " ").title(),
                "problems": problems
            })

    return index

# ======================================================
# PROGRESS SERVICES
# ======================================================

def get_user_id():
    # User ID comes from cookie set by frontend (script.js)
    # Default to 'anonymous' if missing, ensuring backward compat/safety
    return request.cookies.get("user_id", "anonymous")

def load_solved_list():
    return get_solved_problems(get_user_id())

def update_progress(problem_id):
    """
    Mark problem as solved in DB.
    """
    mark_solved(get_user_id(), problem_id)
    # logger.info(f"🏆 Progress Updated: Solved {problem_id}")


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

    problem = load_problem(problem_id)
    # OLD: progress = load_progress()
    solved_list = load_solved_list()

    return render_template(
        "problem.html",
        problem=problem,
        sidebar=sidebar,
        solved=solved_list
    )

# ======================================================
# ROUTES – RUN CODE
# ======================================================

@app.route("/run", methods=["POST"])
def run_code():
    data = request.json
    code = data["code"]
    problem_id = data["problem_id"]

    problem = load_problem(problem_id)
    passed, details = evaluate_code(code, problem)

    if passed:
        update_progress(problem_id)

    return jsonify({
        "passed": passed,
        "details": details
    })

# ======================================================
# DASHBOARD HELPERS
# ======================================================

def calculate_day_stats(sidebar, solved_set):
    total = 0
    stats = []

    for day in sidebar:
        day_total = len(day["problems"])
        day_solved = sum(
            1 for p in day["problems"] if p["id"] in solved_set
        )

        total += day_total
        stats.append({
            "day": day["day"],
            "solved": day_solved,
            "total": day_total,
            "percent": int((day_solved / day_total) * 100) if day_total else 0
        })

    return total, stats


def calculate_streak(solve_stats):
    """
    Calculate current and best streak using DB stats (day -> count).
    """
    if not solve_stats:
        return 0, 0

    sorted_days = sorted(solve_stats.keys())

    streak = 0
    best = 0
    prev = None

    for d in sorted_days:
        if prev is None:
            streak = 1
        else:
            try:
                # d is 'YYYY-MM-DD' from SQLite
                curr_date = date.fromisoformat(d)
                prev_date = date.fromisoformat(prev)
                diff = (curr_date - prev_date).days
                
                streak = streak + 1 if diff == 1 else 1
            except Exception:
                streak = 1
                
        best = max(best, streak)
        prev = d

    return streak, best

# ======================================================
# ROUTES – DASHBOARD
# ======================================================

@app.route("/dashboard")
@app.route("/dashboard")
def dashboard():
    sidebar = load_problem_index()
    # OLD: progress = load_progress()
    user_id = get_user_id()
    solved_list = load_solved_list()
    solve_stats = get_solve_stats(user_id) # Dict { "2025-12-26": 5 }

    solved_set = set(solved_list)

    total, day_stats = calculate_day_stats(sidebar, solved_set)
    overall_percent = int((len(solved_set) / total) * 100) if total else 0

    current_streak, best_streak = calculate_streak(solve_stats)

    return render_template(
        "dashboard.html",
        overall_percent=overall_percent,
        day_stats=day_stats,
        solved_count=len(solved_set),
        total_count=total,
        current_streak=current_streak,
        best_streak=best_streak
    )

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