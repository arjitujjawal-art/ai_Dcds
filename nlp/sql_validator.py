"""
QueryMind SQL Validator
Ensures only safe, read-only queries are executed against SQLite.
"""

import re

try:
    import sqlglot
    HAS_SQLGLOT = True
except ImportError:
    HAS_SQLGLOT = False

BLOCKED_KEYWORDS = {
    "INSERT","UPDATE","DELETE","DROP","CREATE","ALTER","TRUNCATE",
    "REPLACE","GRANT","REVOKE","EXEC","EXECUTE","CALL","ATTACH",
    "DETACH","PRAGMA",
}

ALLOWED_TABLES   = {"students","subjects","marks","attendance"}
ADMIN_TABLES     = {"app_users"}
FORBIDDEN_COLS   = {"password_hash","password","secret","token"}


def validate_sql(sql: str, user_role: str = "student") -> dict:
    if not sql or not sql.strip():
        return {"valid": False, "reason": "Empty query."}

    sql_upper = sql.upper().strip()

    # Must start with SELECT
    if not sql_upper.startswith("SELECT"):
        return {"valid": False, "reason": "Only SELECT queries are permitted."}

    # Block dangerous keywords
    tokens = set(re.findall(r"\b[A-Z_]+\b", sql_upper))
    bad = BLOCKED_KEYWORDS & tokens
    if bad:
        return {"valid": False, "reason": f"Disallowed keyword(s): {', '.join(sorted(bad))}."}

    # No multiple statements
    if ";" in sql.strip().rstrip(";"):
        return {"valid": False, "reason": "Multiple statements are not allowed."}

    # No comment injection
    if "--" in sql or "/*" in sql or "*/" in sql:
        return {"valid": False, "reason": "SQL comments are not allowed."}

    # Parse with sqlglot if available
    if HAS_SQLGLOT:
        try:
            parsed = sqlglot.parse_one(sql, dialect="sqlite")
            if parsed is None:
                return {"valid": False, "reason": "SQL could not be parsed."}
        except Exception as exc:
            return {"valid": False, "reason": f"SQL parse error: {exc}"}

    # Table / column checks
    ids_lower = set(t.lower() for t in re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", sql))

    if user_role not in ("admin", "teacher"):
        blocked_tbls = ADMIN_TABLES & ids_lower
        if blocked_tbls:
            return {"valid": False, "reason": f"Access to {', '.join(blocked_tbls)} is restricted."}

    bad_cols = FORBIDDEN_COLS & ids_lower
    if bad_cols:
        return {"valid": False, "reason": f"Column(s) {', '.join(bad_cols)} not accessible."}

    return {"valid": True, "reason": "OK"}
