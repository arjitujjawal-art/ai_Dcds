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
        input_mode       TEXT DEFAULT 'text',
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

    # Migration for query_logs input_mode
    try:
        col_names = [col[1] for col in c.execute("PRAGMA table_info(query_logs)").fetchall()]
        if "input_mode" not in col_names:
            c.execute("ALTER TABLE query_logs ADD COLUMN input_mode TEXT DEFAULT 'text'")
    except Exception:
        pass

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


def explain_query_plan(sql: str) -> dict:
    """
    Run EXPLAIN QUERY PLAN on a validated SELECT query to introspect
    the DBMS query execution tree, scan strategies, and B-Tree usage.
    """
    import re
    try:
        conn = _conn()
        c = conn.cursor()
        c.execute(f"EXPLAIN QUERY PLAN {sql}")
        raw_rows = c.fetchall()
        conn.close()

        plan_steps = []
        has_index_scan = False
        has_temp_btree = False
        tables_accessed = []

        for r in raw_rows:
            step_id = r[0] if len(r) > 0 else 0
            parent_id = r[1] if len(r) > 1 else 0
            detail = r[3] if len(r) > 3 else (r[0] if isinstance(r[0], str) else str(r))

            step_type = "SCAN"
            if "SEARCH" in detail.upper():
                step_type = "INDEX_SEARCH"
                has_index_scan = True
            elif "SCAN" in detail.upper():
                step_type = "FULL_TABLE_SCAN"
            elif "USE TEMP B-TREE" in detail.upper():
                step_type = "TEMP_BTREE_SORT"
                has_temp_btree = True
            elif "COMPOUND" in detail.upper():
                step_type = "COMPOUND_SUBQUERY"

            tbl_match = re.search(r"(?:SCAN|SEARCH)\s+(?:TABLE\s+)?([a-zA-Z0-9_]+)", detail, re.IGNORECASE)
            tbl = tbl_match.group(1) if tbl_match else None

            plan_steps.append({
                "id": step_id,
                "parent": parent_id,
                "detail": detail,
                "step_type": step_type,
                "table": tbl
            })

        # Detect all database tables referenced in the query
        for kt in ["students", "marks", "subjects", "attendance", "app_users", "query_logs", "audit_logs"]:
            if re.search(rf"\b{kt}\b", sql, re.IGNORECASE) and kt not in tables_accessed:
                tables_accessed.append(kt)

        return {
            "status": "success",
            "sql": sql,
            "steps": plan_steps,
            "summary": {
                "step_count": len(plan_steps),
                "has_index_scan": has_index_scan,
                "has_temp_btree": has_temp_btree,
                "tables_accessed": tables_accessed,
                "optimization_level": "High (Indexed)" if has_index_scan and not has_temp_btree else ("Moderate (Sorted with B-Tree)" if has_temp_btree else "Sequential (Full Scan)")
            },
            "error": None
        }
    except Exception as exc:
        return {
            "status": "error",
            "sql": sql,
            "steps": [],
            "summary": {},
            "error": str(exc)
        }


# ══════════════════════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════════════════════

def log_query(user_id, username, question, sql, status,
              execution_ms, row_count, error=None, input_mode="text"):
    try:
        conn = _conn()
        conn.execute(
            """INSERT INTO query_logs
               (user_id, username, question, generated_sql, status,
                execution_time_ms, result_row_count, error, input_mode)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (user_id, username, question, sql, status,
             execution_ms, row_count, error, input_mode)
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


def generate_er_diagram_mermaid(schema_dict: dict, relationships: list) -> str:
    """Generate Mermaid ER syntax from real introspected SQLite metadata."""
    lines = ["erDiagram"]
    er_tables = ["students", "subjects", "marks", "attendance"]
    for t in schema_dict:
        if t not in er_tables and schema_dict[t]["category"] != "system":
            er_tables.append(t)

    for tbl_name in er_tables:
        if tbl_name not in schema_dict:
            continue
        tbl = schema_dict[tbl_name]
        lines.append(f"    {tbl_name} {{")
        for c in tbl["columns"]:
            c_type = (c["type"] or "TEXT").split("(")[0].strip()
            m_type = "string"
            if "INT" in c_type.upper():
                m_type = "int"
            elif any(f in c_type.upper() for f in ("REAL", "FLOAT", "NUMERIC", "DECIMAL", "DOUBLE")):
                m_type = "float"

            flag = ""
            if c["pk"]:
                flag = "PK"
            elif c["fk"]:
                flag = "FK"
            lines.append(f"        {m_type} {c['name']} {flag}".rstrip())
        lines.append("    }")

    for rel in relationships:
        if rel["from_table"] in er_tables and rel["to_table"] in er_tables:
            label = f"{rel['from_column']}"
            lines.append(f'    {rel["to_table"]} ||--o{{ {rel["from_table"]} : "{label}"')

    return "\n".join(lines)


def get_database_schema_metadata() -> dict:
    """
    Introspect live SQLite metadata for all tables, columns, constraints,
    primary keys, foreign keys, row counts, and sample records.
    """
    conn = _conn()
    tables = [
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    ]

    schema_dict = {}
    er_relationships = []

    for tbl in tables:
        col_info = conn.execute(f'PRAGMA table_info("{tbl}")').fetchall()
        fk_list = conn.execute(f'PRAGMA foreign_key_list("{tbl}")').fetchall()

        fk_map = {}
        for fk in fk_list:
            from_col = fk[3]
            to_tbl = fk[2]
            to_col = fk[4]
            fk_map[from_col] = {"table": to_tbl, "to_column": to_col}
            er_relationships.append({
                "from_table": tbl,
                "from_column": from_col,
                "to_table": to_tbl,
                "to_column": to_col,
            })

        columns = []
        for c in col_info:
            cid, cname, ctype, notnull, dflt, pk = c
            columns.append({
                "name": cname,
                "type": ctype or "TEXT",
                "notnull": bool(notnull),
                "default": dflt,
                "pk": bool(pk),
                "fk": fk_map.get(cname),
            })

        try:
            row_count = conn.execute(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()[0]
        except Exception:
            row_count = 0

        sample_rows = []
        try:
            raw_sample = conn.execute(f'SELECT * FROM "{tbl}" LIMIT 5').fetchall()
            col_names = [col["name"] for col in columns]
            sample_rows = [dict(zip(col_names, r)) for r in raw_sample]
        except Exception:
            pass

        category = "academic"
        if tbl in ("app_users", "query_logs", "audit_logs", "query_feedback", "dataset_registry"):
            category = "system"
        elif tbl not in ("students", "subjects", "marks", "attendance"):
            category = "custom_dataset"

        schema_dict[tbl] = {
            "table_name": tbl,
            "category": category,
            "columns": columns,
            "foreign_keys": list(fk_map.values()),
            "row_count": row_count,
            "sample_rows": sample_rows,
        }

    conn.close()

    mermaid = generate_er_diagram_mermaid(schema_dict, er_relationships)

    return {
        "tables": schema_dict,
        "relationships": er_relationships,
        "er_mermaid": mermaid,
    }


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
        "datasets": c.execute("SELECT COUNT(*) FROM dataset_registry").fetchone()[0] if c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dataset_registry'").fetchone() else 0,
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


# ══════════════════════════════════════════════════════════════════════════════
# DATASET UPLOAD — Dynamic Table Management
# ══════════════════════════════════════════════════════════════════════════════

import re as _re
import pandas as _pd


_SYSTEM_TABLES = {"app_users", "students", "subjects", "marks", "attendance",
                  "query_logs", "audit_logs", "query_feedback", "sqlite_sequence",
                  "dataset_registry"}


def _setup_registry():
    """Create the dataset registry table if it doesn't exist."""
    conn = _conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dataset_registry (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name   TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            row_count    INTEGER DEFAULT 0,
            col_count    INTEGER DEFAULT 0,
            columns_json TEXT,
            uploaded_by  TEXT,
            uploaded_at  TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM dataset_registry").fetchone()[0]
    conn.close()

    if count == 0:
        sample_df = _pd.DataFrame([
            {"emp_id": 101, "name": "Aarav Sharma", "department": "Engineering", "salary": 95000, "rating": 4.8, "experience_years": 5, "city": "Mumbai"},
            {"emp_id": 102, "name": "Priya Patel", "department": "Marketing", "salary": 72000, "rating": 4.5, "experience_years": 4, "city": "Delhi"},
            {"emp_id": 103, "name": "Rohan Mehta", "department": "Engineering", "salary": 110000, "rating": 4.9, "experience_years": 7, "city": "Bengaluru"},
            {"emp_id": 104, "name": "Sneha Reddy", "department": "Finance", "salary": 88000, "rating": 4.2, "experience_years": 6, "city": "Hyderabad"},
            {"emp_id": 105, "name": "Arjun Singh", "department": "Sales", "salary": 65000, "rating": 3.9, "experience_years": 3, "city": "Pune"},
            {"emp_id": 106, "name": "Kavya Nair", "department": "HR", "salary": 62000, "rating": 4.4, "experience_years": 4, "city": "Chennai"},
            {"emp_id": 107, "name": "Vikram Gupta", "department": "Engineering", "salary": 125000, "rating": 4.9, "experience_years": 8, "city": "Bengaluru"},
            {"emp_id": 108, "name": "Meena Iyer", "department": "Marketing", "salary": 78000, "rating": 4.6, "experience_years": 5, "city": "Mumbai"},
            {"emp_id": 109, "name": "Aditya Joshi", "department": "Finance", "salary": 92000, "rating": 4.3, "experience_years": 5, "city": "Delhi"},
            {"emp_id": 110, "name": "Pooja Desai", "department": "Sales", "salary": 71000, "rating": 4.1, "experience_years": 3, "city": "Ahmedabad"},
        ])
        import_dataframe(sample_df, "company_employees", "Company Employees & Salaries", "system")


def _safe_table_name(original: str) -> str:
    """Convert any string to a safe SQLite table name."""
    name = _re.sub(r"[^\w]", "_", original.lower())
    name = _re.sub(r"_+", "_", name).strip("_")
    if not name or name[0].isdigit():
        name = "ds_" + name
    return name[:50]


def import_dataframe(df: "_pd.DataFrame", table_name: str, display_name: str,
                     uploaded_by: str = "admin") -> dict:
    """
    Given a pandas DataFrame, create a SQLite table and populate it.
    Returns a result dict with row_count, columns, and table_name.
    """
    import json

    # Sanitise column names
    df.columns = [_safe_table_name(str(c)) for c in df.columns]

    # Ensure unique table name (append _2, _3 if needed)
    base = _safe_table_name(table_name)
    candidate = base
    conn = _conn()
    existing = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    i = 2
    while candidate in existing:
        candidate = f"{base}_{i}"
        i += 1
    table_name_safe = candidate
    conn.close()

    # Write DataFrame to SQLite (pandas does the CREATE TABLE + INSERT)
    conn_raw = __import__("sqlite3").connect(DB_PATH)
    df.to_sql(table_name_safe, conn_raw, if_exists="replace", index=False)
    conn_raw.close()

    # Register the dataset
    col_info = [{"name": c, "dtype": str(df[c].dtype)} for c in df.columns]
    conn = _conn()
    conn.execute("""
        INSERT OR REPLACE INTO dataset_registry
          (table_name, display_name, row_count, col_count, columns_json, uploaded_by)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (table_name_safe, display_name, len(df), len(df.columns),
          json.dumps(col_info), uploaded_by))
    conn.commit()
    conn.close()

    return {
        "table_name": table_name_safe,
        "display_name": display_name,
        "row_count": len(df),
        "columns": list(df.columns),
        "col_info": col_info,
    }


def upload_csv_excel(file_bytes: bytes, filename: str, uploaded_by: str = "admin") -> dict:
    """
    Accept raw file bytes from a CSV or Excel upload.
    Auto-detects format from filename extension.
    Returns result from import_dataframe().
    """
    import io
    display_name = filename.rsplit(".", 1)[0]
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "csv"

    try:
        if ext in ("xlsx", "xls"):
            df = _pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
        else:
            # Try comma first, fallback to tab
            try:
                df = _pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8")
            except Exception:
                df = _pd.read_csv(io.BytesIO(file_bytes), sep="\t", encoding="utf-8")
    except Exception as exc:
        return {"error": str(exc)}

    if df.empty:
        return {"error": "The uploaded file contains no data."}

    # Drop fully empty columns/rows
    df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")

    table_name_hint = _safe_table_name(display_name)
    return import_dataframe(df, table_name_hint, display_name, uploaded_by)


def get_uploaded_datasets() -> list:
    """Return all user-uploaded datasets from the registry."""
    _setup_registry()
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM dataset_registry ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_dataset_schema(table_name: str) -> dict | None:
    """Return column info and a sample row preview for a dataset table."""
    import json
    _setup_registry()
    conn = _conn()
    reg = conn.execute(
        "SELECT * FROM dataset_registry WHERE table_name = ?", (table_name,)
    ).fetchone()
    if not reg:
        conn.close()
        return None
    reg = dict(reg)
    reg["col_info"] = json.loads(reg["columns_json"] or "[]")

    # Sample rows
    try:
        sample = conn.execute(f'SELECT * FROM "{table_name}" LIMIT 5').fetchall()
        cols = [d[0] for d in conn.execute(f'SELECT * FROM "{table_name}" LIMIT 1').description or []]
        reg["sample_rows"] = [dict(zip(cols, r)) for r in sample]
        reg["all_columns"] = cols
    except Exception:
        reg["sample_rows"] = []
        reg["all_columns"] = []

    conn.close()
    return reg


def delete_dataset(table_name: str) -> bool:
    """Drop a user-uploaded dataset table and remove its registry entry."""
    if table_name in _SYSTEM_TABLES:
        return False
    try:
        conn = _conn()
        conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        conn.execute("DELETE FROM dataset_registry WHERE table_name = ?", (table_name,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def get_dataset_table_names() -> set:
    """Return names of all registered dataset tables (for NLP routing)."""
    _setup_registry()
    conn = _conn()
    rows = conn.execute("SELECT table_name FROM dataset_registry").fetchall()
    conn.close()
    return {r[0] for r in rows}


# ── Auto-setup on import ───────────────────────────────────────────────────────
_setup()
_setup_registry()
