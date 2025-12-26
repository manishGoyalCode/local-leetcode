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
# DATA LOADING (In-Memory)
# ======================================================

CURRICULUMS_DIR = "curriculums"
ALL_PROBLEMS = {}      # Map: problem_id -> problem_data
CURRICULUMS = {}       # Map: track_name -> sidebar_list
TRACK_TITLES = {}      # Map: track_name -> Display Title

def load_data():
    """Butcher the file system to load all curriculums into memory."""
    global ALL_PROBLEMS, CURRICULUMS, TRACK_TITLES
    
    ALL_PROBLEMS = {}
    CURRICULUMS = {}
    TRACK_TITLES = {}
    
    if not os.path.exists(CURRICULUMS_DIR):
        os.makedirs(CURRICULUMS_DIR)
        
    for filename in os.listdir(CURRICULUMS_DIR):
        if not filename.endswith(".json"):
            continue
            
        track_id = filename.replace(".json", "")
        # Pretty title: "blind75" -> "Blind75"
        TRACK_TITLES[track_id] = track_id.replace("_", " ").title()
        
        path = os.path.join(CURRICULUMS_DIR, filename)
        try:
            with open(path) as f:
                data = json.load(f)
                
            # Build Sidebar
            sidebar = []
            for group_key, group_data in data.items():
                day_title = group_data.get("title", group_key)
                problems_list = []
                
                for p in group_data.get("problems", []):
                    # Cache Problem
                    ALL_PROBLEMS[p["id"]] = p
                    
                    # Add to Index
                    problems_list.append({
                        "id": p["id"],
                        "title": p["title"],
                        "difficulty": p.get("difficulty", "Easy"),
                        "tags": p.get("tags", [])
                    })
                
                if problems_list:
                    sidebar.append({
                        "day": day_title,
                        "problems": problems_list
                    })
            
            CURRICULUMS[track_id] = sidebar
            logger.info(f"📚 Loaded Curriculum: {track_id} ({len(sidebar)} sections)")
            
        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")

    # SYNC: Ensure filesystem matches loaded data
    sync_problems()

def sync_problems():
    """Ensures every problem in ALL_PROBLEMS has a physical file in problems/ directory."""
    if not os.path.exists(PROBLEMS_DIR):
        os.makedirs(PROBLEMS_DIR)

    count = 0
    for pid, problem in ALL_PROBLEMS.items():
        # Clean ID to be safe filename
        safe_id = "".join([c if c.isalnum() else "_" for c in pid])
        
        found = False
        for day in os.listdir(PROBLEMS_DIR):
            day_path = os.path.join(PROBLEMS_DIR, day)
            if os.path.isdir(day_path):
                if f"{safe_id}.json" in os.listdir(day_path):
                    found = True
                    break
        
        if not found:
            # Create in problems/extra
            target_dir = os.path.join(PROBLEMS_DIR, "extra")
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            # ======================================================
            # NORMALIZE DATA FOR RUNNER
            # ======================================================
            
            # 1. Map 'signature' -> 'function_signature'
            if "function_signature" not in problem and "signature" in problem:
                # Add a default docstring
                problem["function_signature"] = f"{problem['signature']}\n    \"\"\"\n    Write your code here\n    \"\"\"\n    pass"

            # 2. Map 'tests' (simple) -> 'test_cases' (runner format)
            if "test_cases" not in problem and "tests" in problem:
                new_tests = []
                for t in problem["tests"]:
                    # Assume simple format: [input_args, expected_output]
                    # input_args can be a single value or list of args
                    raw_input = t[0]
                    raw_output = t[1]
                    
                    # Convert Input: Must be a string of comma-separated args
                    if isinstance(raw_input, list):
                        # e.g., [[1,2], 5] -> "1,2, 5" NOT "[1,2], 5" if they are separate args!
                        # But wait, python eval("1, 2") is tuple (1, 2). 
                        # If signature is solve(a, b). Input "1, 2" works.
                        # If args are [[1,2], 5]. Input "[1,2], 5" works.
                        # So joining by comma is generally correct for python args.
                        input_strings = []
                        for arg in raw_input:
                            input_strings.append(json.dumps(arg))
                        input_str = ", ".join(input_strings)
                    else:
                        # Single arg
                        input_str = json.dumps(raw_input)
                        
                    output_str = json.dumps(raw_output)
                    
                    new_tests.append({
                        "input": input_str,
                        "output": output_str
                    })
                problem["test_cases"] = new_tests

            # 3. Generate Sample Data
            if "sample_input" not in problem and "test_cases" in problem and problem["test_cases"]:
                first = problem["test_cases"][0]
                problem["sample_input"] = first["input"]
                problem["sample_output"] = first["output"]

            target_file = os.path.join(target_dir, f"{safe_id}.json")
            with open(target_file, "w") as f:
                json.dump(problem, f, indent=2)
            count += 1
            
    if count > 0:
        logger.info(f"✨ Synced {count} new problems to {PROBLEMS_DIR}/extra")

# Load immediately on start
load_data()

# ======================================================
# HELPERS
# ======================================================

def get_current_track():
    # Default to 'default' if exists, else first available
    track = request.cookies.get("active_track", "default")
    if track not in CURRICULUMS:
        return next(iter(CURRICULUMS)) if CURRICULUMS else None
    return track

def load_problem(problem_id):
    if problem_id not in ALL_PROBLEMS:
        raise Exception(f"Problem {problem_id} not found")
    return ALL_PROBLEMS[problem_id]

# ======================================================
# ROUTES – PROBLEM VIEW
# ======================================================

@app.route("/")
@app.route("/problem/<problem_id>")
def show_problem(problem_id=None):
    track_id = get_current_track()
    if not track_id:
        return "❌ No curriculums found. Please check curriculums/ folder."
        
    sidebar = CURRICULUMS[track_id]

    # If no specific problem requested, pick first from this track
    if problem_id is None:
        try:
            problem_id = sidebar[0]["problems"][0]["id"]
        except (IndexError, KeyError):
            return "❌ Empty curriculum."
    
    # Check if problem actually exists (it might be from another track)
    # If so, we just load it. Cross-track loading is allowed!
    try:
        problem = load_problem(problem_id)
    except:
         return f"❌ Problem {problem_id} not found."

    logger.info(f"👀 View Problem: {problem_id} (Track: {track_id})")

    response =  render_template(
        "problem.html",
        problem=problem,
        sidebar=sidebar,
        current_track=track_id,
        all_tracks=TRACK_TITLES
    )
    return response

# ======================================================
# ROUTES – SWITCH TRACK
# ======================================================

@app.route("/switch_track/<track_id>")
def switch_track(track_id):
    if track_id in CURRICULUMS:
        resp = jsonify({"status": "ok", "track": track_id})
        resp.set_cookie("active_track", track_id, max_age=31536000) # 1 year
        return resp
    return jsonify({"status": "error", "message": "Invalid track"}), 404

# ======================================================
# ROUTES – RUN CODE
# ======================================================

@app.route("/run", methods=["POST"])
def run_code():
    data = request.json
    code = data["code"]
    problem_id = data["problem_id"]
    
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
            "details": [{"status": "error", "error": str(e), "index": 0}]
        })


# ======================================================
# ROUTES – DASHBOARD
# ======================================================

@app.route("/dashboard")
def dashboard():
    track_id = get_current_track()
    sidebar = CURRICULUMS.get(track_id, [])
    
    return render_template(
        "dashboard.html", 
        sidebar=sidebar,
        current_track=track_id,
        all_tracks=TRACK_TITLES
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