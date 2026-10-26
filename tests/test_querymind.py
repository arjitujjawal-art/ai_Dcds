"""
QueryMind Test Suite
Run with: pytest tests/ -v
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from nlp.sql_generator import generate_sql
from nlp.sql_validator  import validate_sql


# ══════════════════════════════════════════════════════
# NLP / SQL Generator Tests
# ══════════════════════════════════════════════════════

class TestSqlGenerator:

    def test_top_students(self):
        r = generate_sql("Show me the top 5 students with the highest average marks")
        assert r["matched"] is True
        assert "AVG" in r["sql"]
        assert "ORDER BY" in r["sql"]
        assert "LIMIT 5" in r["sql"]

    def test_top_students_custom_n(self):
        r = generate_sql("top 10 students by average marks")
        assert r["matched"] is True
        assert "LIMIT 10" in r["sql"]

    def test_average_attendance_division(self):
        r = generate_sql("What is the average attendance of each division?")
        assert r["matched"] is True
        assert "attendance" in r["sql"].lower()
        assert "GROUP BY" in r["sql"]

    def test_subjects_below_threshold(self):
        r = generate_sql("Which subjects have an average score below 60?")
        assert r["matched"] is True
        assert "60" in r["sql"]
        assert "HAVING" in r["sql"]

    def test_count_above_threshold(self):
        r = generate_sql("How many students scored above 80 in each subject?")
        assert r["matched"] is True
        assert "COUNT" in r["sql"]
        assert "80" in r["sql"]

    def test_low_attendance_students(self):
        r = generate_sql("Show students with attendance below 75%")
        assert r["matched"] is True
        assert "attendance" in r["sql"].lower()
        assert "75" in r["sql"]

    def test_compare_divisions(self):
        r = generate_sql("Compare average marks across divisions")
        assert r["matched"] is True
        assert "division" in r["sql"].lower()

    def test_all_students(self):
        r = generate_sql("Show all students")
        assert r["matched"] is True
        assert "FROM students" in r["sql"]

    def test_unrecognised_question(self):
        r = generate_sql("What is the weather like today?")
        assert r["matched"] is False
        assert r["sql"] is None

    def test_min_max_marks(self):
        r = generate_sql("Show min and max marks per subject")
        assert r["matched"] is True
        assert "MIN" in r["sql"] and "MAX" in r["sql"]


# ══════════════════════════════════════════════════════
# SQL Validator Tests
# ══════════════════════════════════════════════════════

class TestSqlValidator:

    def test_valid_select(self):
        sql = "SELECT name, division FROM students ORDER BY name"
        r = validate_sql(sql)
        assert r["valid"] is True

    def test_blocks_drop(self):
        sql = "DROP TABLE students"
        r = validate_sql(sql)
        assert r["valid"] is False

    def test_blocks_insert(self):
        sql = "INSERT INTO students (name) VALUES ('hacker')"
        r = validate_sql(sql)
        assert r["valid"] is False

    def test_blocks_delete(self):
        sql = "DELETE FROM students WHERE 1=1"
        r = validate_sql(sql)
        assert r["valid"] is False

    def test_blocks_comment_injection(self):
        sql = "SELECT * FROM students -- DROP TABLE students"
        r = validate_sql(sql)
        assert r["valid"] is False

    def test_blocks_semicolon_injection(self):
        sql = "SELECT * FROM students; DROP TABLE marks"
        r = validate_sql(sql)
        assert r["valid"] is False

    def test_blocks_password_hash(self):
        sql = "SELECT username, password_hash FROM app_users"
        r = validate_sql(sql, user_role="student")
        assert r["valid"] is False

    def test_blocks_app_users_for_student(self):
        sql = "SELECT username FROM app_users"
        r = validate_sql(sql, user_role="student")
        assert r["valid"] is False

    def test_allows_app_users_for_admin(self):
        sql = "SELECT user_id, username, role FROM app_users"
        r = validate_sql(sql, user_role="admin")
        # Only blocked by password_hash column, which isn't in this query
        assert r["valid"] is True

    def test_empty_query(self):
        r = validate_sql("")
        assert r["valid"] is False

    def test_group_by_valid(self):
        sql = (
            "SELECT division, COUNT(*) AS cnt FROM students "
            "GROUP BY division ORDER BY cnt DESC"
        )
        r = validate_sql(sql)
        assert r["valid"] is True

    def test_join_valid(self):
        sql = (
            "SELECT s.name, AVG(m.marks) AS avg_m "
            "FROM students s JOIN marks m ON s.student_id = m.student_id "
            "GROUP BY s.name ORDER BY avg_m DESC LIMIT 5"
        )
        r = validate_sql(sql)
        assert r["valid"] is True
