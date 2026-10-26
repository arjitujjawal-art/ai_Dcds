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
    Fully supports English, Hindi, and Hinglish vernacular (e.g., 'average nikalna hai',
    'sabse jyada salary kiski hai', 'top 5 dikhao', 'department wise count').
    """
    q = question.lower().strip()
    toks = _tokens(q)
    num_match = re.search(r"\b(\d+)\b", q)
    limit_n = int(num_match.group(1)) if num_match else 10

    # Detect numeric and text columns
    numeric_cols = [c for c in columns if any(k in c.lower() for k in
                    ("marks","score","grade","salary","price","amount",
                     "count","total","avg","rate","value","age","year",
                     "number","num","qty","quantity","revenue","profit","cost","sales","units"))]
    cat_cols = [c for c in columns if c not in numeric_cols]

    num_col = numeric_cols[0] if numeric_cols else (columns[1] if len(columns) > 1 else columns[0])
    cat_col = cat_cols[0] if cat_cols else columns[0]

    tbl = f'"{table_name}"'

    # Keyword synonyms (English + Hindi/Hinglish)
    is_avg = any(k in toks or k in q for k in ("average", "avg", "mean", "ausat", "nikalna", "nikalo", "nikal", "madhya"))
    is_top = any(k in toks or k in q for k in ("top", "highest", "best", "maximum", "max", "sabse jyada", "sabse bada", "zyada", "jyada", "accha", "peak"))
    is_bottom = any(k in toks or k in q for k in ("bottom", "lowest", "worst", "minimum", "min", "sabse kam", "sabse chhota", "kam", "least"))
    is_count = any(k in toks or k in q for k in ("count", "kitne", "kitna", "ginna", "gino", "sankhya", "each", "per", "group by", "wise", "hisab"))
    is_sum = any(k in toks or k in q for k in ("sum", "total", "kul", "jod", "jodo", "pura sum"))
    is_show_all = any(k in toks or k in q for k in ("all", "every", "list", "show", "display", "fetch", "get", "dikhao", "dekho", "batao", "sabhi", "saara"))

    # Try to identify an explicit column mentioned in question
    mentioned_col = None
    for c in columns:
        c_clean = c.lower().replace("_", " ")
        if c.lower() in q or c_clean in q:
            mentioned_col = c
            break

    # 1. Average / Mean ("average nikalna hai", "average of salary")
    if is_avg:
        target_col = mentioned_col if (mentioned_col and mentioned_col in numeric_cols) else num_col
        # Check for group by / per category
        grp_col = None
        for c in cat_cols:
            if c.lower() in q or c.lower().replace("_", " ") in q:
                grp_col = c
                break
        if grp_col and grp_col != target_col:
            return {
                "sql": f'SELECT "{grp_col}", ROUND(AVG("{target_col}"), 2) AS avg_{target_col} FROM {tbl} GROUP BY "{grp_col}" ORDER BY avg_{target_col} DESC',
                "description": f"Average {target_col} grouped by {grp_col}",
                "matched": True, "confidence": 3,
            }
        return {
            "sql": f'SELECT ROUND(AVG("{target_col}"), 2) AS avg_{target_col} FROM {tbl}',
            "description": f"Average value of {target_col}",
            "matched": True, "confidence": 3,
        }

    # 2. Top N / Highest ("top 5", "sabse jyada", "highest marks")
    if is_top:
        target_col = mentioned_col if (mentioned_col and mentioned_col in numeric_cols) else num_col
        return {
            "sql": f'SELECT * FROM {tbl} ORDER BY "{target_col}" DESC LIMIT {limit_n}',
            "description": f"Top {limit_n} records by {target_col}",
            "matched": True, "confidence": 3,
        }

    # 3. Bottom N / Lowest ("sabse kam", "lowest", "worst")
    if is_bottom:
        target_col = mentioned_col if (mentioned_col and mentioned_col in numeric_cols) else num_col
        return {
            "sql": f'SELECT * FROM {tbl} ORDER BY "{target_col}" ASC LIMIT {limit_n}',
            "description": f"Bottom {limit_n} records by {target_col}",
            "matched": True, "confidence": 3,
        }

    # 4. Count / Group By ("count by department", "har division me kitne students hain")
    if is_count:
        if any(w in q for w in ("total kitne", "total count", "kul sankhya", "how many records", "kitne records", "total records")):
            return {
                "sql": f'SELECT COUNT(*) AS total_records FROM {tbl}',
                "description": f"Total record count in {table_name}",
                "matched": True, "confidence": 3,
            }
        target_col = mentioned_col or cat_col
        return {
            "sql": f'SELECT "{target_col}", COUNT(*) AS count FROM {tbl} GROUP BY "{target_col}" ORDER BY count DESC',
            "description": f"Count grouped by {target_col}",
            "matched": True, "confidence": 3,
        }

    # 5. Sum / Total ("total salary", "kul jod")
    if is_sum:
        target_col = mentioned_col if (mentioned_col and mentioned_col in numeric_cols) else num_col
        return {
            "sql": f'SELECT ROUND(SUM("{target_col}"), 2) AS total_{target_col} FROM {tbl}',
            "description": f"Total sum of {target_col}",
            "matched": True, "confidence": 3,
        }

    # 6. Min / Max
    if ("min" in toks and "max" in toks) or ("minimum" in q and "maximum" in q):
        target_col = mentioned_col if (mentioned_col and mentioned_col in numeric_cols) else num_col
        return {
            "sql": f'SELECT MIN("{target_col}") AS min_{target_col}, MAX("{target_col}") AS max_{target_col} FROM {tbl}',
            "description": f"Min and max of {target_col}",
            "matched": True, "confidence": 3,
        }

    # 7. Show all / list ("sabhi data dikhao", "show all")
    if is_show_all:
        return {
            "sql": f"SELECT * FROM {tbl} LIMIT 100",
            "description": f"All records from {table_name}",
            "matched": True, "confidence": 3,
        }

    # 8. Filter by exact column if mentioned
    if mentioned_col:
        return {
            "sql": f'SELECT "{mentioned_col}", COUNT(*) AS count FROM {tbl} GROUP BY "{mentioned_col}" ORDER BY count DESC',
            "description": f"Distribution by {mentioned_col}",
            "matched": True, "confidence": 2,
        }

    # Default fallback
    return {
        "sql": f"SELECT * FROM {tbl} LIMIT 50",
        "description": f"First 50 records from {table_name}",
        "matched": True, "confidence": 1,
    }
