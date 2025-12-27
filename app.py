from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import json
import os
import logging
from dotenv import load_dotenv
from models import db, Problem, User
from runner.code_runner import evaluate_code

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
    
    try:
        problem = load_problem(problem_id)
    except Exception as e:
        return f"❌ {str(e)}"

    return render_template(
        "problem.html",
        problem=problem,
        sidebar=sidebar
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

@app.route("/dashboard")
@login_required
def dashboard():
    sidebar = load_problem_index()
    return render_template("dashboard.html", sidebar=sidebar)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080))
    )