import sqlite3
import os
from datetime import datetime

DB_FILE = "leetcode.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database tables."""
    with get_db() as conn:
        # Check if table exists and has user_id, if not drop (simplest migration for dev)
        try:
            conn.execute("SELECT user_id FROM solves LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute("DROP TABLE IF EXISTS solves")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS solves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                problem_id TEXT NOT NULL,
                solved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, problem_id)
            )
        """)
        conn.commit()

def mark_solved(user_id, problem_id):
    """Mark a problem as solved for a specific user."""
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO solves (user_id, problem_id) VALUES (?, ?)",
                (user_id, problem_id)
            )
            conn.commit()
    except Exception as e:
        print(f"DB Error: {e}")

def get_solved_problems(user_id):
    """Return a list of solved problem IDs for a user."""
    with get_db() as conn:
        cursor = conn.execute("SELECT problem_id FROM solves WHERE user_id = ?", (user_id,))
        return [row["problem_id"] for row in cursor.fetchall()]

def get_solve_stats(user_id):
    """Return stats for the dashboard timeline."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT date(solved_at) as day, count(*) as count FROM solves WHERE user_id = ? GROUP BY day",
            (user_id,)
        )
        return {row["day"]: row["count"] for row in cursor.fetchall()}
