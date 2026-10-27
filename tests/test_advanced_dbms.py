"""
Tests for QueryMind 2.0 Advanced DBMS Features:
- Query Execution Plan Analyzer (EXPLAIN QUERY PLAN)
- Index Inspection and B-Tree Sort Detection
- Table Access Profiling
- /api/explain-sql Endpoint Verification
"""

import pytest
import json
from app import app
from db.database import explain_query_plan

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "admin"
        yield c

class TestQueryPlanExplainer:
    def test_explain_simple_scan(self):
        sql = "SELECT student_id, name FROM students LIMIT 10"
        plan = explain_query_plan(sql)
        assert plan["status"] == "success"
        assert len(plan["steps"]) >= 1
        assert "students" in plan["summary"]["tables_accessed"]
        assert plan["summary"]["step_count"] >= 1

    def test_explain_join_and_sort(self):
        sql = """
        SELECT s.name, m.marks
        FROM students s
        JOIN marks m ON s.student_id = m.student_id
        ORDER BY m.marks DESC
        LIMIT 5
        """
        plan = explain_query_plan(sql)
        assert plan["status"] == "success"
        assert "students" in plan["summary"]["tables_accessed"]
        assert "marks" in plan["summary"]["tables_accessed"]
        assert plan["summary"]["step_count"] >= 2
        # Verify optimization summary is populated
        assert "optimization_level" in plan["summary"]

    def test_explain_syntax_error_handled(self):
        sql = "SELECT * FROM non_existent_table_xyz_123"
        plan = explain_query_plan(sql)
        assert plan["status"] == "error"
        assert plan["error"] is not None

class TestApiExplainEndpoint:
    def test_api_explain_valid_query(self, client):
        payload = {"sql": "SELECT student_id, name, division FROM students"}
        resp = client.post("/api/explain-sql",
                           data=json.dumps(payload),
                           content_type="application/json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert len(data["steps"]) >= 1
        assert "students" in data["summary"]["tables_accessed"]

    def test_api_explain_blocks_injection(self, client):
        payload = {"sql": "SELECT * FROM students; DROP TABLE students;"}
        resp = client.post("/api/explain-sql",
                           data=json.dumps(payload),
                           content_type="application/json")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["valid"] is False

    def test_api_explain_empty_sql_rejected(self, client):
        resp = client.post("/api/explain-sql",
                           data=json.dumps({"sql": ""}),
                           content_type="application/json")
        assert resp.status_code == 400


class TestDatabaseMigration:
    def test_sqlite_to_supabase_migration_generator(self, tmp_path):
        from scripts.migrate_sqlite_to_supabase import generate_supabase_seed_script
        out_sql = str(tmp_path / "test_seed.sql")
        content = generate_supabase_seed_script(output_path=out_sql)
        assert "BEGIN;" in content
        assert "INSERT INTO public.subjects" in content
        assert "INSERT INTO public.students" in content
        assert "INSERT INTO public.marks" in content
        assert "INSERT INTO public.attendance" in content
        assert "setval" in content
        assert "COMMIT;" in content
