"""
QueryMind — Unified SQLite Database
Works out-of-the-box with ZERO external setup.
Handles: academic data, users, query logs, audit events, feedback.
"""

import sqlite3
import hashlib
import datetime
import random
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "querymind.db")


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # rows accessible as dicts
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


# ══════════════════════════════════════════════════════════════════════════════
# SCHEMA + SEED — runs automatically on first import
# ══════════════════════════════════════════════════════════════════════════════

def _setup():
    conn = _conn()
    c = conn.cursor()

    # ── Academic tables ───────────────────────────────────────────────────────
    c.executescript("""
    CREATE TABLE IF NOT EXISTS app_users (
        user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        username      TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role          TEXT NOT NULL DEFAULT 'student'
    );

    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT NOT NULL,
        division   TEXT NOT NULL,
        email      TEXT
    );

    CREATE TABLE IF NOT EXISTS subjects (
        subject_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_name TEXT NOT NULL,
        credits      INTEGER NOT NULL DEFAULT 3
    );

    CREATE TABLE IF NOT EXISTS marks (
        mark_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL REFERENCES students(student_id),
        subject_id INTEGER NOT NULL REFERENCES subjects(subject_id),
        marks      REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS attendance (
        attendance_id         INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id            INTEGER NOT NULL REFERENCES students(student_id),
        subject_id            INTEGER NOT NULL REFERENCES subjects(subject_id),
        attendance_percentage REAL NOT NULL
    );

    -- Logging tables
    CREATE TABLE IF NOT EXISTS query_logs (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id          INTEGER,
        username         TEXT,
        question         TEXT,
        generated_sql    TEXT,
        status           TEXT,
        execution_time_ms INTEGER,
        result_row_count INTEGER,
        error            TEXT,
        timestamp        TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        user_id    INTEGER,
        username   TEXT,
        details    TEXT,
        timestamp  TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS query_feedback (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id   INTEGER,
        question  TEXT,
        sql       TEXT,
        rating    TEXT,
        comment   TEXT,
        timestamp TEXT DEFAULT (datetime('now'))
    );
    """)

    # ── Seed only if empty ────────────────────────────────────────────────────
    if c.execute("SELECT COUNT(*) FROM app_users").fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO app_users (username, password_hash, role) VALUES (?,?,?)",
            [
                ("admin",    _hash("admin123"),  "admin"),
                ("teacher1", _hash("teach123"),  "teacher"),
                ("student1", _hash("stud123"),   "student"),
            ]
        )

    if c.execute("SELECT COUNT(*) FROM subjects").fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO subjects (subject_name, credits) VALUES (?,?)",
            [
                ("Mathematics", 4),
                ("Physics", 3),
                ("Chemistry", 3),
                ("Computer Science", 4),
                ("English", 2),
            ]
        )

    if c.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
        names = [
            ("Aarav Sharma",    "A"), ("Priya Patel",    "A"), ("Rohan Mehta",    "A"),
            ("Sneha Reddy",     "B"), ("Arjun Singh",    "B"), ("Kavya Nair",     "B"),
            ("Vikram Gupta",    "C"), ("Meena Iyer",     "C"), ("Aditya Joshi",   "A"),
            ("Pooja Desai",     "B"), ("Siddharth Rao",  "C"), ("Ananya Krishnan","A"),
            ("Kiran Bhat",      "B"), ("Divya Menon",    "C"), ("Rahul Choudhary","A"),
            ("Riya Shah",       "B"), ("Nikhil Verma",   "C"), ("Sana Khan",      "A"),
            ("Tarun Kumar",     "B"), ("Preeti Yadav",   "C"),
        ]
        c.executemany(
            "INSERT INTO students (name, division, email) VALUES (?,?,?)",
            [(n, d, f"{n.split()[0].lower()}@college.edu") for n, d in names]
        )

    if c.execute("SELECT COUNT(*) FROM marks").fetchone()[0] == 0:
        random.seed(42)
        sids   = [r[0] for r in c.execute("SELECT student_id FROM students").fetchall()]
        subids = [r[0] for r in c.execute("SELECT subject_id FROM subjects").fetchall()]
        c.executemany(
            "INSERT INTO marks (student_id, subject_id, marks) VALUES (?,?,?)",
            [(s, sub, round(random.uniform(35, 100), 2)) for s in sids for sub in subids]
        )
        c.executemany(
            "INSERT INTO attendance (student_id, subject_id, attendance_percentage) VALUES (?,?,?)",
            [(s, sub, round(random.uniform(50, 100), 2)) for s in sids for sub in subids]
        )

    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# USER AUTH
# ══════════════════════════════════════════════════════════════════════════════

def get_user(username: str, password: str):
    """Return user dict if credentials match, else None."""
    conn = _conn()
    row = conn.execute(
        "SELECT user_id, username, role FROM app_users WHERE username=? AND password_hash=?",
        (username, _hash(password))
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ══════════════════════════════════════════════════════════════════════════════
# QUERY EXECUTION
# ══════════════════════════════════════════════════════════════════════════════

import time

def execute_query(sql: str, max_rows: int = 500):
    """Execute a validated SELECT query against the SQLite academic DB."""
    start = time.monotonic()
    try:
        conn = _conn()
        c = conn.cursor()
        c.execute(sql)
        raw_rows = c.fetchmany(max_rows)
        columns  = [desc[0] for desc in c.description] if c.description else []
        rows     = [dict(zip(columns, r)) for r in raw_rows]
        conn.close()
        elapsed = int((time.monotonic() - start) * 1000)
        return {"rows": rows, "columns": columns, "row_count": len(rows),
                "execution_ms": elapsed, "error": None}
    except Exception as exc:
        elapsed = int((time.monotonic() - start) * 1000)
        return {"rows": [], "columns": [], "row_count": 0,
                "execution_ms": elapsed, "error": str(exc)}


# ══════════════════════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════════════════════

def log_query(user_id, username, question, sql, status,
              execution_ms, row_count, error=None):
    try:
        conn = _conn()
        conn.execute(
            """INSERT INTO query_logs
               (user_id, username, question, generated_sql, status,
                execution_time_ms, result_row_count, error)
               VALUES (?,?,?,?,?,?,?,?)""",
            (user_id, username, question, sql, status,
             execution_ms, row_count, error)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_query_history(user_id=None, limit=50):
    conn = _conn()
    if user_id:
        rows = conn.execute(
            "SELECT * FROM query_logs WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM query_logs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_history(limit=200):
    return get_query_history(user_id=None, limit=limit)


def log_audit(event_type, user_id=None, username=None, details=None):
    try:
        conn = _conn()
        conn.execute(
            "INSERT INTO audit_logs (event_type, user_id, username, details) VALUES (?,?,?,?)",
            (event_type, user_id, username, str(details) if details else None)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_audit_logs(limit=200):
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_feedback(user_id, question, sql, rating, comment=""):
    try:
        conn = _conn()
        conn.execute(
            "INSERT INTO query_feedback (user_id, question, sql, rating, comment) VALUES (?,?,?,?,?)",
            (user_id, question, sql, rating, comment)
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def get_feedback(limit=100):
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM query_feedback ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ══════════════════════════════════════════════════════════════════════════════
# PORTAL SPECIFIC DATA HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def get_system_stats():
    """Retrieve full system metrics for the Admin Governance Portal."""
    conn = _conn()
    c = conn.cursor()
    stats = {
        "users": c.execute("SELECT COUNT(*) FROM app_users").fetchone()[0],
        "students": c.execute("SELECT COUNT(*) FROM students").fetchone()[0],
        "subjects": c.execute("SELECT COUNT(*) FROM subjects").fetchone()[0],
        "marks_records": c.execute("SELECT COUNT(*) FROM marks").fetchone()[0],
        "attendance_records": c.execute("SELECT COUNT(*) FROM attendance").fetchone()[0],
        "total_queries": c.execute("SELECT COUNT(*) FROM query_logs").fetchone()[0],
        "success_queries": c.execute("SELECT COUNT(*) FROM query_logs WHERE status='success'").fetchone()[0],
        "blocked_queries": c.execute("SELECT COUNT(*) FROM query_logs WHERE status IN ('validation_failed', 'no_match')").fetchone()[0],
        "audit_events": c.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0],
    }
    conn.close()
    return stats


def get_app_users():
    """Return all app users without exposing password hashes."""
    conn = _conn()
    rows = conn.execute("SELECT user_id, username, role FROM app_users ORDER BY user_id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_division_stats():
    """Retrieve academic performance by division for Teacher Portal."""
    conn = _conn()
    rows = conn.execute("""
        SELECT s.division, 
               COUNT(DISTINCT s.student_id) as student_count,
               ROUND(AVG(m.marks), 1) as avg_marks,
               ROUND(AVG(a.attendance_percentage), 1) as avg_attendance
        FROM students s
        LEFT JOIN marks m ON s.student_id = m.student_id
        LEFT JOIN attendance a ON s.student_id = a.student_id
        GROUP BY s.division
        ORDER BY s.division
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_defaulters(threshold=75.0):
    """Retrieve students with attendance below threshold for Teacher/Admin Radar."""
    conn = _conn()
    rows = conn.execute("""
        SELECT s.student_id, s.name, s.division, s.email,
               ROUND(AVG(a.attendance_percentage), 1) as avg_attendance
        FROM students s
        JOIN attendance a ON s.student_id = a.student_id
        GROUP BY s.student_id, s.name, s.division, s.email
        HAVING avg_attendance < ?
        ORDER BY avg_attendance ASC
    """, (threshold,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_student_profile(username="student1"):
    """Retrieve personalized academic report for student view."""
    conn = _conn()
    # Student1 is mapped to Aarav Sharma (student_id = 1)
    student = conn.execute("SELECT student_id, name, division, email FROM students WHERE student_id = 1").fetchone()
    if not student:
        conn.close()
        return None

    sid = student["student_id"]
    courses = conn.execute("""
        SELECT sub.subject_name, sub.credits,
               ROUND(m.marks, 1) as marks,
               ROUND(a.attendance_percentage, 1) as attendance
        FROM subjects sub
        JOIN marks m ON sub.subject_id = m.subject_id AND m.student_id = ?
        JOIN attendance a ON sub.subject_id = a.subject_id AND a.student_id = ?
        ORDER BY sub.subject_name
    """, (sid, sid)).fetchall()

    summary = conn.execute("""
        SELECT ROUND(AVG(m.marks), 1) as gpa_marks,
               ROUND(AVG(a.attendance_percentage), 1) as avg_attendance
        FROM marks m
        JOIN attendance a ON m.student_id = a.student_id
        WHERE m.student_id = ?
    """, (sid,)).fetchone()

    conn.close()
    return {
        "info": dict(student),
        "courses": [dict(c) for c in courses],
        "avg_marks": summary["gpa_marks"] if summary else 0,
        "avg_attendance": summary["avg_attendance"] if summary else 0,
    }


# ── Auto-setup on import ───────────────────────────────────────────────────────
_setup()

