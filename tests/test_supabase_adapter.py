"""
Tests for Supabase Adapter and Dual-Engine Relational Routing.
Verifies query execution, catalog metadata, latency measurement, and fallback mechanics.
"""

import pytest
from db.supabase_adapter import DatabaseAdapter

def test_adapter_initializes_with_fallback():
    adapter = DatabaseAdapter()
    assert adapter.backend_name in ["SQLite (Local Unified)", "Supabase PostgreSQL (Cloud)"]
    assert adapter.execute_query("SELECT 1 AS test_val")["status"] == "success"

def test_adapter_execute_academic_query():
    adapter = DatabaseAdapter()
    res = adapter.execute_query("SELECT student_id, name, division FROM students LIMIT 5", input_mode="voice")
    assert res["status"] == "success"
    assert "student_id" in res["columns"]
    assert "name" in res["columns"]
    assert res["input_mode"] == "voice"
    assert res["exec_time_ms"] >= 0.0
    assert len(res["rows"]) <= 5

def test_adapter_catalog_metadata():
    adapter = DatabaseAdapter()
    catalog = adapter.get_catalog_metadata()
    assert "tables" in catalog
    assert "students" in catalog["tables"]
    assert "subjects" in catalog["tables"]
    assert "marks" in catalog["tables"]
    assert "mermaid" in catalog
    assert "erDiagram" in catalog["mermaid"]
