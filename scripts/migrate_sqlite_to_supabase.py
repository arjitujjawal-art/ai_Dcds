"""
QueryMind 2.0 – SQLite to Supabase PostgreSQL Migration Utility
Extracts relational academic data from SQLite, converts data types to PostgreSQL 15+,
and generates an idempotent SQL seed migration for Supabase.
"""

import sqlite3
import os
import uuid
import datetime
from typing import List, Dict, Any

SQLITE_DB = os.path.join(os.path.dirname(__file__), "..", "db", "querymind.db")
OUTPUT_SQL = os.path.join(os.path.dirname(__file__), "..", "migrations", "002_data_seed_supabase.sql")

def escape_pg_str(val: Any) -> str:
    """Sanitize string values for PostgreSQL literals."""
    if val is None:
        return "NULL"
    if isinstance(val, (int, float)):
        return str(val)
    val_str = str(val).replace("'", "''")
    return f"'{val_str}'"

def generate_supabase_seed_script(sqlite_path: str = SQLITE_DB, output_path: str = OUTPUT_SQL) -> str:
    """Extract records from SQLite and compile into PostgreSQL 15+ INSERT statements."""
    if not os.path.exists(sqlite_path):
        raise FileNotFoundError(f"SQLite database not found at {sqlite_path}")

    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    lines = [
        "-- ============================================================================",
        "-- QueryMind 2.0 – Supabase PostgreSQL Data Seed",
        f"-- Generated on: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        "-- Relational Data Export from Local SQLite Instance",
        "-- ============================================================================\n",
        "BEGIN;\n"
    ]

    # 1. Subjects
    cur.execute("SELECT subject_id, subject_name, credits FROM subjects ORDER BY subject_id")
    subjects = cur.fetchall()
    if subjects:
        lines.append("-- Subjects Seed")
        lines.append("INSERT INTO public.subjects (subject_id, name, department, credits) VALUES")
        subj_rows = []
        for s in subjects:
            name = s["subject_name"]
            dept = "Computer Science"
            if any(k in name.lower() for k in ["math", "calculus", "linear"]):
                dept = "Mathematics"
            elif any(k in name.lower() for k in ["physics", "mechanics"]):
                dept = "Physics"
            elif any(k in name.lower() for k in ["data", "dbms", "database", "python", "algorithms"]):
                dept = "Computer Science"
            
            subj_rows.append(f"  ({s['subject_id']}, {escape_pg_str(name)}, {escape_pg_str(dept)}, {s['credits']})")
        lines.append(",\n".join(subj_rows))
        lines.append("ON CONFLICT (subject_id) DO NOTHING;\n")

    # 2. Students
    cur.execute("SELECT student_id, name, division FROM students ORDER BY student_id")
    students = cur.fetchall()
    if students:
        lines.append("-- Students Seed")
        lines.append("INSERT INTO public.students (student_id, name, division, enrollment_year) VALUES")
        stud_rows = []
        for st in students:
            stud_rows.append(f"  ({st['student_id']}, {escape_pg_str(st['name'])}, {escape_pg_str(st['division'])}, 2024)")
        lines.append(",\n".join(stud_rows))
        lines.append("ON CONFLICT (student_id) DO NOTHING;\n")

    # 3. Marks
    cur.execute("SELECT mark_id, student_id, subject_id, marks FROM marks ORDER BY mark_id")
    marks = cur.fetchall()
    if marks:
        lines.append("-- Marks Seed")
        lines.append("INSERT INTO public.marks (mark_id, student_id, subject_id, marks, exam_type) VALUES")
        mark_rows = []
        for m in marks:
            mark_rows.append(f"  ({m['mark_id']}, {m['student_id']}, {m['subject_id']}, {m['marks']}, 'Final')")
        lines.append(",\n".join(mark_rows))
        lines.append("ON CONFLICT (student_id, subject_id, exam_type) DO UPDATE SET marks = EXCLUDED.marks;\n")

    # 4. Attendance
    cur.execute("SELECT attendance_id, student_id, subject_id, attendance_percentage FROM attendance ORDER BY attendance_id")
    att = cur.fetchall()
    if att:
        lines.append("-- Attendance Seed (Derives attended & total_classes from percentage)")
        lines.append("INSERT INTO public.attendance (att_id, student_id, subject_id, attended, total_classes) VALUES")
        att_rows = []
        for a in att:
            pct = float(a["attendance_percentage"])
            total_classes = 40
            attended = int(round((pct / 100.0) * total_classes))
            att_rows.append(f"  ({a['attendance_id']}, {a['student_id']}, {a['subject_id']}, {attended}, {total_classes})")
        lines.append(",\n".join(att_rows))
        lines.append("ON CONFLICT (student_id, subject_id) DO UPDATE SET attended = EXCLUDED.attended, total_classes = EXCLUDED.total_classes;\n")

    # Sequence alignment for PostgreSQL SERIAL columns
    lines.append("-- Align PostgreSQL Auto-Increment Sequence IDs")
    lines.append("SELECT setval(pg_get_serial_sequence('public.subjects', 'subject_id'), COALESCE(MAX(subject_id), 1)) FROM public.subjects;")
    lines.append("SELECT setval(pg_get_serial_sequence('public.students', 'student_id'), COALESCE(MAX(student_id), 1)) FROM public.students;")
    lines.append("SELECT setval(pg_get_serial_sequence('public.marks', 'mark_id'), COALESCE(MAX(mark_id), 1)) FROM public.marks;")
    lines.append("SELECT setval(pg_get_serial_sequence('public.attendance', 'att_id'), COALESCE(MAX(att_id), 1)) FROM public.attendance;\n")

    lines.append("COMMIT;\n")

    conn.close()

    full_sql = "\n".join(lines)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_sql)

    return full_sql

if __name__ == "__main__":
    sql_text = generate_supabase_seed_script()
    print(f"Successfully generated Supabase migration seed script ({len(sql_text.splitlines())} lines) at {OUTPUT_SQL}")
