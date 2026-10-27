# QueryMind 2.0 — Voice-to-SQL Relational Database Management System

> **A Voice-Enabled Natural Language to SQL Query System built upon Relational Database Engineering, Deterministic AST Security Governance, and Live Schema Introspection.**

QueryMind 2.0 transforms spoken or typed natural language questions into relational SQL queries, displays them in an editable panel for user inspection, enforces Abstract Syntax Tree (AST) validation, executes authorized queries against a normalized SQLite academic database, and renders matching records with interactive tabular and visual views.

---

## 🏛️ Central DBMS Academic Concepts

While voice recognition serves as the ergonomic input layer, the technical core of the project demonstrates fundamental **Database Management System (DBMS)** principles:

| DBMS Pillar | Implementation in QueryMind 2.0 |
|---|---|
| **Relational Database** | Normalized schemas (`students`, `subjects`, `marks`, `attendance`) with strict primary and foreign key constraints. |
| **Entity-Relationship (ER) Modeling** | Live ER diagram dynamically generated from SQLite schema catalogs (`PRAGMA foreign_key_list`), showcasing 1:N cardinality connectors. |
| **Relational SQL Algebra** | Multi-table INNER/LEFT `JOIN`, `GROUP BY`, `HAVING` filtering, aggregations (`AVG`, `COUNT`, `SUM`, `MIN`, `MAX`), and `ORDER BY`. |
| **Deterministic Query Processing** | Speech-to-text conversion &rarr; tokenization & normalization &rarr; schema-aware template mapping &rarr; generated SQL panel for inspection &rarr; execution. |
| **AST Security Governance** | In-memory Abstract Syntax Tree validation via `sqlglot` guaranteeing single `SELECT` expressions, blocking DDL/DML (`DROP`, `INSERT`, `DELETE`, `UPDATE`), and injecting deterministic `LIMIT 50` row ceilings. |
| **Role-Based Access Control (RBAC)** | Entitlements partitioned across Student, Faculty, and Admin personas; unauthorized system tables (`app_users`) and sensitive credentials (`password_hash`) are blocked. |
| **Schema Introspection** | Interactive table explorer displaying datatypes, nullability, default values, foreign key targets, row counts, and sample record previews. |
| **Audit & Telemetry Logs** | Query history recording user identity, natural question, generated SQL, execution status, latency (ms), row count, and input method (`voice` vs `text`). |

---

## 🧭 Application Structure (6 Core Areas)

The redesigned web interface features six specialized workspaces:

1. **Home (`/`)**: Academic DBMS overview, interactive processing pipeline flow, live database statistics, and direct "Launch Workspace" actions.
2. **Voice SQL Workspace (`/workspace` or `/voice-sql`)**: The flagship workspace featuring real-time speech-to-text recording, editable recognized question textarea, syntax-highlighted generated SQL panel, `[Validate SQL]` AST button, `[Run Query]` execution button, and interactive results table with Chart.js visualization.
3. **Database Explorer (`/explorer`)**: Dynamic schema catalog and live Mermaid.js ER diagram mapping table definitions, column types, primary keys, foreign keys, and 5-row live sample previews.
4. **SQL Playground (`/playground`)**: Manual SQL editor for custom relational queries with pre-filled academic presets, AST validation checks, execution latency tracking, and CSV export.
5. **Query History (`/history`)**: Persistent audit log with input mode filtering (🎙️ Voice vs ⌨️ Text), execution status, latency, row counts, and instant "Load in Workspace" re-run actions.
6. **Admin Dashboard (`/admin`)**: Governance command center featuring user account inspection, role entitlements matrix, dataset upload with automatic SQLite table creation, and security audit logs.

---

## 🎙️ The Voice-to-SQL User Journey

```text
User Speaks Question
        │
        ▼
Speech-to-Text Ingestion (Web Speech API with live audio wave pulse)
        │
        ▼
Spoken-Number Normalization ("five" -> 5, "seventy five" -> 75)
        │
        ▼
Schema-Aware SQL Generation (Matches relational academic templates)
        │
        ▼
Generated SQL Displayed in Editable Code Panel
        │
        ▼
User Reviews, Inspects, or Edits SQL
        │
        ▼
[Validate SQL] AST Check (sqlglot AST parse, SELECT-only verification, auto LIMIT injection)
        │
        ▼
[Run Query] Execution against SQLite Engine
        │
        ▼
Results Displayed (Sub-millisecond latency, row counts, data table, Chart.js, optional TTS summary)
        │
        ▼
Persistence in Query History (Tagged with input_mode='voice')
```

> **Important**: The microphone captures speech as an input mechanism. The system does **not** automatically execute queries upon speech capture; the user retains full control to inspect, edit, or validate the SQL before clicking `[Run Query]`.

---

## 🚀 Installation & Execution

### 1. Prerequisites
- Python 3.10+
- Modern browser with Web Speech API support (Google Chrome, Microsoft Edge, Safari)

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

### 3. Run Application
```bash
python app.py
```

The SQLite database (`db/querymind.db`) self-initializes and seeds academic records on first startup.

Open your browser to:
**http://127.0.0.1:5000**

---

## 🧪 Automated Testing

Run the full automated test suite:

```bash
pytest tests/ -v
```

All 49 unit, integration, security, and web endpoint tests verify:
- Voice input normalization (e.g. converting spoken words like "five" to numeric digits)
- Academic query templates (attendance threshold filter, subject averages, 3-table joins, division counts)
- Schema metadata introspection and dynamic Mermaid ER diagram generation
- AST security governance blocking `DROP`, `DELETE`, `INSERT`, `UPDATE`, comments, and semicolon injections
- Role-based table and column masking (blocking `app_users` and `password_hash` for students)
- Asynchronous REST endpoints (`/api/generate-sql`, `/api/validate-sql`, `/api/execute-sql`, `/api/schema`)
- Query history persistence of `input_mode` (`voice` vs `text`)
- HTTP 200 OK responses across all 6 core page routes

---

## 📊 Sample Academic Queries to Test

| User Speech / Text | Generated SQL Query | Key DBMS Concepts |
|---|---|---|
| *"Show students whose attendance is below 75 percent"* | `SELECT s.student_id, s.name, s.division, ROUND(AVG(a.attendance_percentage), 2) AS attendance_percentage FROM students s JOIN attendance a ON s.student_id = a.student_id GROUP BY s.student_id, s.name, s.division HAVING attendance_percentage < 75 ORDER BY attendance_percentage;` | INNER JOIN, GROUP BY, HAVING, Threshold Filtering |
| *"Show the average marks for each subject"* | `SELECT sub.subject_name, ROUND(AVG(m.marks), 2) AS avg_marks FROM subjects sub JOIN marks m ON sub.subject_id = m.subject_id GROUP BY sub.subject_name ORDER BY avg_marks DESC;` | Aggregation (`AVG`), GROUP BY, ORDER BY DESC |
| *"List the top five students by marks"* | `SELECT s.student_id, s.name, s.division, ROUND(AVG(m.marks), 2) AS avg_marks FROM students s JOIN marks m ON s.student_id = m.student_id GROUP BY s.student_id, s.name, s.division ORDER BY avg_marks DESC LIMIT 5;` | Word Number Normalization ("five" &rarr; 5), Multi-Table JOIN, LIMIT |
| *"Count students in each department"* | `SELECT division AS department, COUNT(*) AS student_count FROM students GROUP BY division ORDER BY division;` | Column Alias, COUNT(*), GROUP BY |
| *"Show students and their subject marks"* | `SELECT s.student_id, s.name, s.division, sub.subject_name, m.marks FROM students s JOIN marks m ON s.student_id = m.student_id JOIN subjects sub ON m.subject_id = sub.subject_id ORDER BY s.name, sub.subject_name;` | 3-Table Relational JOIN (`students` + `marks` + `subjects`) |
| *"Show all students"* | `SELECT student_id, name, division, email FROM students ORDER BY name;` | Projection, Sorting |
