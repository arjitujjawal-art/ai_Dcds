# QueryMind (DCDS-NLP)

> **Intelligent Natural Language to SQL Query System with Role-Based Database Governance**

QueryMind empowers users to query an academic database by asking questions in ordinary plain English. It converts those questions into SQL, validates them against strict AST security rules, executes authorized queries, visualizes results with interactive tables and charts, and maintains a complete audit trail.

---

## 🚀 Quick Start

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/12karthikpra-dev/DCDS-NLP.git
cd DCDS-NLP
pip install -r requirements.txt
```

### 2. Run the App

```bash
python app.py
```

The database automatically initializes and self-seeds on first startup (zero setup required).

Open **http://127.0.0.1:5000** in your browser.

---

## 🔑 Role-Differentiated Portals & Demo Credentials

QueryMind features three purpose-built portals with customized UI themes and clearance scopes:

| Role | Username | Password | Theme & Portal Scope |
|---|---|---|---|
| **Student** | `student1` | `stud123` | **Emerald Theme**: Personalized student dashboard for Aarav Sharma, coursework grades, attendance tracker, distinction status, and student-scoped academic queries. |
| **Faculty** | `teacher1` | `teach123` | **Amber Theme**: Class analytics, division performance comparison matrix (Divisions A, B, C), and Attendance Defaulters Radar (`< 75%` attendance). |
| **Admin** | `admin` | `admin123` | **Crimson Theme**: Enterprise data governance, security audit logs, database schema & user account management (`app_users`), and full system query logs. |

> *Tip: You can click any demo credential card on the login page to auto-fill.*

---

## 🧠 System Architecture

```text
User Question (Plain English)
            │
            ▼
┌───────────────────────────┐
│     NLP / SQL Engine      │  Extracts intent, keywords, aggregation, limits, thresholds
└───────────┬───────────────┘
            │
            ▼
┌───────────────────────────┐
│ Zero-Trust SQL Validator  │  Blocks DML/DDL (INSERT/UPDATE/DELETE/DROP), prevents injection,
└───────────┬───────────────┘  enforces table/column allowlists and role-based permissions
            │
            ▼
┌───────────────────────────┐
│   SQLite Database Engine  │  Executes authorized read-only queries with millisecond timing
└───────────┬───────────────┘
            │
            ▼
┌───────────────────────────┐
│ Visualization & Governance│  Displays interactive tables, Chart.js graphs, and logs
└───────────────────────────┘  complete query execution & security events to audit trail
```

---

## 💬 Example Questions Supported

- *"Show me the top 5 students with the highest average marks"*
- *"What is the average attendance of each division?"*
- *"Which subjects have an average score below 60?"*
- *"Show students with attendance below 75%"*
- *"Compare average marks across divisions"*
- *"How many students scored above 80 in each subject"*
- *"Show all students"*
- *"Show all subjects"*
- *"Min and max marks per subject"*
- *"Total credits"*

---

## 🛡️ Security & Governance

- **Read-Only Enforcement**: Rejects `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `EXEC`.
- **AST Parsing**: Validates SQL structure using `sqlglot` with fallback tokenizer checks.
- **Role-Based Access Control**: Sensitive tables like `app_users` are restricted to Admin clearance.
- **Sensitive Column Masking**: Columns containing `password_hash`, `secret`, or `token` are blocked from student and faculty output.
- **Audit Logging**: Every authentication event, query execution, and blocked attempt is recorded with timestamps and execution metadata.

---

## 🧪 Testing

Run the test suite:

```bash
pytest tests/ -v
```

All 22 unit & integration tests verify:
- NLP keyword extraction & SQL generation
- Aggregations (`AVG`, `COUNT`, `SUM`, `MIN`, `MAX`)
- Multi-table `JOIN` and `GROUP BY` logic
- SQL injection prevention (semicolons, SQL comments, blocked keywords)
- Role-based table access clearance
