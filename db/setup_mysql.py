"""
QueryMind – MySQL Schema Setup & Sample Data
Run this script once to create tables and populate sample academic data.

Usage:
    python db/setup_mysql.py
"""

import pymysql
import hashlib
import os

# ── Connection settings ──────────────────────────────────────────────────────
MYSQL_HOST     = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT     = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER     = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB       = os.getenv("MYSQL_DB", "querymind_db")

# ── DDL ───────────────────────────────────────────────────────────────────────
DDL = """
CREATE TABLE IF NOT EXISTS app_users (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(80)  NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    role          ENUM('admin','teacher','student') NOT NULL DEFAULT 'student'
);

CREATE TABLE IF NOT EXISTS students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    division   VARCHAR(10)  NOT NULL,
    email      VARCHAR(150)
);

CREATE TABLE IF NOT EXISTS subjects (
    subject_id   INT AUTO_INCREMENT PRIMARY KEY,
    subject_name VARCHAR(100) NOT NULL,
    credits      TINYINT      NOT NULL DEFAULT 3
);

CREATE TABLE IF NOT EXISTS marks (
    mark_id    INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    marks      DECIMAL(5,2) NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

CREATE TABLE IF NOT EXISTS attendance (
    attendance_id        INT AUTO_INCREMENT PRIMARY KEY,
    student_id           INT            NOT NULL,
    subject_id           INT            NOT NULL,
    attendance_percentage DECIMAL(5,2)  NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);
"""

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def setup():
    conn = pymysql.connect(
        host=MYSQL_HOST, port=MYSQL_PORT,
        user=MYSQL_USER, password=MYSQL_PASSWORD,
        autocommit=True, cursorclass=pymysql.cursors.DictCursor
    )
    cur = conn.cursor()

    # Create database
    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cur.execute(f"USE `{MYSQL_DB}`")

    # Create tables
    for stmt in DDL.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            cur.execute(stmt)

    # ── Seed app_users ────────────────────────────────────────────────────────
    users = [
        ("admin",   _hash("admin123"),   "admin"),
        ("teacher1",_hash("teach123"),   "teacher"),
        ("student1",_hash("stud123"),    "student"),
    ]
    cur.execute("SELECT COUNT(*) AS cnt FROM app_users")
    if cur.fetchone()["cnt"] == 0:
        cur.executemany(
            "INSERT INTO app_users (username, password_hash, role) VALUES (%s,%s,%s)",
            users
        )

    # ── Seed subjects ─────────────────────────────────────────────────────────
    subjects = [
        ("Mathematics", 4),
        ("Physics", 3),
        ("Chemistry", 3),
        ("Computer Science", 4),
        ("English", 2),
    ]
    cur.execute("SELECT COUNT(*) AS cnt FROM subjects")
    if cur.fetchone()["cnt"] == 0:
        cur.executemany(
            "INSERT INTO subjects (subject_name, credits) VALUES (%s,%s)",
            subjects
        )

    # ── Seed students ─────────────────────────────────────────────────────────
    divisions = ["A", "A", "A", "B", "B", "B", "C", "C", "A", "B",
                 "C", "A", "B", "C", "A", "B", "C", "A", "B", "C"]
    student_names = [
        "Aarav Sharma", "Priya Patel", "Rohan Mehta", "Sneha Reddy", "Arjun Singh",
        "Kavya Nair", "Vikram Gupta", "Meena Iyer", "Aditya Joshi", "Pooja Desai",
        "Siddharth Rao", "Ananya Krishnan", "Kiran Bhat", "Divya Menon", "Rahul Choudhary",
        "Riya Shah", "Nikhil Verma", "Sana Khan", "Tarun Kumar", "Preeti Yadav",
    ]
    cur.execute("SELECT COUNT(*) AS cnt FROM students")
    if cur.fetchone()["cnt"] == 0:
        rows = [(n, d, f"{n.split()[0].lower()}@college.edu")
                for n, d in zip(student_names, divisions)]
        cur.executemany("INSERT INTO students (name, division, email) VALUES (%s,%s,%s)", rows)

    # ── Seed marks and attendance ─────────────────────────────────────────────
    import random
    random.seed(42)
    cur.execute("SELECT COUNT(*) AS cnt FROM marks")
    if cur.fetchone()["cnt"] == 0:
        cur.execute("SELECT student_id FROM students")
        sids = [r["student_id"] for r in cur.fetchall()]
        cur.execute("SELECT subject_id FROM subjects")
        subids = [r["subject_id"] for r in cur.fetchall()]
        marks_data = []
        attend_data = []
        for sid in sids:
            for subid in subids:
                m = round(random.uniform(35, 100), 2)
                a = round(random.uniform(50, 100), 2)
                marks_data.append((sid, subid, m))
                attend_data.append((sid, subid, a))
        cur.executemany(
            "INSERT INTO marks (student_id, subject_id, marks) VALUES (%s,%s,%s)",
            marks_data
        )
        cur.executemany(
            "INSERT INTO attendance (student_id, subject_id, attendance_percentage) VALUES (%s,%s,%s)",
            attend_data
        )

    conn.close()
    print("✅  QueryMind database setup complete.")
    print(f"    Database : {MYSQL_DB}")
    print(f"    Users    : admin / teacher1 / student1")


if __name__ == "__main__":
    setup()
