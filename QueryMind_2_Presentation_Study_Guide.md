# QueryMind 2.0: Academic Presentation & Viva Defense Study Guide

- **Course:** Data Communication & Database Systems (DCDS) — ESE Project (2025–2026)
- **Target System:** QueryMind 2.0 (Branch: `querymind-2.0`)
- **Verification Baseline:** 99 / 99 Automated Pytest Tests Passing (100%)

---

## 1. The 2-Minute Elevator Pitch (How to Introduce Your Project in 60–90 Seconds)

> *"Good morning, esteemed examiners. Our project is **QueryMind 2.0**, a voice-enabled relational database query system. While voice provides an accessible, hands-free input modality, our core engineering focus is strictly on **Relational Database Management Systems (RDBMS)**.
> 
> Non-technical stakeholders—like educators and academic administrators—struggle to write SQL and navigate complex schemas. Meanwhile, commercial LLM wrappers suffer from stochastic hallucinations, unpredictable table selection, and destructive query risks.
> 
> QueryMind 2.0 solves this by introducing a **deterministic, multi-tier pipeline**:
> 1. We capture speech using the browser-native W3C Web Speech API with **strict pre-execution review**—audio stop never auto-executes queries.
> 2. We pass speech through an explicit **5-state Intent Classification Engine** that halts conversational greetings and out-of-scope talk before SQL synthesis.
> 3. We validate queries mathematically using **SQLGlot Abstract Syntax Trees (AST)** to enforce read-only SELECT rules and inject defensive `LIMIT 100` row ceilings.
> 4. We execute queries across a **Dual-Engine Database Adapter** supporting Cloud Supabase PostgreSQL 15+ with Row-Level Security (RLS) and local SQLite in Write-Ahead Logging (WAL) mode.
> 5. We expose database internals through **live Mermaid ER diagrams** and **EXPLAIN QUERY PLAN execution profiling**.
> 
> Our system is verified through **99 automated pytest tests with a 100% pass rate**. Let us demonstrate how it works."*

---

## 2. Slide-by-Slide Presentation Script (What to Say for Each Slide 1 to 13)

### Slide 1: Title Slide
> *"Respected examiners, this is QueryMind 2.0. Our course is DCDS. Our project integrates voice natural language processing with rigorous relational database principles, AST security governance, and cloud Supabase PostgreSQL."*

### Slide 2: Problem Statement & Motivation
> *"Why did we build this? Two reasons: First, writing SQL joins and aggregations is too difficult for ordinary users. Second, existing AI wrappers are dangerous—they hallucinate non-existent tables or emit DROP TABLE statements. Even worse, our baseline had a critical defect: speaking 'hello how are you' generated an arbitrary query `SELECT * FROM exam_scores LIMIT 50` with a fake 'Safe' badge. We set out to fix this permanently."*

### Slide 3: Objectives & Scope
> *"Our objectives were five-fold: zero-install browser voice capture, deterministic 5-state intent gating, dual-engine RDBMS support (PostgreSQL + SQLite), mathematical SQLGlot AST validation, and educational DBMS transparency via live Mermaid ER diagrams and EXPLAIN query plan profiling."*

### Slide 4: System Overview / Proposed Solution
> *"Here is our decoupled architecture. Notice the critical principle: **Microphone stop NEVER automatically executes queries**. The voice stream is normalized, classified for intent, translated to SQL, parsed into an AST, and displayed in an interactive editor. The user must manually click [Run Query]. We also eliminated misleading single 'Safe' badges by providing separate badges for Speech Recognized, Intent Validated, and AST Validated."*

### Slide 5: Requirements & Tech Stack
> *"We use Python 3.11 with Flask for the REST backend, Vanilla JavaScript with the Web Speech API on the frontend without heavy framework overhead, SQLite in WAL mode for local zero-config CI, Supabase PostgreSQL 15+ for enterprise cloud deployment, SQLGlot for AST parsing, and Pytest running our 99 tests."*

### Slide 6: Database Design — ER Diagram
> *"Our relational database models academic records: `students`, `subjects`, `marks`, and `attendance`. Foreign keys enforce referential integrity with cascading deletes. In our live system, the ER diagram is generated dynamically using Mermaid.js by querying SQLite catalog pragmas and PostgreSQL constraints."*

### Slide 7: Relational Schema & Normalization (1NF, 2NF, 3NF)
> *"Our schema strictly satisfies Third Normal Form (3NF). 1NF is satisfied because all attributes are atomic scalar values with designated primary keys. 2NF is satisfied because transactional records (`marks` and `attendance`) use composite candidate keys `(student_id, subject_id)`, and subject attributes like credits are decoupled to `subjects`, eliminating partial dependencies. 3NF is satisfied because student demographics reside strictly in `students`, eliminating transitive dependencies like mark_id &rarr; student_id &rarr; division."*

### Slide 8: Implementation & SQL Operations
> *"Our SQL generator translates voice queries into multi-table relational joins, aggregate grouping, and threshold filtering (like attendance below 75%). Importantly, our AST parser auto-injects `LIMIT 100` ceilings when queries omit limits, protecting database memory buffer pools from exhaustion."*

### Slide 9: Results / Demonstration
> *"In our live workspace, speaking a greeting like 'hello how are you' returns an out-of-scope status, clears the SQL editor, hides the AST badge, and suggests valid questions. When a valid query runs, our interactive [Explain Plan] drawer reveals whether the database used a full table scan or an index lookup."*

### Slide 10: Testing & Validation
> *"We adhere to a strict test-driven development loop. Our automated test suite grew from 59 to **99 passing tests** across 5 test files in 3.99 seconds, including 40 regression tests in `test_intent_regression.py` verifying our greeting bug fix."*

### Slide 11: Conclusion & Future Scope
> *"We have proven that natural language voice interaction with databases can be achieved safely without LLM hallucinations. For future scope, we plan to add offline Vosk WebAssembly models for air-gapped institutions and Redis multi-turn session memory."*

### Slide 12: References & Q&A
> *"We cited primary sources including E. F. Codd's 1970 relational model paper, W3C Web Speech specifications, and PostgreSQL 15 documentation. We are now eager to answer your questions and demonstrate the live system."*

---

## 3. Core DBMS Concepts Tested in Viva (With Exact Answers)

### Q1: How do you prove your database is in 3NF?
**Answer:**
We establish functional dependencies:
- `student_id` &rarr; `{ name, division, email }`
- `subject_id` &rarr; `{ subject_name, credits }`
- `{ student_id, subject_id }` &rarr; `{ marks, attendance_percentage }`

- **1NF:** Atomic scalar attributes with designated primary keys.
- **2NF:** `marks` and `attendance` have composite key `(student_id, subject_id)`. All non-key attributes depend on the **entire** key. Subject credits are isolated in `subjects` table, eliminating partial functional dependencies.
- **3NF:** No transitive dependencies ($X \to Y \land Y \to Z$). Student division depends solely on `student_id`, not stored in `marks` table. Hence, 3NF holds strictly.

### Q2: Why SQLGlot AST parsing instead of Regex blacklists?
**Answer:**
Regex string matching is easily bypassed by SQL comment obfuscation (`SEL/**/ECT`) or semicolon chaining. SQLGlot tokenizes queries into an in-memory Abstract Syntax Tree. We verify the root node is strictly `exp.Select`, disallowing DDL/DML at the compiler level.

### Q3: Difference between SQLite WAL mode and traditional rollback journal?
**Answer:**
Rollback journals acquire exclusive write locks that block all readers. WAL (Write-Ahead Logging) appends modifications to a separate `.wal` file, allowing concurrent multi-reader access without lock contention, while ensuring ACID durability.

### Q4: How does EXPLAIN QUERY PLAN work in QueryMind 2.0?
**Answer:**
We execute `EXPLAIN QUERY PLAN <sql>`. SQLite's optimizer returns an execution tree. We parse node types:
- `FULL_TABLE_SCAN`: Scanning all physical pages sequentially.
- `INDEX_SEARCH`: $\mathcal{O}(\log N)$ B-Tree index seek using primary or foreign keys.
- `TEMP_BTREE_SORT`: Allocating temporary RAM/disk B-Tree to satisfy `ORDER BY`.

### Q5: How does Supabase PostgreSQL Row-Level Security (RLS) work?
**Answer:**
RLS operates at the PostgreSQL kernel level. For students, policies enforce:
`USING (student_id IN (SELECT s.student_id FROM students s JOIN users u ON s.user_id = u.user_id WHERE u.auth_uid = auth.uid()))`
Even if an unauthorized query is attempted, PostgreSQL returns an empty set or only authorized rows.

---

## 4. The Critical Bug Defense: The Greeting Bug Autopsy

> **Question: "What was the hardest bug you faced and how did you resolve it?"**

**Answer:**
*"Our most critical defect was in voice intent handling. Speaking 'hello how are you' produced an arbitrary query: `SELECT * FROM exam_scores LIMIT 50`, with a deceptive 'Safe' badge.*

*Root Cause:*
1. In `nlp/sql_generator.py` (line 402), `generate_sql_for_dataset()` unconditionally fell back to `SELECT * FROM {table_name} LIMIT 50` whenever no keywords matched.
2. The API gateway routed all transcriptions straight to SQL synthesis without an intent classification stage.
3. In `static/js/voice_sql.js`, `#sqlEditor` was never cleared on unrecognized input, leaving stale SQL executable.

*Solution:*
1. Removed the arbitrary fallback in `nlp/sql_generator.py` (returns `matched: False`).
2. Created a 5-state Intent Classifier in `nlp/intent_classifier.py` (`OUT_OF_SCOPE`, `AMBIGUOUS_QUERY`, `UNSUPPORTED_OPERATION`, `EMPTY_INPUT`, `DATABASE_QUERY`).
3. Updated `static/js/voice_sql.js` to clear `#sqlEditor`, reset AST badges, and render clickable suggestions.
4. Created 40 regression tests in `tests/test_intent_regression.py` proving that greetings return zero SQL and cannot execute queries."*

---

## 5. Top 10 Rapid-Fire Viva Questions

1. **What happens if a user speaks "Drop table students"?**
   &rarr; Classified as `UNSUPPORTED_OPERATION`. AST validation also blocks `exp.Drop`.
2. **Does the microphone auto-execute queries?**
   &rarr; No, audio stop only populates the editor. User must review and click `[Run Query]`.
3. **Why have both SQLite and PostgreSQL?**
   &rarr; SQLite WAL mode provides zero-config local CI. Supabase PostgreSQL provides cloud persistence and Row-Level Security (RLS).
4. **What prevents SQL injection in QueryMind 2.0?**
   &rarr; SQLGlot AST validation parses single-statement Select trees, rejects semicolon chaining and comment injection, and auto-injects `LIMIT 100`.
5. **What is an ambiguous query?**
   &rarr; *"Show me the data"* or *"Find records"*. The system asks the user to clarify which table or entity they wish to inspect.
6. **How is the Mermaid ER diagram created?**
   &rarr; Introspects SQLite `PRAGMA foreign_key_list` and dynamically compiles Mermaid syntax.
7. **What is ON DELETE CASCADE?**
   &rarr; When a parent student is deleted, related marks and attendance records are automatically removed to maintain referential integrity.
8. **How are passwords stored?**
   &rarr; Salted SHA-256 hashes in `app_users`, masked from student query results.
9. **How many automated tests are passing?**
   &rarr; 99 automated pytest tests across 5 test suites in 3.99 seconds (100% pass rate).
10. **Can custom CSVs be uploaded?**
    &rarr; Yes, administrators can upload CSVs in the Admin Dashboard, which creates SQLite tables and registers them for NLP queries.

---

## 6. Live Demonstration Cheat-Sheet (5-Step Sequence)

- **Demo 1 (Greeting Bug Fix):** Speak *"Hello how are you"*  
  &rarr; Show `status: out_of_scope`, zero SQL generated, editor blank, suggestions shown.
- **Demo 2 (Ambiguous Query):** Speak *"Show me the data"*  
  &rarr; Show `status: ambiguous`, prompts for target entity (students, subjects).
- **Demo 3 (Valid Relational Join):** Speak *"Students with attendance below 75 percent"*  
  &rarr; Show spoken normalization (*"seventy five percent"* &rarr; 75%), SQL join, AST badge.
- **Demo 4 (Internal Profiler):** Click `[Explain Plan]` drawer button  
  &rarr; Show execution plan tree: `SCAN attendance` vs `SEARCH students USING PK`.
- **Demo 5 (Live Schema Explorer):** Open `/database-explorer`  
  &rarr; Show dynamic Mermaid ER diagram generated from schema pragmas.
