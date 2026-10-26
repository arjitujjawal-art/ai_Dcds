"""
QueryMind NLP Engine — Rule-Based Natural Language to SQL
SQLite-compatible queries. 13 patterns covering all spec examples.
"""

import re

PATTERNS = [
    # Top N students by average marks
    {
        "keywords": ["top","student","average","mark"],
        "template": (
            "SELECT s.student_id, s.name, s.division, "
            "ROUND(AVG(m.marks),2) AS avg_marks "
            "FROM students s "
            "JOIN marks m ON s.student_id = m.student_id "
            "GROUP BY s.student_id, s.name, s.division "
            "ORDER BY avg_marks DESC "
            "LIMIT {limit}"
        ),
        "extract": {"limit": r"\b(\d+)\b"},
        "defaults": {"limit": 5},
        "description": "Top {limit} students by average marks",
    },
    # Average attendance per division
    {
        "keywords": ["average","attendance","division"],
        "template": (
            "SELECT s.division, ROUND(AVG(a.attendance_percentage),2) AS avg_attendance "
            "FROM students s "
            "JOIN attendance a ON s.student_id = a.student_id "
            "GROUP BY s.division "
            "ORDER BY avg_attendance DESC"
        ),
        "extract": {},
        "defaults": {},
        "description": "Average attendance per division",
    },
    # Subjects below average score
    {
        "keywords": ["subject","average","score","below"],
        "template": (
            "SELECT sub.subject_name, ROUND(AVG(m.marks),2) AS avg_score "
            "FROM subjects sub "
            "JOIN marks m ON sub.subject_id = m.subject_id "
            "GROUP BY sub.subject_name "
            "HAVING avg_score < {threshold} "
            "ORDER BY avg_score"
        ),
        "extract": {"threshold": r"\b(\d+)\b"},
        "defaults": {"threshold": 60},
        "description": "Subjects with average score below {threshold}",
    },
    # Count students scoring above N per subject
    {
        "keywords": ["count","student","above","subject"],
        "template": (
            "SELECT sub.subject_name, COUNT(*) AS student_count "
            "FROM marks m "
            "JOIN subjects sub ON m.subject_id = sub.subject_id "
            "WHERE m.marks > {threshold} "
            "GROUP BY sub.subject_name "
            "ORDER BY student_count DESC"
        ),
        "extract": {"threshold": r"\b(\d+)\b"},
        "defaults": {"threshold": 80},
        "description": "Students scoring above {threshold} per subject",
    },
    # Students with attendance below threshold
    {
        "keywords": ["student","attendance","below"],
        "template": (
            "SELECT s.name, s.division, "
            "ROUND(AVG(a.attendance_percentage),2) AS avg_attendance "
            "FROM students s "
            "JOIN attendance a ON s.student_id = a.student_id "
            "GROUP BY s.student_id, s.name, s.division "
            "HAVING avg_attendance < {threshold} "
            "ORDER BY avg_attendance"
        ),
        "extract": {"threshold": r"\b(\d+)\b"},
        "defaults": {"threshold": 75},
        "description": "Students with attendance below {threshold}%",
    },
    # Compare marks across divisions
    {
        "keywords": ["compare","average","mark","division"],
        "template": (
            "SELECT s.division, ROUND(AVG(m.marks),2) AS avg_marks "
            "FROM students s "
            "JOIN marks m ON s.student_id = m.student_id "
            "GROUP BY s.division "
            "ORDER BY avg_marks DESC"
        ),
        "extract": {},
        "defaults": {},
        "description": "Average marks compared across divisions",
    },
    # Average marks per subject
    {
        "keywords": ["average","mark","subject"],
        "template": (
            "SELECT sub.subject_name, ROUND(AVG(m.marks),2) AS avg_marks "
            "FROM subjects sub "
            "JOIN marks m ON sub.subject_id = m.subject_id "
            "GROUP BY sub.subject_name "
            "ORDER BY avg_marks DESC"
        ),
        "extract": {},
        "defaults": {},
        "description": "Average marks per subject",
    },
    # All students
    {
        "keywords": ["show","all","student"],
        "template": (
            "SELECT student_id, name, division, email "
            "FROM students ORDER BY name"
        ),
        "extract": {},
        "defaults": {},
        "description": "All students",
    },
    # All subjects
    {
        "keywords": ["show","subject"],
        "template": (
            "SELECT subject_id, subject_name, credits "
            "FROM subjects ORDER BY subject_name"
        ),
        "extract": {},
        "defaults": {},
        "description": "All subjects",
    },
    # Count students per division
    {
        "keywords": ["count","student","division"],
        "template": (
            "SELECT division, COUNT(*) AS student_count "
            "FROM students GROUP BY division ORDER BY division"
        ),
        "extract": {},
        "defaults": {},
        "description": "Student count per division",
    },
    # Top N by raw marks
    {
        "keywords": ["top","student","mark"],
        "template": (
            "SELECT s.name, s.division, m.marks, sub.subject_name "
            "FROM students s "
            "JOIN marks m ON s.student_id = m.student_id "
            "JOIN subjects sub ON m.subject_id = sub.subject_id "
            "ORDER BY m.marks DESC LIMIT {limit}"
        ),
        "extract": {"limit": r"\b(\d+)\b"},
        "defaults": {"limit": 5},
        "description": "Top {limit} mark records",
    },
    # Min / Max marks per subject
    {
        "keywords": ["min","max","mark","subject"],
        "template": (
            "SELECT sub.subject_name, "
            "MIN(m.marks) AS min_marks, MAX(m.marks) AS max_marks "
            "FROM subjects sub "
            "JOIN marks m ON sub.subject_id = m.subject_id "
            "GROUP BY sub.subject_name"
        ),
        "extract": {},
        "defaults": {},
        "description": "Min and max marks per subject",
    },
    # Total credits
    {
        "keywords": ["total","credit"],
        "template": "SELECT SUM(credits) AS total_credits FROM subjects",
        "extract": {},
        "defaults": {},
        "description": "Total credits",
    },
]


def _tokens(question: str) -> set:
    words = re.sub(r"[^a-z0-9\s]", "", question.lower()).split()
    out = set()
    for w in words:
        out.add(w)
        if w.endswith("s") and len(w) > 3:
            out.add(w[:-1])   # simple plural stem
    return out


def generate_sql(question: str) -> dict:
    toks = _tokens(question)

    best, score = None, 0
    for p in PATTERNS:
        s = sum(1 for kw in p["keywords"] if kw in toks)
        if s > score:
            score, best = s, p

    if best and score >= 2:
        params = dict(best["defaults"])
        for key, rx in best["extract"].items():
            m = re.search(rx, question)
            if m:
                params[key] = int(m.group(1))
        sql  = best["template"].format(**params)
        desc = best["description"]
        try:
            desc = desc.format(**params)
        except KeyError:
            pass
        return {"sql": sql, "description": desc, "matched": True, "confidence": score}

    return {
        "sql": None,
        "description": (
            "I couldn't understand that question. Try asking about "
            "students, marks, attendance, or subjects."
        ),
        "matched": False,
        "confidence": score,
    }
