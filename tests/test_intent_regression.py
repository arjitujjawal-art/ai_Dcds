"""
Regression and Intent Classification Test Suite for QueryMind 2.0.
Verifies resolution of the greeting-input bug, out-of-scope non-database queries,
ambiguous utterances, unsupported DDL/DML, and schema-aware validation.
"""

import pytest
import json
from app import app
from nlp.intent_classifier import (
    classify_intent,
    DATABASE_QUERY,
    AMBIGUOUS_QUERY,
    OUT_OF_SCOPE,
    UNSUPPORTED_OPERATION,
    EMPTY_INPUT,
)

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "testuser"
            sess["role"] = "student"
        yield c

class TestIntentClassificationUnits:
    """Unit tests for the intent classifier module."""

    @pytest.mark.parametrize("greeting", [
        "hello how are you",
        "hi",
        "good morning",
        "what is your name",
        "what is your name?",
        "tell me a joke",
        "who are you",
        "how are you doing",
        "kaise ho",
        "kya hal hai"
    ])
    def test_conversational_and_greetings_classified_as_out_of_scope(self, greeting):
        res = classify_intent(greeting)
        assert res["classification"] == OUT_OF_SCOPE
        assert res["status"] == "out_of_scope"
        assert res["sql"] is None
        assert "suggestions" in res
        assert len(res["suggestions"]) >= 3

    @pytest.mark.parametrize("ambiguous", [
        "show me the data",
        "find records",
        "show data",
        "data dikhao",
        "records",
        "get everything"
    ])
    def test_ambiguous_queries_classified_as_ambiguous(self, ambiguous):
        res = classify_intent(ambiguous)
        assert res["classification"] == AMBIGUOUS_QUERY
        assert res["status"] == "ambiguous"
        assert res["sql"] is None
        assert len(res["suggestions"]) >= 2

    @pytest.mark.parametrize("destructive", [
        "delete all students",
        "drop table students",
        "truncate table marks",
        "remove students",
        "DROP TABLE students",
        "alter table students"
    ])
    def test_destructive_operations_classified_as_unsupported(self, destructive):
        res = classify_intent(destructive)
        assert res["classification"] == UNSUPPORTED_OPERATION
        assert res["status"] == "unsupported"
        assert res["sql"] is None

    @pytest.mark.parametrize("empty_val", [
        "",
        "   ",
        "???",
        "..."
    ])
    def test_empty_input_classified_as_empty(self, empty_val):
        res = classify_intent(empty_val)
        assert res["classification"] == EMPTY_INPUT
        assert res["status"] == "empty"
        assert res["sql"] is None

    @pytest.mark.parametrize("valid_q", [
        "show all students",
        "show students with attendance below 75 percent",
        "average marks by subject",
        "top five students",
        "count students in each department",
        "show students and their subject marks"
    ])
    def test_valid_database_queries_classified_as_database_query(self, valid_q):
        res = classify_intent(valid_q)
        assert res["classification"] == DATABASE_QUERY
        assert res["status"] == "valid"


class TestApiGenerateSqlRegression:
    """End-to-end REST API regression tests for /api/generate-sql."""

    def test_hello_how_are_you_returns_out_of_scope_and_no_sql(self, client):
        """CRITICAL BUG REPRODUCTION TEST: 'hello how are you' must return out_of_scope with NO SQL."""
        resp = client.post("/api/generate-sql",
                           data=json.dumps({"question": "hello how are you"}),
                           content_type="application/json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "out_of_scope"
        assert data["sql"] is None
        assert data["intent"] is None
        assert data["matched"] is False
        assert "Please ask a question about the connected database." in data["message"]
        assert len(data["suggestions"]) >= 3
        # Assert no exam_scores or arbitrary table is returned
        assert "exam_scores" not in str(data)

    def test_tell_me_a_joke_returns_out_of_scope(self, client):
        resp = client.post("/api/generate-sql",
                           data=json.dumps({"question": "tell me a joke"}),
                           content_type="application/json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "out_of_scope"
        assert data["sql"] is None

    def test_show_me_the_data_returns_ambiguous(self, client):
        resp = client.post("/api/generate-sql",
                           data=json.dumps({"question": "show me the data"}),
                           content_type="application/json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ambiguous"
        assert data["sql"] is None
        assert "ambiguous" in data["message"].lower()

    def test_delete_all_students_returns_unsupported(self, client):
        resp = client.post("/api/generate-sql",
                           data=json.dumps({"question": "delete all students"}),
                           content_type="application/json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "unsupported"
        assert data["sql"] is None
        assert "prohibited" in data["message"].lower()

    def test_valid_show_all_students_returns_sql(self, client):
        resp = client.post("/api/generate-sql",
                           data=json.dumps({"question": "show all students"}),
                           content_type="application/json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert data["sql"] is not None
        assert "SELECT" in data["sql"].upper()
        assert "students" in data["sql"].lower()

    def test_valid_attendance_below_threshold_returns_sql(self, client):
        resp = client.post("/api/generate-sql",
                           data=json.dumps({"question": "show students with attendance below 75 percent"}),
                           content_type="application/json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert "75" in data["sql"]
        assert "attendance" in data["sql"].lower()

    def test_valid_average_marks_by_subject_returns_sql(self, client):
        resp = client.post("/api/generate-sql",
                           data=json.dumps({"question": "average marks by subject"}),
                           content_type="application/json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert "AVG" in data["sql"].upper()
        assert "GROUP BY" in data["sql"].upper()


class TestFormQueryEndpointRegression:
    """Regression tests for traditional form submission route /query."""

    def test_form_query_out_of_scope_blocks_sql(self, client):
        resp = client.post("/query", data={"question": "hello how are you"}, follow_redirects=True)
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert "Please ask a question about the connected database." in html
        assert "SELECT * FROM" not in html
