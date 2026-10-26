"""
QueryMind MySQL Client
Handles all interactions with the MySQL academic database.
"""

import time
import pymysql
from flask import current_app


def get_connection():
    """Create and return a new MySQL connection using app config."""
    cfg = current_app.config
    return pymysql.connect(
        host=cfg["MYSQL_HOST"],
        port=int(cfg.get("MYSQL_PORT", 3306)),
        user=cfg["MYSQL_USER"],
        password=cfg["MYSQL_PASSWORD"],
        database=cfg["MYSQL_DB"],
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5,
        autocommit=True,
    )


def execute_query(sql: str, max_rows: int = 500):
    """
    Execute a validated, read-only SQL query.

    Returns:
        {
            "rows":          list[dict],
            "columns":       list[str],
            "row_count":     int,
            "execution_ms":  int,
            "error":         str | None,
        }
    """
    start = time.monotonic()
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchmany(max_rows)
            columns = [d[0] for d in cur.description] if cur.description else []
        conn.close()
        elapsed = int((time.monotonic() - start) * 1000)
        return {
            "rows": rows,
            "columns": columns,
            "row_count": len(rows),
            "execution_ms": elapsed,
            "error": None,
        }
    except pymysql.MySQLError as exc:
        elapsed = int((time.monotonic() - start) * 1000)
        return {
            "rows": [],
            "columns": [],
            "row_count": 0,
            "execution_ms": elapsed,
            "error": f"Database error: {exc.args[1] if len(exc.args) > 1 else str(exc)}",
        }
    except Exception as exc:
        elapsed = int((time.monotonic() - start) * 1000)
        return {
            "rows": [],
            "columns": [],
            "row_count": 0,
            "execution_ms": elapsed,
            "error": f"Unexpected error: {str(exc)}",
        }


def test_connection():
    """Return True if MySQL is reachable, False otherwise."""
    try:
        conn = get_connection()
        conn.close()
        return True
    except Exception:
        return False
