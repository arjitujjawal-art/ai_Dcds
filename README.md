# QueryMind 2.0 — Voice-Enabled Relational Database Management System

[![Pytest Tests](https://img.shields.io/badge/pytest-101%2F101%20passing-brightgreen.svg)](tests/)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Database Engines](https://img.shields.io/badge/database-SQLite%20(WAL)%20%7C%20Supabase%20Postgres-purple.svg)](db/)
[![Security Governance](https://img.shields.io/badge/security-SQLGlot%20AST%20%7C%20PostgreSQL%20RLS-orange.svg)](nlp/sql_validator.py)
[![Academic Project](https://img.shields.io/badge/course-DCDS%20ESE%20Project-navy.svg)](QueryMind_2_Final_Implementation_Report.pdf)

> **A deterministic, schema-governed Voice-to-SQL system built upon Relational Database Engineering, 5-State Intent Classification, Mathematical AST Security Governance, Dual-Engine RDBMS (Cloud Supabase PostgreSQL + Local SQLite), and Live Execution Plan Profiling.**

---

## 📑 Project Deliverables & Academic Documentation

| Deliverable Document | Format | Description & Scope | File Link |
| :--- | :---: | :--- | :--- |
| **Comprehensive Academic Report** | `PDF` | **Exact 30-Page Dossier**: Chapters 1–18, 3NF Normalization Proofs, AST Security Invariants, Defect Autopsy, 99-Test Execution Logs, DDL Specs. | [Download PDF](QueryMind_2_Final_Implementation_Report.pdf) |
| **Editable Technical Report** | `DOCX` | Complete academic Word document with structured headings, tables, callout blocks, and IEEE citations. | [Download DOCX](QueryMind_2_Final_Implementation_Report.docx) |
| **Presentation Slides** | `PPTX` | **13-Slide DCDS ESE Project Presentation** formatted to official departmental presentation standards. | [Download PPTX](QueryMind_2_DCDS_ESE_Presentation.pptx) |
| **Printable Web Report** | `HTML` | Standalone publication-grade HTML report with A4 print styling and responsive CSS. | [View HTML](QueryMind_2_Final_Implementation_Report.html) |

---

## 🏛️ Central DBMS Academic Concepts (DCDS Curriculum)

While voice recognition serves as the ergonomic input modality, the core engineering of QueryMind 2.0 demonstrates fundamental **Data Communication & Database Systems (DCDS)** principles:

| DBMS Pillar | Implementation in QueryMind 2.0 |
| :--- | :--- |
| **Relational Database Modeling** | Normalized schemas (`students`, `subjects`, `marks`, `attendance`, `app_users`) with primary and foreign key constraints. |
| **3NF Normalization Analysis** | Formal functional dependency proofs eliminating insertion, update, and deletion anomalies ($1\text{NF} \to 2\text{NF} \to 3\text{NF}$). |
| **Live Mermaid ER Modeling** | Dynamic ER diagram compiled from live catalog tables (`PRAGMA foreign_key_list` and `pg_constraint`), showing $1:N$ cardinalities. |
| **Relational SQL Algebra** | Multi-table relational joins (`students` $\bowtie$ `marks` $\bowtie$ `subjects`), `GROUP BY`, `HAVING` threshold filters, and aggregations (`AVG`, `COUNT`, `MAX`, `MIN`). |
| **Intent-Aware Query Gating** | 5-state Intent Classifier (`DATABASE_QUERY`, `AMBIGUOUS_QUERY`, `OUT_OF_SCOPE`, `UNSUPPORTED_OPERATION`, `EMPTY_INPUT`) halting non-database speech before SQL synthesis. |
| **Mathematical AST Governance** | In-memory syntax tree parsing via `SQLGlot` enforcing a read-only `SELECT` whitelist, blocking DDL/DML, and injecting defensive `LIMIT 100` ceilings. |
| **Dual-Engine Architecture** | Unified `DatabaseAdapter` supporting cloud-hosted **Supabase PostgreSQL 15+** and local zero-configuration **SQLite (WAL mode)** with automated failover. |
| **PostgreSQL Row-Level Security (RLS)** | Multi-tenant isolation at the database kernel level; students can only inspect their personal scores via `auth.uid()` policies. |
| **Execution Plan Profiling** | Interactive `EXPLAIN QUERY PLAN` analyzer categorizing optimizer steps into `FULL_TABLE_SCAN`, `INDEX_SEARCH` (B-Trees), and `TEMP_BTREE_SORT`. |
| **Audit & Telemetry Logs** | Append-only query history recording username, input mode (`voice` vs `text`), synthesized SQL, execution latency (ms), and row counts. |

---

## 🔍 Critical Bug Autopsy & Resolution: The Greeting-Input Defect

### 1. The Defect Manifestation
In previous iterations, speaking non-database conversational greetings (e.g., *"hello how are you"*) caused the system to:
1. Synthesize an unrelated database query: `SELECT * FROM "exam_scores" LIMIT 50`.
2. Display misleading green success badges: *"SQL generated successfully"* and *"AST Validated • Read-Only SELECT • Safe"*.

### 2. Root Cause Analysis
- **Root Cause 1 (Arbitrary Fallback):** In `nlp/sql_generator.py` (line 402), `generate_sql_for_dataset()` had an unconditional fallback returning `SELECT * FROM "{table_name}" LIMIT 50` whenever no keyword patterns matched.
- **Root Cause 2 (Missing Intent Gating):** The API gateway dispatched all speech transcripts directly to SQL pattern matching without verifying whether the utterance was a database inquiry.
- **Root Cause 3 (UI Stale State):** In `static/js/voice_sql.js`, unmatched inputs did not clear `#sqlEditor`, leaving previous queries active and executable.

### 3. The Implemented Fix
- **Engineered `nlp/intent_classifier.py`:** Enforces 5 canonical intent states. Non-database utterances immediately return structured payloads with `status: "out_of_scope"` and helpful suggestions:
  ```json
  {
    "classification": "OUT_OF_SCOPE",
    "status": "out_of_scope",
    "intent": null,
    "sql": null,
    "message": "Please ask a question about the connected database.",
    "suggestions": [
      "Show all students",
      "Find students with attendance below 75%",
      "Show average marks by subject"
    ]
  }
  ```
- **Excised Arbitrary Fallbacks:** Unmatched queries in `nlp/sql_generator.py` strictly return `matched: False, sql: None`.
- **UI State Clearing:** `static/js/voice_sql.js` clears `#sqlEditor`, hides AST badges, collapses the explain drawer, and presents suggestion chips.
- **Automated Regression Verification:** 40 regression tests in `tests/test_intent_regression.py` verify that greetings, jokes, ambiguous inputs, and destructive commands generate zero SQL.

---

## 🎙️ The Voice-to-SQL Pipeline Lifecycle

```
[User Speaks Natural Language]
             │
             ▼
[Web Speech API: Audio Waveform Capture]
             │
             ▼
[Spoken Normalization: "seventy five percent" ──► "75%"]
             │
             ▼
[Intent Classification Engine: 5 Canonical States]
      ├── OUT_OF_SCOPE / AMBIGUOUS / UNSUPPORTED ──► [Immediate Structured Guidance & Halt]
      └── DATABASE_QUERY (Approved)
             │
             ▼
[Schema Mapping: Slot Filling & Join Assembly]
             │
             ▼
[SQLGlot AST Validation: Read-Only Check & Auto LIMIT 100]
             │
             ▼
[Workspace UI Review: User Reviews SQL in #sqlEditor]  <── Microphone stop NEVER auto-executes!
             │
             ▼ (User Explicitly Clicks [Run Query])
[Database Adapter: Supabase PostgreSQL 15+ / SQLite WAL]
             │
             ▼
[Execution Plan Profiler: EXPLAIN Tree + Results Table + Charts]
```

---

## 🧭 Application Workspaces & Portals

QueryMind 2.0 provides six specialized interfaces accessible from any browser:

1. **Voice SQL Workspace (`/voice-sql` or `/workspace`)**: Real-time microphone capture with audio waveform visualization, transcript editor, distinct badge indicators (Speech Recognized, Intent Validated, AST Validated), execution button, interactive results table, and `[Explain Plan]` drawer.
2. **Database Schema Explorer (`/database-explorer` or `/explorer`)**: Live schema catalog displaying table structures, column datatypes, nullability, primary/foreign keys, and an interactive **Mermaid.js Entity-Relationship diagram**.
3. **SQL Playground (`/sql-playground` or `/playground`)**: Direct SQL workbench for writing manual relational queries, featuring AST security validation, execution latency profiling, and CSV export.
4. **Query History (`/query-history` or `/history`)**: Complete audit trail with input mode tagging (🎙️ Voice vs ⌨️ Text), query status, latency timers, row counts, and one-click re-run buttons.
5. **Admin Governance Portal (`/admin-dashboard` or `/admin`)**: Command center displaying system metrics, user role management (Student, Faculty, Admin), dataset upload with dynamic table creation, and security audit logs.
6. **Academic Home Portal (`/`)**: Architecture diagrams, DCDS curriculum relevance, database statistics, and quick-launch links.

---

## 🧪 Automated Testing Suite (99 / 99 Tests Passing)

QueryMind 2.0 enforces a continuous automated test suite run via `pytest tests/ -v`:

```bash
pytest tests/ -v
```

### Test Suite Execution Matrix (100% Pass Rate in 3.99s)

| Test Module | Test Coverage & Scope | Tests Passed | Status |
| :--- | :--- | :---: | :---: |
| `tests/test_intent_regression.py` | Greeting bug fix, out-of-scope blocking, destructive query rejection, live API regression | **40 / 40** | ✅ PASSED |
| `tests/test_querymind.py` | Core SQL template mapping, SQLGlot AST validation rules, CSV dataset queries | **22 / 22** | ✅ PASSED |
| `tests/test_querymind_2.py` | Spoken number normalization, schema introspection catalog, Mermaid ER compilation, page routes | **27 / 27** | ✅ PASSED |
| `tests/test_advanced_dbms.py` | Query plan analysis (`EXPLAIN QUERY PLAN`), table scan and index search detection | **3 / 3** | ✅ PASSED |
| `tests/test_supabase_adapter.py` | Dual-engine database adapter initialization, local SQLite fallback, catalog metadata | **7 / 7** | ✅ PASSED |
| **TOTAL AGGREGATE** | **Complete System Verification** | **99 / 99** | **✅ 100% PASS** |

---

## 🚀 Installation & Local Execution

### 1. Prerequisites
- Python 3.11+
- Chromium-based browser (Google Chrome, Microsoft Edge, Safari) with microphone support

### 2. Setup
```bash
# Clone the repository
git clone https://github.com/arjitujjawal-art/ai_Dcds.git
cd ai_Dcds

# Switch to QueryMind 2.0 branch
git checkout querymind-2.0

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Automated Tests
```bash
pytest tests/ -v
```

### 4. Start the Application
```bash
python app.py
```

Open your browser to:
**`http://127.0.0.1:5000`**

### Default Academic Credentials
- **Student User:** `student1` / `stud123` (Role: `student`)
- **Faculty User:** `teacher1` / `teach123` (Role: `teacher`)
- **Administrator:** `admin` / `admin123` (Role: `admin`)

---

## ☁️ Supabase Cloud PostgreSQL Integration (Optional)

To connect QueryMind 2.0 to your cloud Supabase instance:
```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-anon-or-service-key"
export DATABASE_URL="postgresql://postgres:password@db.your-project.supabase.co:5432/postgres"
```

### Running Schema & Data Migrations:
```bash
# Generate idempotent PostgreSQL 15+ seed script from SQLite records
python scripts/migrate_sqlite_to_supabase.py

# Execute migrations in Supabase SQL Editor:
# 1. migrations/001_initial_supabase_postgres_schema.sql (Tables, Indexes, RLS Policies)
# 2. migrations/002_data_seed_supabase.sql (Relational Data Seed)
```

If Supabase credentials are not provided, QueryMind 2.0 automatically runs on its local, zero-configuration SQLite engine in WAL mode.

---

## 🚀 Production Deployment Guide

QueryMind 2.0 is fully containerized and production-ready for deployment across any cloud provider or bare-metal environment.

### Option 1: Docker / Container Deployment (Recommended)
Build and run with a single command:
```bash
# Using Docker Compose:
docker-compose up -d --build

# Or using plain Docker:
docker build -t querymind-2 .
docker run -d -p 5000:5000 --name querymind querymind-2
```
Test health check:
```bash
curl http://localhost:5000/health
# Returns: {"status": "healthy", "service": "QueryMind 2.0 DBMS", "database": "sqlite_ready"}
```

### Option 2: 1-Click Cloud Deployment (Render / Railway / Heroku)
- **Render.com:** Connect your GitHub repository. Render automatically detects [`render.yaml`](render.yaml) and [`Procfile`](Procfile), building with Python 3.11 and launching with Gunicorn WSGI.
- **Railway.app / Heroku:** Connect repo, configure environment variables from [`.env.example`](.env.example), and deploy.

### Option 3: Standard Production WSGI Server (Linux / VPS)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run with Gunicorn (multi-threaded production WSGI)
gunicorn --workers 2 --threads 4 --timeout 120 wsgi:app --bind 0.0.0.0:5000
```

### Option 4: Production on Windows (Waitress)
```bash
pip install waitress
waitress-serve --port=5000 wsgi:app
```

---

## 👥 Contributors & Academic Credits

- **Course:** Data Communication & Database Systems (DCDS) — ESE Project (2025–2026)
- **Repository:** [`https://github.com/arjitujjawal-art/ai_Dcds`](https://github.com/arjitujjawal-art/ai_Dcds)
- **Branch:** `querymind-2.0`
- **Lead Systems Architect & QA Lead:** Systems Development Team
