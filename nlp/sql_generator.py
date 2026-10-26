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


# ── Dynamic NLP for any uploaded dataset ─────────────────────────────────────

def generate_sql_for_dataset(question: str, table_name: str, columns: list) -> dict:
    """
    Generate SQL for any uploaded dataset table using generic patterns.
    Columns is a list of column name strings.
    """
    q = question.lower().strip()
    toks = _tokens(q)
    num_match = re.search(r"\b(\d+)\b", q)
    limit_n = int(num_match.group(1)) if num_match else 10

    # Detect numeric and text columns
    numeric_cols = [c for c in columns if any(k in c.lower() for k in
                    ("marks","score","grade","salary","price","amount",
                     "count","total","avg","rate","value","age","year",
                     "number","num","qty","quantity","revenue","profit"))]
    cat_cols = [c for c in columns if c not in numeric_cols]

    first_col = columns[0] if columns else "id"
    num_col   = numeric_cols[0] if numeric_cols else (columns[1] if len(columns) > 1 else columns[0])
    cat_col   = cat_cols[0] if cat_cols else columns[0]

    tbl = f'"{table_name}"'

    # ── Pattern matching ───────────────────────────────────────────────────────

    # Show all
    if any(k in toks for k in ("all","every","list","show","display","fetch","get")):
        if not any(k in toks for k in ("top","above","below","count","average","avg","sum","max","min","group")):
            return {
                "sql": f"SELECT * FROM {tbl} LIMIT 200",
                "description": f"All records from {table_name}",
                "matched": True, "confidence": 3,
            }

    # Top N by numeric column
    if "top" in toks or "highest" in toks or "best" in toks or "maximum" in toks:
        col = num_col
        # try to find a column mentioned by name
        for c in columns:
            if c.lower() in q:
                col = c; break
        return {
            "sql": f'SELECT * FROM {tbl} ORDER BY "{col}" DESC LIMIT {limit_n}',
            "description": f"Top {limit_n} records by {col}",
            "matched": True, "confidence": 3,
        }

    # Bottom N / lowest
    if "bottom" in toks or "lowest" in toks or "worst" in toks or "minimum" in toks:
        col = num_col
        for c in columns:
            if c.lower() in q:
                col = c; break
        return {
            "sql": f'SELECT * FROM {tbl} ORDER BY "{col}" ASC LIMIT {limit_n}',
            "description": f"Bottom {limit_n} records by {col}",
            "matched": True, "confidence": 3,
        }

    # Count / group by
    if "count" in toks or "group" in toks or "each" in toks or "per" in toks or "by" in toks:
        col = cat_col
        for c in columns:
            if c.lower() in q and c != num_col:
                col = c; break
        return {
            "sql": f'SELECT "{col}", COUNT(*) AS count FROM {tbl} GROUP BY "{col}" ORDER BY count DESC',
            "description": f"Count grouped by {col}",
            "matched": True, "confidence": 3,
        }

    # Average / mean
    if "average" in toks or "avg" in toks or "mean" in toks:
        col = num_col
        for c in columns:
            if c.lower() in q:
                col = c; break
        grp = cat_col
        for c in columns:
            if c.lower() in q and c != col:
                grp = c; break
        if grp != col:
            return {
                "sql": f'SELECT "{grp}", ROUND(AVG("{col}"), 2) AS avg_{col} FROM {tbl} GROUP BY "{grp}" ORDER BY avg_{col} DESC',
                "description": f"Average {col} grouped by {grp}",
                "matched": True, "confidence": 3,
            }
        return {
            "sql": f'SELECT ROUND(AVG("{col}"), 2) AS avg_{col} FROM {tbl}',
            "description": f"Average value of {col}",
            "matched": True, "confidence": 3,
        }

    # Sum / total
    if "sum" in toks or "total" in toks:
        col = num_col
        for c in columns:
            if c.lower() in q:
                col = c; break
        return {
            "sql": f'SELECT ROUND(SUM("{col}"), 2) AS total_{col} FROM {tbl}',
            "description": f"Total sum of {col}",
            "matched": True, "confidence": 3,
        }

    # Above / greater than
    if "above" in toks or "greater" in toks or "more" in toks or "exceed" in toks:
        col = num_col
        for c in columns:
            if c.lower() in q:
                col = c; break
        threshold = limit_n
        return {
            "sql": f'SELECT * FROM {tbl} WHERE "{col}" > {threshold} ORDER BY "{col}" DESC',
            "description": f"Records where {col} > {threshold}",
            "matched": True, "confidence": 3,
        }

    # Below / less than
    if "below" in toks or "less" in toks or "under" in toks:
        col = num_col
        for c in columns:
            if c.lower() in q:
                col = c; break
        threshold = limit_n
        return {
            "sql": f'SELECT * FROM {tbl} WHERE "{col}" < {threshold} ORDER BY "{col}" ASC',
            "description": f"Records where {col} < {threshold}",
            "matched": True, "confidence": 3,
        }

    # Min / max
    if "min" in toks and "max" in toks:
        col = num_col
        for c in columns:
            if c.lower() in q:
                col = c; break
        return {
            "sql": f'SELECT MIN("{col}") AS min_{col}, MAX("{col}") AS max_{col} FROM {tbl}',
            "description": f"Min and max of {col}",
            "matched": True, "confidence": 3,
        }

    if "min" in toks or "minimum" in toks:
        col = num_col
        return {
            "sql": f'SELECT * FROM {tbl} ORDER BY "{col}" ASC LIMIT {limit_n}',
            "description": f"Records with lowest {col}",
            "matched": True, "confidence": 3,
        }

    if "max" in toks or "maximum" in toks:
        col = num_col
        return {
            "sql": f'SELECT * FROM {tbl} ORDER BY "{col}" DESC LIMIT {limit_n}',
            "description": f"Records with highest {col}",
            "matched": True, "confidence": 3,
        }

    # Column mentioned by exact name → show all filtered by it
    for c in columns:
        if c.lower() in q and len(c) > 2:
            return {
                "sql": f'SELECT "{c}", COUNT(*) AS count FROM {tbl} GROUP BY "{c}" ORDER BY count DESC',
                "description": f"Distribution of {c}",
                "matched": True, "confidence": 2,
            }

    # Default: show all
    return {
        "sql": f"SELECT * FROM {tbl} LIMIT 50",
        "description": f"First 50 records from {table_name}",
        "matched": True, "confidence": 1,
    }
