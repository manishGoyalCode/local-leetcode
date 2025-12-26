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
PROGRESS_FILE = "progress.json"

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

    print("✅ Sidebar index:", index)  # DEBUG
    return index

# ======================================================
# PROGRESS SERVICES
# ======================================================

def load_progress():
    if not os.path.exists(PROGRESS_FILE):
        return {"solved": []}
    return read_json(PROGRESS_FILE)


def save_progress(progress):
    write_json(PROGRESS_FILE, progress)


def update_progress(problem_id):
    """
    Update solved list and daily solve log.
    """
    progress = load_progress()

    if problem_id not in progress.get("solved", []):
        progress.setdefault("solved", []).append(problem_id)

        today = str(date.today())
        progress.setdefault("solve_log", {})
        progress["solve_log"].setdefault(today, []).append(problem_id)

        save_progress(progress)

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
    progress = load_progress()

    return render_template(
        "problem.html",
        problem=problem,
        sidebar=sidebar,
        solved=progress.get("solved", [])
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


def calculate_streak(progress):
    """
    Calculate current and best streak from solve_log.
    """
    log = progress.get("solve_log", {})
    sorted_days = sorted(log.keys())

    streak = 0
    best = 0
    prev = None

    for d in sorted_days:
        if prev is None:
            streak = 1
        else:
            diff = (date.fromisoformat(d) - date.fromisoformat(prev)).days
            streak = streak + 1 if diff == 1 else 1

        best = max(best, streak)
        prev = d

    return streak, best

# ======================================================
# ROUTES – DASHBOARD
# ======================================================

@app.route("/dashboard")
def dashboard():
    sidebar = load_problem_index()
    progress = load_progress()

    solved = set(progress.get("solved", []))

    total, day_stats = calculate_day_stats(sidebar, solved)
    overall_percent = int((len(solved) / total) * 100) if total else 0

    current_streak, best_streak = calculate_streak(progress)

    return render_template(
        "dashboard.html",
        overall_percent=overall_percent,
        day_stats=day_stats,
        solved_count=len(solved),
        total_count=total,
        current_streak=current_streak,
        best_streak=best_streak
    )

# ======================================================
# ENTRY POINT
# ======================================================

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
