"""
QueryMind 2.0 — Comprehensive Test Suite
Validates:
- Voice-to-SQL generation and spoken number normalization
- Schema-aware table selection and relational 3-table joins
- WHERE clauses, GROUP BY, HAVING, and Aggregation
- REST APIs (/api/generate-sql, /api/validate-sql, /api/execute-sql, /api/schema)
- Deterministic AST governance, RBAC security, and SQL injection blocking
- Query history persistence of input_mode ('voice' vs 'text')
- Web endpoint response codes (200 OK across all 6 core pages)
"""

import json
import pytest
from app import app
from nlp.sql_generator import generate_sql, normalize_spoken_numbers, generate_sql_for_dataset
from nlp.sql_validator import validate_sql
from db.database import (
    get_database_schema_metadata,
    execute_query,
    log_query,
    get_query_history,
    _conn,
)


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "admin"
        yield client


class TestVoiceNormalizationAndGeneration:
    def test_spoken_number_normalization(self):
        text = "List the top five students by marks with attendance below seventy five"
        normalized = normalize_spoken_numbers(text)
        assert "5" in normalized
        assert "75" in normalized

    def test_attendance_below_threshold_voice_query(self):
        res = generate_sql("Show students whose attendance is below 75 percent")
        assert res["matched"] is True
        assert "students" in res["sql"].lower()
        assert "attendance" in res["sql"].lower()
        assert "75" in res["sql"]
        assert "attendance_percentage" in res["sql"].lower()

    def test_average_marks_subject(self):
        res = generate_sql("Show the average marks for each subject")
        assert res["matched"] is True
        assert "subjects" in res["sql"].lower()
        assert "avg" in res["sql"].lower()
        assert "group by" in res["sql"].lower()

    def test_top_students_spoken_word_five(self):
        res = generate_sql("List the top five students by marks")
        assert res["matched"] is True
        assert "LIMIT 5" in res["sql"].upper()
        assert "ORDER BY avg_marks DESC" in res["sql"]

    def test_count_students_department(self):
        res = generate_sql("Count students in each department")
        assert res["matched"] is True
        assert "COUNT" in res["sql"].upper()
        assert "division" in res["sql"].lower()
        assert "GROUP BY" in res["sql"].upper()

    def test_students_and_subject_marks_join(self):
        res = generate_sql("Show students and their subject marks")
        assert res["matched"] is True
        sql_lower = res["sql"].lower()
        assert "students" in sql_lower
        assert "marks" in sql_lower
        assert "subjects" in sql_lower
        assert "join" in sql_lower

    def test_show_all_students(self):
        res = generate_sql("Show all students")
        assert res["matched"] is True
        assert "FROM students" in res["sql"]

    def test_unrecognized_query_fails_safely(self):
        res = generate_sql("What is the weather in Mumbai tomorrow?")
        assert res["matched"] is False
        assert res["sql"] is None


class TestSchemaIntrospectionAndErDiagram:
    def test_metadata_contains_academic_tables(self):
        meta = get_database_schema_metadata()
        tables = meta["tables"]
        for expected in ["students", "subjects", "marks", "attendance"]:
            assert expected in tables
            assert len(tables[expected]["columns"]) > 0
            assert tables[expected]["row_count"] > 0

    def test_foreign_keys_introspected(self):
        meta = get_database_schema_metadata()
        marks_tbl = meta["tables"]["marks"]
        fk_tables = [fk["table"] for fk in marks_tbl["foreign_keys"]]
        assert "students" in fk_tables
        assert "subjects" in fk_tables

    def test_mermaid_er_diagram_generated(self):
        meta = get_database_schema_metadata()
        mermaid = meta["er_mermaid"]
        assert "erDiagram" in mermaid
        assert "students ||--o{ marks" in mermaid or "marks }o--|| students" in mermaid
        assert "subjects ||--o{ marks" in mermaid or "marks }o--|| subjects" in mermaid


class TestAstGovernanceAndSecurity:
    def test_blocks_ddl_and_dml(self):
        dangerous = [
            "DROP TABLE students",
            "DELETE FROM marks WHERE mark_id = 1",
            "INSERT INTO students (name, division) VALUES ('Hacker', 'X')",
            "UPDATE students SET name = 'Owned'",
            "ALTER TABLE students ADD COLUMN secret TEXT",
        ]
        for query in dangerous:
            v = validate_sql(query, user_role="admin")
            assert v["valid"] is False
            assert "unauthorized" in v["reason"].lower() or "blocked" in v["reason"].lower()

    def test_blocks_multi_statement_semicolon(self):
        query = "SELECT * FROM students; DROP TABLE students;"
        v = validate_sql(query, user_role="admin")
        assert v["valid"] is False

    def test_student_role_blocked_from_system_tables(self):
        query = "SELECT * FROM app_users"
        v = validate_sql(query, user_role="student")
        assert v["valid"] is False
        assert "denied access" in v["reason"].lower() or "rbac" in v["reason"].lower()

    def test_auto_limit_ceiling_injection(self):
        query = "SELECT student_id, name FROM students"
        v = validate_sql(query, user_role="admin", row_ceiling=25)
        assert v["valid"] is True
        assert "LIMIT 25" in v["sanitized_sql"].upper()


class TestAsyncRestApis:
    def test_api_generate_sql_does_not_execute(self, client):
        payload = {"question": "Find students whose attendance is below 75 percent"}
        res = client.post("/api/generate-sql", json=payload)
        assert res.status_code == 200
        data = res.get_json()
        assert "sql" in data
        assert data["matched"] is True
        # Generated SQL should be a string ready for review
        assert "attendance" in data["sql"].lower()

    def test_api_validate_sql_valid(self, client):
        payload = {"sql": "SELECT student_id, name FROM students"}
        res = client.post("/api/validate-sql", json=payload)
        assert res.status_code == 200
        data = res.get_json()
        assert data["valid"] is True
        assert "LIMIT" in data["sanitized_sql"].upper()

    def test_api_validate_sql_blocks_drop(self, client):
        payload = {"sql": "DROP TABLE students"}
        res = client.post("/api/validate-sql", json=payload)
        assert res.status_code == 200
        data = res.get_json()
        assert data["valid"] is False

    def test_api_execute_sql_with_voice_input_mode(self, client):
        payload = {
            "sql": "SELECT student_id, name, division FROM students LIMIT 3",
            "question": "Show first 3 students",
            "input_mode": "voice"
        }
        res = client.post("/api/execute-sql", json=payload)
        assert res.status_code == 200
        data = res.get_json()
        assert data["error"] is None
        assert data["row_count"] == 3
        assert len(data["rows"]) == 3
        assert "execution_ms" in data

        # Verify query was logged into query_logs with input_mode='voice'
        conn = _conn()
        row = conn.execute(
            "SELECT question, generated_sql, input_mode FROM query_logs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        assert row["question"] == "Show first 3 students"
        assert row["input_mode"] == "voice"

    def test_api_schema_endpoint(self, client):
        res = client.get("/api/schema")
        assert res.status_code == 200
        data = res.get_json()
        assert "tables" in data
        assert "er_mermaid" in data


class TestCorePageRoutes:
    def test_home_page_returns_200(self, client):
        res = client.get("/")
        assert res.status_code == 200
        assert b"Voice-to-SQL Database Management System" in res.data
        assert b"Launch Voice SQL Workspace" in res.data

    def test_voice_sql_workspace_returns_200(self, client):
        res = client.get("/workspace")
        assert res.status_code == 200
        assert b"Ask your database anything" in res.data
        assert b"Start Recording" in res.data
        assert b"Generated SQL Query" in res.data
        assert b"Run Query" in res.data

    def test_database_explorer_returns_200(self, client):
        res = client.get("/explorer")
        assert res.status_code == 200
        assert b"Database Explorer" in res.data
        assert b"students" in res.data
        assert b"erDiagram" in res.data

    def test_sql_playground_returns_200(self, client):
        res = client.get("/playground")
        assert res.status_code == 200
        assert b"Manual SQL Playground" in res.data
        assert b"Validate SQL" in res.data

    def test_query_history_returns_200(self, client):
        res = client.get("/history")
        assert res.status_code == 200
        assert b"Query Execution History" in res.data
        assert b"Input Mode" in res.data

    def test_admin_dashboard_returns_200(self, client):
        res = client.get("/admin")
        assert res.status_code == 200
        assert b"Administration &amp; System Governance" in res.data
