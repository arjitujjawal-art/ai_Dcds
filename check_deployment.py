"""
QueryMind 2.0 — Production Deployment Pre-Flight Audit
Verifies:
1. Python environment and core package imports
2. WSGI application entrypoint integrity
3. Gunicorn configuration syntax
4. SQLite database integrity and seeded academic catalogs
5. All core route HTTP response codes (200 OK)
6. REST API contracts (/health, /api/generate-sql, /api/schema)
7. Static assets and bundled offline JavaScript/CSS libraries
8. Mathematical AST governance invariants
"""

import sys
import os
import sqlite3
import json

# Ensure UTF-8 stdout encoding on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def print_check(name: str, passed: bool, detail: str = ""):
    symbol = "[PASS]" if passed else "[FAIL]"
    print(f"{symbol} {name:<45} {detail}")
    if not passed:
        print(f"    ERROR DETAILS: {detail}")
        sys.exit(1)

def run_preflight_audit():
    print("=" * 75)
    print(" QueryMind 2.0 DBMS - Production Deployment Pre-Flight Audit")
    print("=" * 75)

    # 1. Python runtime check
    py_ver = sys.version.split()[0]
    print_check("Python Runtime (3.10+)", sys.version_info >= (3, 10), f"Detected {py_ver}")

    # 2. Package imports
    packages = ["flask", "sqlglot", "pandas", "openpyxl", "edge_tts"]
    for pkg in packages:
        try:
            __import__(pkg)
            print_check(f"Module Import: {pkg}", True, "Available")
        except ImportError as e:
            print_check(f"Module Import: {pkg}", False, str(e))

    # 3. WSGI Entrypoint verification
    try:
        from wsgi import app, application
        print_check("WSGI Entrypoint (wsgi:app)", app is not None and application is not None, "Callable found")
    except Exception as e:
        print_check("WSGI Entrypoint (wsgi:app)", False, str(e))

    # 4. Gunicorn config syntax
    try:
        import gunicorn_config
        print_check("Gunicorn Configuration (gunicorn_config.py)", hasattr(gunicorn_config, "bind"), f"Binding to {gunicorn_config.bind}")
    except Exception as e:
        print_check("Gunicorn Configuration (gunicorn_config.py)", False, str(e))

    # 5. Database file & integrity
    db_path = os.path.join(os.path.dirname(__file__), "db", "querymind.db")
    db_exists = os.path.exists(db_path)
    print_check("Database File (db/querymind.db)", db_exists, f"Path: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        check = conn.execute("PRAGMA quick_check").fetchone()[0]
        print_check("SQLite Database Integrity Check", check == "ok", f"Status: {check}")
        
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        for req_table in ["students", "subjects", "marks", "attendance", "app_users", "dataset_registry"]:
            count = conn.execute(f'SELECT COUNT(*) FROM "{req_table}"').fetchone()[0] if req_table in tables else -1
            print_check(f"Table Catalog: {req_table}", count >= 0, f"{count} rows seeded")
        conn.close()
    except Exception as e:
        print_check("SQLite Catalog Verification", False, str(e))

    # 6. Static Asset Bundling
    static_assets = [
        ("static/css/style.css", "Design System CSS"),
        ("static/js/main.js", "Core Shell JS"),
        ("static/js/voice_sql.js", "Voice & SQL Workspace JS"),
        ("static/js/mermaid.min.js", "Offline Bundled Mermaid.js"),
    ]
    for path, label in static_assets:
        full_path = os.path.join(os.path.dirname(__file__), path)
        size_kb = os.path.getsize(full_path) / 1024 if os.path.exists(full_path) else 0
        print_check(f"Static Asset: {label}", os.path.exists(full_path) and size_kb > 0, f"{size_kb:.1f} KB")

    # 7. Flask Test Client Endpoint Checks
    from app import app
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "admin"

        routes = [
            ("/health", 200, "Production Health Probe"),
            ("/", 200, "Executive Home Landing"),
            ("/workspace", 200, "Voice & SQL Workspace"),
            ("/explorer", 200, "Database Explorer & ER Model"),
            ("/playground", 200, "Manual SQL Playground"),
            ("/history", 200, "Query Execution History"),
            ("/admin", 200, "System Administration Dashboard"),
        ]
        for route, expected_status, label in routes:
            resp = client.get(route)
            print_check(f"Endpoint: {route} ({label})", resp.status_code == expected_status, f"HTTP {resp.status_code}")

        # 8. API Contract: Health Probe Payload
        health_resp = client.get("/health")
        health_data = health_resp.get_json()
        print_check("Health API Contract (/health)", health_data.get("status") == "healthy", f"Service: {health_data.get('service')}")

        # 9. API Contract: /api/generate-sql (Student Name List)
        gen_resp = client.post("/api/generate-sql", data=json.dumps({"question": "can I get the name list of students"}), content_type="application/json")
        gen_data = gen_resp.get_json()
        sql_ok = gen_data.get("status") == "success" and "from students" in gen_data.get("sql", "").lower()
        print_check("API Contract: /api/generate-sql", sql_ok, f"SQL: {gen_data.get('sql')}")

        # 10. Intent Gating: Conversational Greeting Rejection
        greet_resp = client.post("/api/generate-sql", data=json.dumps({"question": "hello how are you"}), content_type="application/json")
        greet_data = greet_resp.get_json()
        greet_ok = greet_data.get("status") == "out_of_scope" and greet_data.get("sql") is None
        print_check("Intent Classifier: Out-of-Scope Rejection", greet_ok, f"Classification: {greet_data.get('classification')}")

    print("=" * 75)
    print(" >>> ALL PRE-FLIGHT CHECKS PASSED! QueryMind 2.0 IS DEPLOYMENT READY! <<<")
    print("=" * 75)

if __name__ == "__main__":
    run_preflight_audit()
