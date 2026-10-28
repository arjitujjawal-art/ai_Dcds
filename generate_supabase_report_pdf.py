"""
Generate Publication-Quality PDF Report for:
QueryMind 2.0 – Voice-to-SQL with Supabase (Research Report)
And launch Adobe Acrobat to view it.
"""

import os
import shutil
import subprocess
import sys

HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>QueryMind 2.0 – Voice-to-SQL with Supabase (Research Report)</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    @page {
      size: A4 portrait;
      margin: 18mm 16mm 20mm 16mm;
      @bottom-right {
        content: "Page " counter(page);
        font-family: 'Inter', sans-serif;
        font-size: 8.5pt;
        color: #64748B;
      }
      @bottom-left {
        content: "QueryMind 2.0 — Voice-to-SQL with Supabase (Research Report)";
        font-family: 'Inter', sans-serif;
        font-size: 8.5pt;
        color: #64748B;
      }
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      font-size: 9.5pt;
      line-height: 1.55;
      color: #1E293B;
      background: #FFFFFF;
    }

    /* Header Banner */
    .header-banner {
      border-bottom: 2.5px solid #0F172A;
      padding-bottom: 16px;
      margin-bottom: 22px;
    }

    .badge-strip {
      display: flex;
      gap: 8px;
      margin-bottom: 10px;
    }

    .badge {
      font-size: 8pt;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 3px 8px;
      border-radius: 4px;
      display: inline-block;
    }

    .badge-primary { background: #EEF2FF; color: #3730A3; border: 1px solid #C7D2FE; }
    .badge-emerald { background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; }
    .badge-amber { background: #FFFBEB; color: #92400E; border: 1px solid #FDE68A; }
    .badge-slate { background: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; }

    h1.doc-title {
      font-size: 21pt;
      font-weight: 800;
      line-height: 1.22;
      color: #0F172A;
      letter-spacing: -0.025em;
      margin-bottom: 8px;
    }

    .doc-meta-row {
      display: flex;
      justify-content: space-between;
      font-size: 8.8pt;
      color: #64748B;
      margin-top: 6px;
      border-top: 1px solid #E2E8F0;
      padding-top: 8px;
    }

    /* Headings */
    h2 {
      font-size: 13pt;
      font-weight: 700;
      color: #0F172A;
      letter-spacing: -0.015em;
      margin-top: 22px;
      margin-bottom: 10px;
      padding-bottom: 4px;
      border-bottom: 1.5px solid #E2E8F0;
      page-break-after: avoid;
    }

    h3 {
      font-size: 10.5pt;
      font-weight: 600;
      color: #1E293B;
      margin-top: 14px;
      margin-bottom: 6px;
      page-break-after: avoid;
    }

    p {
      margin-bottom: 9px;
      text-align: justify;
    }

    ul, ol {
      margin-left: 20px;
      margin-bottom: 11px;
    }

    li {
      margin-bottom: 4px;
    }

    /* Callouts */
    .callout {
      background: #F8FAFC;
      border-left: 4px solid #3B82F6;
      border-radius: 0 6px 6px 0;
      padding: 12px 14px;
      margin-bottom: 14px;
      font-size: 9.3pt;
    }

    .callout-title {
      font-weight: 700;
      color: #1E3A8A;
      margin-bottom: 4px;
      text-transform: uppercase;
      font-size: 8pt;
      letter-spacing: 0.05em;
    }

    .callout-success {
      background: #F0FDF4;
      border-left-color: #10B981;
    }
    .callout-success .callout-title { color: #065F46; }

    .callout-warning {
      background: #FFFBEB;
      border-left-color: #F59E0B;
    }
    .callout-warning .callout-title { color: #92400E; }

    /* Tables */
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 12px 0 16px 0;
      font-size: 8.7pt;
      page-break-inside: avoid;
    }

    th {
      background: #0F172A;
      color: #FFFFFF;
      text-align: left;
      padding: 7px 10px;
      font-weight: 600;
      border: 1px solid #0F172A;
    }

    td {
      padding: 6px 10px;
      border: 1px solid #CBD5E1;
      vertical-align: top;
    }

    tr:nth-child(even) {
      background: #F8FAFC;
    }

    /* Code blocks */
    pre {
      font-family: 'JetBrains Mono', monospace;
      font-size: 8.2pt;
      background: #0F172A;
      color: #E2E8F0;
      padding: 11px 14px;
      border-radius: 6px;
      overflow-x: auto;
      margin: 10px 0 14px 0;
      line-height: 1.45;
      page-break-inside: avoid;
    }

    code {
      font-family: 'JetBrains Mono', monospace;
      font-size: 8.5pt;
      background: #F1F5F9;
      color: #0F172A;
      padding: 2px 5px;
      border-radius: 3px;
      border: 1px solid #E2E8F0;
    }

    pre code {
      background: transparent;
      color: inherit;
      padding: 0;
      border: none;
    }

    /* Architecture Visual Diagram */
    .flow-diagram-container {
      background: #F8FAFC;
      border: 1.5px solid #CBD5E1;
      border-radius: 8px;
      padding: 14px;
      margin: 14px 0;
      page-break-inside: avoid;
    }

    .flow-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 10px;
    }

    .flow-node {
      flex: 1;
      background: #FFFFFF;
      border: 1.5px solid #94A3B8;
      border-radius: 6px;
      padding: 8px 10px;
      text-align: center;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    .flow-node-title {
      font-weight: 700;
      font-size: 8.5pt;
      color: #0F172A;
      margin-bottom: 2px;
    }

    .flow-node-desc {
      font-size: 7.5pt;
      color: #64748B;
      line-height: 1.25;
    }

    .flow-node.client { border-color: #3B82F6; background: #EFF6FF; }
    .flow-node.client .flow-node-title { color: #1E40AF; }

    .flow-node.server { border-color: #10B981; background: #F0FDF4; }
    .flow-node.server .flow-node-title { color: #065F46; }

    .flow-node.db { border-color: #8B5CF6; background: #F5F3FF; }
    .flow-node.db .flow-node-title { color: #5B21B6; }

    .flow-arrow {
      font-size: 14pt;
      font-weight: 800;
      color: #64748B;
      flex: 0 0 16px;
      text-align: center;
    }

    /* Slides Grid */
    .slides-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;
      margin: 12px 0 16px 0;
      page-break-inside: avoid;
    }

    .slide-card {
      border: 1px solid #CBD5E1;
      border-radius: 6px;
      padding: 8px 10px;
      background: #F8FAFC;
    }

    .slide-number {
      font-size: 7.5pt;
      font-weight: 700;
      color: #3B82F6;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .slide-title {
      font-size: 9pt;
      font-weight: 700;
      color: #0F172A;
      margin: 2px 0;
    }

    .slide-content {
      font-size: 7.8pt;
      color: #475569;
      line-height: 1.35;
    }

    /* Checklist */
    .checklist-item {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      margin-bottom: 6px;
      font-size: 9pt;
    }

    .check-icon {
      color: #10B981;
      font-weight: 800;
      font-size: 10pt;
      line-height: 1;
    }

    .page-break {
      page-break-before: always;
    }
  </style>
</head>
<body>

  <!-- Cover / Header Banner -->
  <div class="header-banner">
    <div class="badge-strip">
      <span class="badge badge-primary">Research & Architectural Report</span>
      <span class="badge badge-emerald">Supabase (PostgreSQL) Migration</span>
      <span class="badge badge-amber">Speech-to-Text Integration</span>
      <span class="badge badge-slate">v2.0 Academic DBMS</span>
    </div>
    <h1 class="doc-title">QueryMind 2.0 – Voice-to-SQL with Supabase</h1>
    <div style="font-size: 10.5pt; color: #475569; font-weight: 500; margin-bottom: 6px;">
      Comprehensive Architectural Analysis, STT Evaluation, Cloud Relational Migration, and Phased Implementation Blueprint
    </div>
    <div class="doc-meta-row">
      <span><strong>Document Reference:</strong> QM-REP-2026-V2</span>
      <span><strong>Target Engine:</strong> Supabase PostgreSQL 15+ & Web Speech API / Vosk</span>
      <span><strong>Academic Focus:</strong> Relational DBMS Governance</span>
    </div>
  </div>

  <!-- Executive Summary -->
  <div class="callout">
    <div class="callout-title">Executive Summary</div>
    <p>
      This report analyzes how to extend the <strong>QueryMind</strong> academic DBMS query platform with voice input (speech-to-text) and a robust <strong>Supabase (PostgreSQL)</strong> relational backend. We begin by auditing the existing repository structure and identifying where speech functionality integrates seamlessly. Next, we survey open-source speech-to-text (STT) solutions across browser-based and server-side paradigms, evaluating trade-offs in accuracy, licensing, latency, and resource footprint.
    </p>
    <p>
      We then outline a concrete migration plan from the existing SQLite embedded schema to a hosted Supabase PostgreSQL cluster, specifying table definitions, foreign keys, Row-Level Security (RLS) policies, and automated backup strategies. An end-to-end architecture diagram illustrates the flow: <em>User Voice &rarr; STT &rarr; Intent Parsing & SQL Generation &rarr; AST Validation &rarr; Supabase Query Execution &rarr; Tabular and Chart Visualization</em>. We propose an iterative developer implementation loop with automated acceptance criteria, detail API and schema changes, provide a rigorous 4-layer testing plan, present an academic presentation slide deck outline, and cite primary documentation sources.
    </p>
  </div>

  <!-- Section 1 -->
  <h2>1. Repository Audit & Current Codebase Inspection</h2>
  <p>
    An audit of the QueryMind repository reveals a monolithic Flask web application utilizing Jinja2 HTML templates and an embedded SQLite database (<code>db/querymind.db</code>). The core functional modules include:
  </p>
  <ul>
    <li><strong>Backend Execution (<code>app.py</code>):</strong> Manages session-based authentication, user roles (Student, Faculty, Admin), dashboard routing, dataset CSV upload handling, query execution, history logging, and audit tracking.</li>
    <li><strong>Natural Language Engine (<code>nlp/sql_generator.py</code>):</strong> Implements deterministic, rule-based regular expression mapping from academic English queries to SQL SELECT statements.</li>
    <li><strong>Security & Validation (<code>nlp/sql_validator.py</code>):</strong> Utilizes AST parsing and token allow-listing to block DDL/DML injection (e.g., <code>DROP</code>, <code>INSERT</code>, <code>DELETE</code>, multi-statement semicolons, comment markers).</li>
    <li><strong>Data Access Layer (<code>db/database.py</code>):</strong> Encapsulates SQLite connection management, table initialization, and schema seeding for academic entities (students, subjects, marks, attendance, users, query logs).</li>
    <li><strong>User Interface (Templates & Static):</strong> Jinja2 templates (<code>dashboard.html</code>, <code>result.html</code>, <code>explorer.html</code>, <code>workspace.html</code>) and static assets (<code>style.css</code>, <code>main.js</code>).</li>
  </ul>

  <div class="callout callout-warning">
    <div class="callout-title">Audit Finding: Voice Mode Realignment</div>
    <p>
      Inspection confirmed that previous iterations possessed no voice input capture. Clarifying the user requirement: the microphone must function strictly as an <strong>input capture mechanism</strong> (Speech-to-Text), transcribing spoken academic questions into an editable text field for pre-execution inspection, rather than performing voice synthesis (TTS).
    </p>
  </div>

  <p>
    <strong>Integration Strategy:</strong> The deterministic English-to-SQL logic in <code>nlp/sql_generator.py</code> remains intact as an academically verifiable pipeline. Speech recognition is positioned as an upstream transcription layer in the browser, while the storage and execution tier transitions from SQLite to Supabase PostgreSQL.
  </p>

  <!-- Section 2 -->
  <h2>2. Speech-to-Text (STT) Options & Technical Evaluation</h2>
  <p>
    To select the optimal STT engine, we evaluated five open-source and standards-based speech-to-text solutions across accuracy, compute requirements, offline capabilities, and licensing:
  </p>

  <table>
    <thead>
      <tr>
        <th style="width: 18%;">Solution</th>
        <th style="width: 12%;">License</th>
        <th style="width: 14%;">Offline Capable</th>
        <th style="width: 16%;">Languages</th>
        <th style="width: 40%;">Accuracy, Latency & Architecture Notes</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Web Speech API</strong></td>
        <td>W3C Standard (Browser)</td>
        <td>No (Requires network)</td>
        <td>Multi-language (Google Engine)</td>
        <td>High accuracy for English academic phrasing; native JavaScript (zero client bundle); supported in Chrome & Edge; immediate real-time transcription.</td>
      </tr>
      <tr>
        <td><strong>Vosk (Alpha Cephei)</strong></td>
        <td>Apache 2.0</td>
        <td>Yes (On-Device / WASM)</td>
        <td>20+ (inc. English, Hindi, Spanish)</td>
        <td>Moderate-to-high accuracy; extremely lightweight (~50MB model); runnable inside browser via WebAssembly or server-side via Python bindings.</td>
      </tr>
      <tr>
        <td><strong>Coqui STT</strong></td>
        <td>MPL 2.0</td>
        <td>Yes (Local CPU/GPU)</td>
        <td>English primary</td>
        <td>Based on DeepSpeech; streaming inference with small footprint (~100–200MB); requires server-side deployment or background Python worker.</td>
      </tr>
      <tr>
        <td><strong>OpenAI Whisper</strong></td>
        <td>MIT</td>
        <td>Yes (High Compute)</td>
        <td>~100 languages</td>
        <td>State-of-the-art robustness against noise and accents; models range from 70MB (tiny) to 1.5GB+ (medium); requires GPU or high server CPU.</td>
      </tr>
      <tr>
        <td><strong>Kaldi</strong></td>
        <td>Apache 2.0</td>
        <td>Yes</td>
        <td>Configurable</td>
        <td>Research-grade HMM/DNN toolkit; steep operational setup and compilation; best utilized indirectly through Vosk abstractions.</td>
      </tr>
    </tbody>
  </table>

  <div class="callout callout-success">
    <div class="callout-title">Architectural Recommendation: Hybrid Client-Server Tier</div>
    <p>
      <strong>Primary Mode:</strong> Implement the <strong>Web Speech API</strong> (<code>window.SpeechRecognition</code>) in JavaScript for instant, zero-latency in-browser transcription without server overhead.<br>
      <strong>Fallback Tier:</strong> Provide a server-side <code>POST /speech</code> endpoint backed by <strong>Vosk</strong> or <strong>Whisper-tiny</strong> for browsers lacking native SpeechRecognition (Safari/Firefox) or offline environments.
    </p>
  </div>

  <!-- Section 3 -->
  <div class="page-break"></div>
  <h2>3. Supabase (PostgreSQL) Migration Plan</h2>
  <p>
    Migrating QueryMind from local SQLite to a cloud-hosted <strong>Supabase PostgreSQL</strong> instance elevates the application into an enterprise-ready relational DBMS featuring strict data integrity, indexing, foreign keys, Row-Level Security (RLS), and automated disaster recovery.
  </p>

  <h3>3.1 Relational Schema Specification</h3>
  <table>
    <thead>
      <tr>
        <th style="width: 15%;">Table Name</th>
        <th style="width: 35%;">Columns & Primary Keys</th>
        <th style="width: 50%;">Foreign Keys, Constraints & Indexes</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><code>users</code></td>
        <td><code>user_id UUID PRIMARY KEY</code>, <code>email TEXT UNIQUE</code>, <code>username TEXT UNIQUE</code>, <code>role TEXT CHECK (role IN ('student','faculty','admin'))</code>, <code>created_at TIMESTAMPTZ DEFAULT NOW()</code></td>
        <td>Integrated with <code>auth.users</code> via Supabase Auth UID. Index on <code>username</code>.</td>
      </tr>
      <tr>
        <td><code>students</code></td>
        <td><code>student_id SERIAL PRIMARY KEY</code>, <code>name TEXT NOT NULL</code>, <code>division VARCHAR(2) NOT NULL</code>, <code>user_id UUID</code></td>
        <td><code>FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL</code>. Index on <code>division</code>.</td>
      </tr>
      <tr>
        <td><code>subjects</code></td>
        <td><code>subject_id SERIAL PRIMARY KEY</code>, <code>name TEXT UNIQUE NOT NULL</code>, <code>department TEXT NOT NULL</code></td>
        <td>Index on <code>department</code>.</td>
      </tr>
      <tr>
        <td><code>marks</code></td>
        <td><code>mark_id SERIAL PRIMARY KEY</code>, <code>student_id INT NOT NULL</code>, <code>subject_id INT NOT NULL</code>, <code>marks NUMERIC(5,2) CHECK (marks >= 0 AND marks <= 100)</code>, <code>credits INT DEFAULT 4</code></td>
        <td><code>FK (student_id) REFERENCES students(student_id)</code><br><code>FK (subject_id) REFERENCES subjects(subject_id)</code><br>Composite Index on <code>(student_id, subject_id)</code>.</td>
      </tr>
      <tr>
        <td><code>attendance</code></td>
        <td><code>att_id SERIAL PRIMARY KEY</code>, <code>student_id INT NOT NULL</code>, <code>subject_id INT NOT NULL</code>, <code>attended INT NOT NULL</code>, <code>total_classes INT NOT NULL</code>, <code>percentage NUMERIC(5,2) GENERATED ALWAYS AS (ROUND((attended::numeric / total_classes::numeric) * 100, 2)) STORED</code></td>
        <td><code>FK (student_id) REFERENCES students(student_id)</code><br><code>FK (subject_id) REFERENCES subjects(subject_id)</code><br>Index on <code>student_id</code> and <code>percentage</code>.</td>
      </tr>
      <tr>
        <td><code>query_logs</code></td>
        <td><code>query_id UUID PRIMARY KEY DEFAULT gen_random_uuid()</code>, <code>user_id UUID</code>, <code>question TEXT NOT NULL</code>, <code>sql_query TEXT NOT NULL</code>, <code>input_mode VARCHAR(10) CHECK (input_mode IN ('voice','text'))</code>, <code>status TEXT</code>, <code>row_count INT</code>, <code>exec_time_ms NUMERIC(8,2)</code>, <code>created_at TIMESTAMPTZ DEFAULT NOW()</code></td>
        <td><code>FK (user_id) REFERENCES users(user_id)</code>. Index on <code>created_at DESC</code> and <code>user_id</code>.</td>
      </tr>
      <tr>
        <td><code>audit_logs</code></td>
        <td><code>audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid()</code>, <code>user_id UUID</code>, <code>action TEXT NOT NULL</code>, <code>target_table TEXT</code>, <code>ip_address TEXT</code>, <code>timestamp TIMESTAMPTZ DEFAULT NOW()</code></td>
        <td>Auditing trail for administrative oversight and compliance.</td>
      </tr>
    </tbody>
  </table>

  <h3>3.2 Row-Level Security (RLS) Implementation</h3>
  <p>
    Supabase enforces granular access control at the database kernel level through PostgreSQL Row-Level Security policies:
  </p>
  <pre><code>-- Enable RLS across all academic tables
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE marks ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendance ENABLE ROW LEVEL SECURITY;

-- Policy 1: Students can only view their own academic profile
CREATE POLICY "Student read own profile"
  ON students FOR SELECT
  USING (auth.uid() = user_id OR auth.jwt() ->> 'role' = 'faculty' OR auth.jwt() ->> 'role' = 'admin');

-- Policy 2: Students can only inspect their own marks
CREATE POLICY "Student read own marks"
  ON marks FOR SELECT
  USING (
    student_id IN (SELECT student_id FROM students WHERE user_id = auth.uid())
    OR auth.jwt() ->> 'role' IN ('faculty', 'admin')
  );

-- Policy 3: Attendance Defaulters visible to Faculty and Admins
CREATE POLICY "Faculty read attendance"
  ON attendance FOR SELECT
  USING (auth.jwt() ->> 'role' IN ('faculty', 'admin'));</code></pre>

  <h3>3.3 Migration Checklist & Backup Strategy</h3>
  <div class="checklist-item"><span class="check-icon">&#10004;</span><span><strong>Provision Supabase Project:</strong> Initialize project instance, configure PostgreSQL 15, and retrieve <code>SUPABASE_URL</code> and <code>SUPABASE_SERVICE_ROLE_KEY</code>.</span></div>
  <div class="checklist-item"><span class="check-icon">&#10004;</span><span><strong>Execute DDL Migrations:</strong> Run SQL table scripts, foreign keys, check constraints, and RLS policies via Supabase SQL Editor.</span></div>
  <div class="checklist-item"><span class="check-icon">&#10004;</span><span><strong>Extract & Convert SQLite Data:</strong> Export records from <code>db/querymind.db</code> to CSV/SQL dump, converting SQLite types to Postgres types.</span></div>
  <div class="checklist-item"><span class="check-icon">&#10004;</span><span><strong>Load & Verify Integrity:</strong> Ingest records via <code>psql</code> or Supabase CSV import; assert foreign key relational integrity and row counts.</span></div>
  <div class="checklist-item"><span class="check-icon">&#10004;</span><span><strong>Automated Backups:</strong> Enable Supabase daily snapshot backups (7-day retention). Configure daily automated CLI cron dump: <code>supabase db dump -f backup_$(date +%Y%m%d).sql</code>.</span></div>

  <!-- Section 4 -->
  <h2>4. Integration Architecture & Data Flow</h2>
  <p>
    The end-to-end processing pipeline bridges the browser voice interface, Flask application logic, SQL AST governance, and the remote Supabase database:
  </p>

  <div class="flow-diagram-container">
    <div style="font-weight: 700; font-size: 8.5pt; color: #475569; text-transform: uppercase; margin-bottom: 8px;">
      Figure 1: End-to-End Voice-to-SQL Architecture Flow
    </div>
    <div class="flow-row">
      <div class="flow-node client">
        <div class="flow-node-title">1. Voice Capture</div>
        <div class="flow-node-desc">Microphone &rarr; Web Speech API / MediaRecorder</div>
      </div>
      <div class="flow-arrow">&rarr;</div>
      <div class="flow-node client">
        <div class="flow-node-title">2. Transcription</div>
        <div class="flow-node-desc">Browser STT populates question input field</div>
      </div>
      <div class="flow-arrow">&rarr;</div>
      <div class="flow-node client">
        <div class="flow-node-title">3. User Inspection</div>
        <div class="flow-node-desc">User verifies / edits question and clicks [Generate]</div>
      </div>
    </div>
    <div class="flow-row">
      <div class="flow-arrow" style="transform: rotate(90deg); margin: 0 auto;">&darr;</div>
    </div>
    <div class="flow-row">
      <div class="flow-node server">
        <div class="flow-node-title">4. Flask API Router</div>
        <div class="flow-node-desc">POST /api/generate-sql & /api/validate-sql</div>
      </div>
      <div class="flow-arrow">&rarr;</div>
      <div class="flow-node server">
        <div class="flow-node-title">5. NL Engine & Validator</div>
        <div class="flow-node-desc">Regex templates & SQLGlot AST allow-list</div>
      </div>
      <div class="flow-arrow">&rarr;</div>
      <div class="flow-node db">
        <div class="flow-node-title">6. Supabase Postgres</div>
        <div class="flow-node-desc">Read-only connection, RLS, execution & logging</div>
      </div>
    </div>
    <div class="flow-row">
      <div class="flow-arrow" style="transform: rotate(90deg); margin: 0 auto;">&darr;</div>
    </div>
    <div class="flow-row">
      <div class="flow-node client" style="flex: 3; background: #F8FAFC; border-color: #0F172A;">
        <div class="flow-node-title" style="color: #0F172A;">7. Interactive Results Workspace (Client)</div>
        <div class="flow-node-desc">Tabular records, latency stats, row counts, and dynamic Chart.js academic graphs</div>
      </div>
    </div>
  </div>

  <!-- Section 5 -->
  <div class="page-break"></div>
  <h2>5. Step-by-Step Implementation Loop Prompt</h2>
  <p>
    For autonomous coding agents or engineering teams, the following iterative cycle provides structured prompts, exact commands, and unambiguous acceptance criteria:
  </p>

  <div class="callout">
    <div class="callout-title">Engineering Task Loop Prompt</div>
    <p>
      <strong>Prompt:</strong> "You are implementing Step <em>[N]</em> of QueryMind 2.0. Execute the specified file edits and run tests. Do not advance until all acceptance criteria pass without warnings."
    </p>
    <ul>
      <li>
        <strong>Step 1: Frontend Speech Capture & Inspection UI</strong><br>
        <em>Task:</em> Add microphone capture button in <code>voice_sql_workspace.html</code> and bind Web Speech API in <code>static/js/voice_sql.js</code>. Populate editable input without auto-executing.<br>
        <em>Acceptance Criteria (✅):</em> Spoken phrase appears in <code>#voiceQuestionInput</code>; waveform animates during speech; no errors in DevTools console.
      </li>
      <li>
        <strong>Step 2: Spoken Number Normalization & Template Expansion</strong><br>
        <em>Task:</em> Implement <code>normalize_spoken_numbers()</code> in <code>nlp/sql_generator.py</code> converting words ("five" &rarr; "5", "seventy five" &rarr; "75"). Add attendance threshold and join patterns.<br>
        <em>Acceptance Criteria (✅):</em> <code>pytest tests/test_querymind_2.py -k test_spoken_number_normalization</code> passes.
      </li>
      <li>
        <strong>Step 3: Supabase Client Adapter & Connection Management</strong><br>
        <em>Task:</em> Add <code>supabase-py</code> client integration in <code>db/supabase_client.py</code> with fallback to local SQLite when credentials are absent.<br>
        <em>Acceptance Criteria (✅):</em> <code>test_supabase_connection</code> connects and verifies table counts.
      </li>
      <li>
        <strong>Step 4: SQLGlot AST Security Governance & Automatic Limit Clamping</strong><br>
        <em>Task:</em> Enforce SELECT-only statements; block DDL/DML, multi-statement queries, and inject <code>LIMIT 100</code> ceiling.<br>
        <em>Acceptance Criteria (✅):</em> <code>pytest tests/test_querymind_2.py -k test_blocks_ddl_and_dml</code> blocks injections with HTTP 400.
      </li>
      <li>
        <strong>Step 5: End-to-End Integration & Workspace Execution</strong><br>
        <em>Task:</em> Wire <code>POST /api/generate-sql</code>, <code>POST /api/validate-sql</code>, and <code>POST /api/execute-sql</code> to return execution latency, row counts, and data arrays.<br>
        <em>Acceptance Criteria (✅):</em> Full test suite passes (49/49 tests); workspace displays results table and Chart.js bar graph.
      </li>
    </ul>
  </div>

  <!-- Section 6 -->
  <h2>6. Frontend / Backend Changes & API Specifications</h2>
  <table>
    <thead>
      <tr>
        <th style="width: 20%;">Endpoint</th>
        <th style="width: 10%;">Method</th>
        <th style="width: 35%;">Payload / Request Format</th>
        <th style="width: 35%;">Response Payload / Description</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><code>/api/generate-sql</code></td>
        <td><code>POST</code></td>
        <td><code>{"question": "Show top 5 students by marks"}</code></td>
        <td><code>{"sql": "SELECT ...", "status": "success"}</code><br>Translates natural language to SQL without executing.</td>
      </tr>
      <tr>
        <td><code>/api/validate-sql</code></td>
        <td><code>POST</code></td>
        <td><code>{"sql": "SELECT * FROM students"}</code></td>
        <td><code>{"valid": true, "sanitized_sql": "SELECT ... LIMIT 100"}</code><br>SQLGlot AST validation and safety verification.</td>
      </tr>
      <tr>
        <td><code>/api/execute-sql</code></td>
        <td><code>POST</code></td>
        <td><code>{"sql": "SELECT ...", "input_mode": "voice"}</code></td>
        <td><code>{"columns": [...], "rows": [...], "row_count": 5, "exec_time_ms": 12.4}</code><br>Executes validated SQL and records query log.</td>
      </tr>
      <tr>
        <td><code>/api/schema</code></td>
        <td><code>GET</code></td>
        <td>None</td>
        <td><code>{"tables": {...}, "mermaid": "erDiagram ..."}</code><br>Live metadata and dynamic ER diagram.</td>
      </tr>
    </tbody>
  </table>

  <h3>Standard Academic Query Templates (PostgreSQL Syntax)</h3>
  <pre><code>-- 1. Top N Students by Average Marks (Multi-table Aggregation & Join)
SELECT s.student_id, s.name, s.division, ROUND(AVG(m.marks), 2) AS avg_marks
FROM students s
JOIN marks m ON s.student_id = m.student_id
GROUP BY s.student_id, s.name, s.division
ORDER BY avg_marks DESC
LIMIT 5;

-- 2. Attendance Defaulters (< 75% Threshold)
SELECT s.student_id, s.name, s.division, sub.name AS subject, a.percentage AS attendance_pct
FROM students s
JOIN attendance a ON s.student_id = a.student_id
JOIN subjects sub ON a.subject_id = sub.subject_id
WHERE a.percentage < 75.00
ORDER BY a.percentage ASC;

-- 3. Departmental Student Distribution
SELECT department, COUNT(student_id) AS total_enrolled
FROM subjects sub
JOIN marks m ON sub.subject_id = m.subject_id
GROUP BY department;</code></pre>

  <!-- Section 7 -->
  <div class="page-break"></div>
  <h2>7. Testing & Quality Assurance Plan</h2>
  <p>
    A multi-tier QA matrix verifies transcription handling, AST governance, relational query performance, and user interface responsiveness:
  </p>
  <ul>
    <li><strong>Unit Testing (Python / Pytest):</strong> Assert regex pattern coverage in <code>nlp/sql_generator.py</code>; verify spoken word normalization ("eighty" &rarr; 80); validate SQLGlot AST rule enforcement in <code>nlp/sql_validator.py</code>.</li>
    <li><strong>Security & Injection Testing:</strong> Attempt malicious payloads (e.g., <code>'; DROP TABLE students; --</code>, UNION-based exfiltration, hash column access). Assert HTTP 400 rejection and database schema immutability.</li>
    <li><strong>Row-Level Security (RLS) Verification:</strong> Connect as Student role; verify query cannot return records belonging to other students. Connect as Faculty/Admin; verify complete division visibility.</li>
    <li><strong>Performance & Latency Benchmarks:</strong> Measure voice transcription-to-render pipeline latency. Target: &lt; 200ms backend translation and query execution for indexed tables.</li>
  </ul>

  <!-- Section 8 -->
  <h2>8. Migration & Deployment Checklist & Effort Estimates</h2>
  <table>
    <thead>
      <tr>
        <th style="width: 45%;">Milestone / Engineering Phase</th>
        <th style="width: 35%;">Deliverables & Tasks</th>
        <th style="width: 20%;">Estimated Effort</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Phase 1: Voice Capture & UI Workspace</strong></td>
        <td>Web Speech API integration, visual audio wave animation, editable SQL panel.</td>
        <td>8 Hours</td>
      </tr>
      <tr>
        <td><strong>Phase 2: Fallback Server STT Tier</strong></td>
        <td>Vosk / Whisper-tiny endpoint in Flask, audio upload decoding.</td>
        <td>10 Hours</td>
      </tr>
      <tr>
        <td><strong>Phase 3: Supabase Schema & Migration</strong></td>
        <td>DDL migrations, foreign keys, indexes, RLS policies, SQLite data transfer.</td>
        <td>12 Hours</td>
      </tr>
      <tr>
        <td><strong>Phase 4: AST Governance & SQLGlot</strong></td>
        <td>AST parser allow-listing, limit injection, parameterized queries.</td>
        <td>8 Hours</td>
      </tr>
      <tr>
        <td><strong>Phase 5: Automated Testing & QA</strong></td>
        <td>49+ unit, integration, and security test cases in pytest.</td>
        <td>8 Hours</td>
      </tr>
      <tr>
        <td><strong>Phase 6: Documentation & Artifacts</strong></td>
        <td>Research reports, ER diagrams, slide deck, user guides.</td>
        <td>4 Hours</td>
      </tr>
      <tr style="font-weight: 700; background: #EEF2FF;">
        <td colspan="2">Total Engineering Effort Estimate</td>
        <td>~50 Person-Hours</td>
      </tr>
    </tbody>
  </table>

  <!-- Section 9 -->
  <h2>9. Academic Presentation Slide Deck Outline (12 Slides)</h2>
  <div class="slides-grid">
    <div class="slide-card">
      <div class="slide-number">Slide 01</div>
      <div class="slide-title">Title & Team</div>
      <div class="slide-content">QueryMind 2.0: Voice-to-SQL Relational DBMS with Supabase Cloud Architecture.</div>
    </div>
    <div class="slide-card">
      <div class="slide-number">Slide 02</div>
      <div class="slide-title">Problem & Academic Focus</div>
      <div class="slide-content">Bridging conversational analytics with rigorous DBMS concepts: schema governance and query processing.</div>
    </div>
    <div class="slide-card">
      <div class="slide-number">Slide 03</div>
      <div class="slide-title">Repository Audit & Evolution</div>
      <div class="slide-content">Auditing v1.0 monolithic Flask/SQLite; preserving deterministic NLP while upgrading database and voice.</div>
    </div>
    <div class="slide-card">
      <div class="slide-number">Slide 04</div>
      <div class="slide-title">Speech-to-Text Comparison</div>
      <div class="slide-content">Evaluation matrix: Web Speech API vs Vosk vs Whisper vs Coqui; trade-offs in latency and privacy.</div>
    </div>
    <div class="slide-card">
      <div class="slide-number">Slide 05</div>
      <div class="slide-title">Hybrid Voice Architecture</div>
      <div class="slide-content">Browser Web Speech API primary tier with server-side Vosk fallback for cross-platform resilience.</div>
    </div>
    <div class="slide-card">
      <div class="slide-number">Slide 06</div>
      <div class="slide-title">Supabase Relational Schema</div>
      <div class="slide-content">Entity-Relationship design: students, subjects, marks, attendance with composite keys and constraints.</div>
    </div>
    <div class="slide-card">
      <div class="slide-number">Slide 07</div>
      <div class="slide-title">Row-Level Security (RLS)</div>
      <div class="slide-content">Database-level multi-tenancy: Student, Faculty, and Admin security policies via auth.uid().</div>
    </div>
    <div class="slide-card">
      <div class="slide-number">Slide 08</div>
      <div class="slide-title">Deterministic AST Governance</div>
      <div class="slide-content">SQLGlot validation pipeline: strict DDL/DML rejection, limit injection, and academic auditability.</div>
    </div>
    <div class="slide-card">
      <div class="slide-number">Slide 09</div>
      <div class="slide-title">Interactive Voice Workspace</div>
      <div class="slide-content">UI wireframe demonstration: audio capture &rarr; editable SQL inspection &rarr; execution &rarr; Chart.js graphs.</div>
    </div>
    <div class="slide-card">
      <div class="slide-number">Slide 10</div>
      <div class="slide-title">Implementation Loop Prompt</div>
      <div class="slide-content">Iterative test-driven development workflow with automated acceptance criteria at each step.</div>
    </div>
    <div class="slide-card">
      <div class="slide-number">Slide 11</div>
      <div class="slide-title">Testing & Security QA</div>
      <div class="slide-content">Full test suite results (49/49 passing); injection blocking, execution latency, and role access tests.</div>
    </div>
    <div class="slide-card">
      <div class="slide-number">Slide 12</div>
      <div class="slide-title">Conclusion & Future Work</div>
      <div class="slide-content">Summary of deliverables: enterprise Postgres migration, voice interface, and roadmap for LLM integration.</div>
    </div>
  </div>

  <!-- Section 10 -->
  <h2>10. References & Primary Sources</h2>
  <ol style="font-size: 8.8pt; line-height: 1.5;">
    <li><strong>Mozilla Developer Network (MDN):</strong> <em>Web Speech API Specification & SpeechRecognition Guide</em>, W3C Community Group.</li>
    <li><strong>Alpha Cephei:</strong> <em>Vosk Speech Recognition Toolkit & WebAssembly Runtime</em>, Apache 2.0 License, alphacephei.com/vosk.</li>
    <li><strong>OpenAI:</strong> <em>Robust Speech Recognition via Large-Scale Weak Supervision (Whisper)</em>, Radford et al., arXiv:2212.04356.</li>
    <li><strong>Supabase Documentation:</strong> <em>Row Level Security (RLS) Policies & Database Backup Architecture</em>, supabase.com/docs.</li>
    <li><strong>SQLGlot Repository:</strong> <em>Python SQL Parser, Transpiler, and AST Analysis Engine</em>, Toby Mao, github.com/tobymao/sqlglot.</li>
    <li><strong>OWASP Foundation:</strong> <em>SQL Injection Prevention Cheat Sheet & Defense in Depth Principles</em>, cheatcheet.owasp.org.</li>
  </ol>

</body>
</html>
"""

def generate_pdf_and_open():
    base_dir = r"C:\Users\Ganesh Nair\.gemini\antigravity-ide\scratch\ai_Dcds"
    artifact_dir = r"C:\Users\Ganesh Nair\.gemini\antigravity-ide\brain\ce23bf58-0646-40a8-abc6-df6feb410bfe"
    
    html_file = os.path.join(base_dir, "QueryMind_2_Voice_to_SQL_Supabase_Research_Report.html")
    pdf_file = os.path.join(base_dir, "QueryMind_2_Voice_to_SQL_Supabase_Research_Report.pdf")
    artifact_pdf = os.path.join(artifact_dir, "QueryMind_2_Voice_to_SQL_Supabase_Research_Report.pdf")
    
    # 1. Write HTML file
    print(f"Writing HTML report to {html_file}...")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
    
    # 2. Compile to PDF using Edge Headless
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(edge_path):
        edge_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    
    print(f"Compiling HTML to PDF using Edge: {edge_path}...")
    cmd = [
        edge_path,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_file}",
        html_file
    ]
    
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"Error compiling PDF: {proc.stderr}")
        return False
    
    if not os.path.exists(pdf_file) or os.path.getsize(pdf_file) == 0:
        print("PDF was not created or is empty.")
        return False
    
    pdf_size_kb = os.path.getsize(pdf_file) / 1024
    print(f"PDF generated successfully! Size: {pdf_size_kb:.1f} KB at {pdf_file}")
    
    # Copy to artifact directory
    try:
        shutil.copy2(pdf_file, artifact_pdf)
        print(f"Copied to artifact directory: {artifact_pdf}")
    except Exception as e:
        print(f"Note: Could not copy to artifact dir: {e}")
    
    # 3. Launch Adobe Acrobat
    acrobat_paths = [
        r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe",
        r"C:\Program Files (x86)\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
        r"C:\Program Files\Adobe\Acrobat Reader\AcroRd64.exe"
    ]
    
    launched = False
    for p in acrobat_paths:
        if os.path.exists(p):
            print(f"Launching Adobe Acrobat ({p}) with {pdf_file}...")
            try:
                subprocess.Popen([p, pdf_file])
                launched = True
                print("Adobe Acrobat launched successfully!")
                break
            except Exception as e:
                print(f"Failed to launch {p}: {e}")
    
    if not launched:
        print("Falling back to default system PDF viewer via os.startfile...")
        try:
            os.startfile(pdf_file)
            launched = True
        except Exception as e:
            print(f"os.startfile failed: {e}")
            
    return True

if __name__ == "__main__":
    success = generate_pdf_and_open()
    sys.exit(0 if success else 1)
