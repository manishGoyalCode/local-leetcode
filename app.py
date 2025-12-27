from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import json
import os
import logging
from dotenv import load_dotenv
from models import db, Problem, User, Submission
from runner.code_runner import evaluate_code
from sqlalchemy import func

# Load env variables
load_dotenv()

# ======================================================
# APP CONFIG
# ======================================================

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")

# Verify Database URL
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("❌ DATABASE_URL missing in environment variables")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize DB with App
db.init_app(app)

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
# AUTH HELPERS
# ======================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        return dict(current_user=user)
    return dict(current_user=None)

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
    problems = Problem.query.order_by(Problem.id).all()
    
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
# ROUTES – AUTH
# ======================================================

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if not username or not password:
            flash("Please fill in all fields")
            return redirect(url_for("signup"))
            
        existing = User.query.filter_by(username=username).first()
        if existing:
            flash("Username already taken")
            return redirect(url_for("signup"))
            
        # Use pbkdf2:sha256 for compatibility
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        
        flash("Account created! Please login.")
        return redirect(url_for("login"))
        
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash(f"Welcome back, {user.username}!")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password")
            return redirect(url_for("login"))
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))

# ======================================================
# ROUTES – APP
# ======================================================

@app.route("/")
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route("/")
@app.route("/problem")
@app.route("/problem/")
@app.route("/problem/<problem_id>")
@login_required
def show_problem(problem_id=None):
    sidebar = load_problem_index()

    if not sidebar:
        return "❌ No problems found in Database."

    if problem_id is None:
        try:
            problem_id = sidebar[0]["problems"][0]["id"]
        except:
             return "❌ No problems available."
    
    logger.info(f"👀 View Problem: {problem_id}")
    
    # Fetch solved IDs for sidebar
    solved_ids = set()
    if 'user_id' in session:
        submissions = db.session.query(Submission.problem_id).filter_by(
            user_id=session['user_id'], status='passed'
        ).distinct().all()
        solved_ids = set([s[0] for s in submissions])

    try:
        problem = load_problem(problem_id)
        # Check if current problem is solved
        problem['is_solved'] = (problem_id in solved_ids)
        
    except Exception as e:
        return f"❌ {str(e)}"

    return render_template(
        "problem.html",
        problem=problem,
        sidebar=sidebar,
        solved=solved_ids
    )

@app.route("/run", methods=["POST"])
@login_required
def run_code():
    data = request.json
    code = data.get("code")
    problem_id = data.get("problem_id")
    
    if not code or not problem_id:
         return jsonify({"passed": False, "details": [{"status": "error", "error": "Missing code or problem_id"}]})
    
    logger.info(f"🚀 Run Code: {problem_id}")

    try:
        problem_data = load_problem(problem_id)
        passed, details = evaluate_code(code, problem_data)
        
        # Save Submission
        status = 'passed' if passed else 'failed'
        new_submission = Submission(
            user_id=session['user_id'],
            problem_id=problem_id,
            code=code,
            status=status
        )
        db.session.add(new_submission)
        db.session.commit()
        
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


@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session['user_id']
    
    # 1. Fetch all problems (for total counts)
    all_problems = Problem.query.all()
    
    # 2. Fetch user's passed submissions (distinct problem_ids)
    solved_problems = db.session.query(Submission.problem_id).filter_by(
        user_id=user_id, status='passed'
    ).distinct().all()
    solved_ids = set([s[0] for s in solved_problems])
    
    # 3. Build Stats
    stats = {
        "total": len(all_problems),
        "solved": len(solved_ids),
        "easy_total": 0, "easy_solved": 0,
        "med_total": 0, "med_solved": 0,
        "hard_total": 0, "hard_solved": 0
    }
    
    # 4. Group by difficulty
    # We can optimize this later with group_by queries but pure python is fine for <1000 items
    for p in all_problems:
        diff = (p.difficulty or "Easy").lower()
        if "easy" in diff:
            stats["easy_total"] += 1
            if p.id in solved_ids: stats["easy_solved"] += 1
        elif "medium" in diff:
            stats["med_total"] += 1
            if p.id in solved_ids: stats["med_solved"] += 1
        elif "hard" in diff:
            stats["hard_total"] += 1
            if p.id in solved_ids: stats["hard_solved"] += 1
            
    # Sidebar is still needed for list details? 
    # Or we can pass a enriched object.
    # Let's pass 'curriculum' object to template with solved flags.
    
    sidebar = load_problem_index()
    
    # Inject 'solved' status into sidebar for dashboard view
    # sidebar structure: [{'day': 'Easy Problems', 'problems': [{id, title...}]}]
    for group in sidebar:
        group_solved = 0
        for p in group['problems']:
            is_solved = (p['id'] in solved_ids)
            p['solved'] = is_solved
            if is_solved:
                group_solved += 1
        
        group['solved_count'] = group_solved
        group['total_count'] = len(group['problems'])
            
    return render_template("dashboard.html", stats=stats, curriculum=sidebar)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080))
    )