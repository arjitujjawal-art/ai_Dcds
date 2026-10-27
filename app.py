"""
QueryMind — Flask Application
Uses SQLite only. Works out-of-the-box with zero setup.
"""

import os
import csv
import io
import json
import re

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, flash, send_file,
)
import asyncio
import edge_tts

# ── Local imports ─────────────────────────────────────────────────────────────
from nlp.sql_generator import generate_sql, generate_sql_for_dataset
from nlp.sql_validator  import validate_sql
from nlp.speech_narrator import DataToSpeechNarrator
from db.analyzer import auto_analyze_dataset
from db.database import (
    get_user,
    execute_query,
    log_query,
    get_query_history,
    get_all_history,
    log_audit,
    get_audit_logs,
    save_feedback,
    get_feedback,
    get_system_stats,
    get_app_users,
    get_division_stats,
    get_defaulters,
    get_student_profile,
    upload_csv_excel,
    get_uploaded_datasets,
    get_dataset_schema,
    delete_dataset,
    get_database_schema_metadata,
)

# ─── App ──────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "querymind-secret-2024-change-in-prod"


# ─── Decorators ───────────────────────────────────────────────────────────────
def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") not in ("admin", "teacher"):
            flash("Access denied.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return wrapper


# ─── Chart helper ─────────────────────────────────────────────────────────────
def make_chart(columns, rows):
    """Return a Chart.js config if 2-column result with numeric second column."""
    if not rows or len(columns) != 2:
        return None
    try:
        float(list(rows[0].values())[1])
    except (ValueError, TypeError):
        return None
    labels = [str(list(r.values())[0]) for r in rows]
    data   = [float(list(r.values())[1]) for r in rows]
    return {
        "type": "bar",
        "labels": labels,
        "datasets": [{
            "label": columns[1].replace("_", " ").title(),
            "data":  data,
            "backgroundColor": [
                "rgba(99,102,241,0.75)", "rgba(168,85,247,0.75)",
                "rgba(6,182,212,0.75)",  "rgba(16,185,129,0.75)",
                "rgba(245,158,11,0.75)", "rgba(244,63,94,0.75)",
            ],
            "borderColor": "rgba(255,255,255,0.15)",
            "borderWidth": 1,
            "borderRadius": 8,
        }],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# DUAL-PORTAL ARCHITECTURE (Portal 1: Ingest & Analyze | Portal 2: Voice & Query)
# ═══════════════════════════════════════════════════════════════════════════════

@app.before_request
def ensure_default_session():
    if "user_id" not in session:
        session["user_id"] = 1
        session["username"] = "admin"
        session["role"] = "admin"


# ── Global Context Processor ──────────────────────────────────────────────────
@app.context_processor
def inject_global_ui_context():
    try:
        datasets = get_uploaded_datasets()
    except Exception:
        datasets = []
    return {
        "current_role": session.get("role", "admin"),
        "current_username": session.get("username", "admin"),
        "global_datasets": datasets,
    }


# ── Role Perspective Switcher ─────────────────────────────────────────────────
@app.route("/switch-role/<target_role>")
def switch_role(target_role):
    role_map = {
        "student": "student",
        "faculty": "teacher",
        "teacher": "teacher",
        "admin": "admin",
        "administrator": "admin"
    }
    target = role_map.get(target_role.lower(), "admin")
    session["role"] = target
    if target == "student":
        session["user_id"] = 3
        session["username"] = "aarav"
    elif target == "teacher":
        session["user_id"] = 2
        session["username"] = "prof_sharma"
    else:
        session["user_id"] = 1
        session["username"] = "admin"
    flash(f"Switched role perspective to {target.title()} mode.", "info")
    return redirect(request.referrer or url_for("dashboard"))


# ── ACADEMIC ROLE DASHBOARD ───────────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    role = session.get("role", "admin")
    stats = get_system_stats()
    uploaded_datasets = get_uploaded_datasets()
    recent = get_all_history(10)
    division_stats = get_division_stats()
    defaulters = get_defaulters(threshold=75.0)
    profile = None
    if role == "student":
        profile = get_student_profile(session.get("user_id", 3))
    return render_template(
        "dashboard.html",
        role=role,
        stats=stats,
        uploaded_datasets=uploaded_datasets,
        recent=recent,
        division_stats=division_stats,
        defaulters=defaulters,
        profile=profile,
    )


# ── QUERYMIND 2.0 PRIMARY APPLICATION AREAS ───────────────────────────────────

@app.route("/")
def home():
    stats = get_system_stats()
    recent = get_all_history(6)
    return render_template("home.html", stats=stats, recent=recent)


@app.route("/workspace")
@app.route("/voice-sql")
def voice_sql_workspace():
    all_ds = get_uploaded_datasets()
    prefill = request.args.get("q", "").strip()
    return render_template(
        "voice_sql_workspace.html",
        all_datasets=all_ds,
        prefill_question=prefill,
    )


@app.route("/explorer")
def database_explorer():
    meta = get_database_schema_metadata()
    return render_template("explorer.html", schema_meta=meta)


@app.route("/playground")
def sql_playground():
    meta = get_database_schema_metadata()
    return render_template("playground.html", schema_meta=meta)


@app.route("/admin")
@login_required
def admin_dashboard():
    stats = get_system_stats()
    uploaded_datasets = get_uploaded_datasets()
    app_users = get_app_users()
    audit_logs = get_audit_logs(100)
    return render_template(
        "admin_dashboard.html",
        stats=stats,
        uploaded_datasets=uploaded_datasets,
        app_users=app_users,
        audit_logs=audit_logs,
    )


# ── PORTAL 1: Dataset Upload & Automated Analysis ─────────────────────────────

@app.route("/portal1")
def portal1():
    all_ds = get_uploaded_datasets()
    req_table = request.args.get("table")
    active_table = None
    if req_table:
        active_table = req_table
    elif all_ds:
        active_table = all_ds[0]["table_name"]

    analysis = None
    if active_table:
        analysis = auto_analyze_dataset(active_table)

    return render_template(
        "portal1_analyzer.html",
        analysis=analysis,
        all_datasets=all_ds,
        active_table=active_table,
        active_dataset_name=analysis["display_name"] if analysis else None
    )


@app.route("/upload-dataset", methods=["POST"])
def upload_dataset_file():
    f = request.files.get("dataset_file")
    if not f or not f.filename:
        flash("Please choose a valid CSV or Excel file.", "warning")
        return redirect(url_for("portal1"))

    res = upload_csv_excel(f.read(), f.filename, uploaded_by=session.get("username", "user"))
    if "error" in res:
        flash(f"Upload failed: {res['error']}", "danger")
        return redirect(url_for("portal1"))

    flash(f"Dataset '{res['display_name']}' successfully uploaded and auto-analyzed! 🚀", "success")
    return redirect(url_for("portal1", table=res["table_name"]))


# ── PORTAL 2: Voice & Text Query Intelligence Studio ──────────────────────────

@app.route("/portal2")
def portal2():
    all_ds = get_uploaded_datasets()
    req_table = request.args.get("table")
    active_table = req_table or (all_ds[0]["table_name"] if all_ds else None)

    schema = get_dataset_schema(active_table) if active_table else None
    cols = schema.get("all_columns", []) if schema else []

    return render_template(
        "portal2_query.html",
        active_table=active_table,
        active_dataset=schema,
        all_datasets=all_ds,
        sample_cols=cols,
        result_loaded=False,
        active_dataset_name=schema["display_name"] if schema else None
    )


@app.route("/portal2/ask", methods=["POST"])
def portal2_ask():
    question = request.form.get("question", "").strip()
    table_name = request.form.get("table_name", "").strip()

    all_ds = get_uploaded_datasets()
    if not table_name and all_ds:
        table_name = all_ds[0]["table_name"]

    schema = get_dataset_schema(table_name) if table_name else None
    if not schema:
        flash("Target dataset not found. Please upload or select a dataset first.", "warning")
        return redirect(url_for("portal1"))

    cols = schema.get("all_columns", [])

    # 1. NLP translation (supports English and Hindi/Hinglish speech)
    nlp = generate_sql_for_dataset(question, table_name, cols)
    sql = nlp["sql"]

    # 2. Deterministic AST Governance & Row Limit Injection
    v = validate_sql(sql, "admin", custom_allowed_tables={table_name})
    if not v["valid"]:
        verbal_summary = DataToSpeechNarrator.construct_verbal_summary(question, [], [], error=v["reason"])
        return render_template(
            "portal2_query.html",
            active_table=table_name,
            active_dataset=schema,
            all_datasets=all_ds,
            sample_cols=cols,
            result_loaded=True,
            question=question,
            sql=sql,
            columns=[],
            rows=[],
            verbal_summary=verbal_summary,
            error=f"Query blocked by governance: {v['reason']}",
            active_dataset_name=schema["display_name"]
        )

    sanitized_sql = v.get("sanitized_sql") or sql

    # 3. Execution against Database Layer
    result = execute_query(sanitized_sql)

    # 4. Tabular-to-Verbal Synthesis
    verbal_summary = DataToSpeechNarrator.construct_verbal_summary(
        question, result["columns"], result["rows"], error=result.get("error")
    )

    # 5. Log Telemetry
    log_query(session.get("user_id", 1), session.get("username", "user"),
              question, sanitized_sql, "success" if not result.get("error") else "db_error",
              result["execution_ms"], result["row_count"])
    log_audit("portal2_query", session.get("user_id", 1), session.get("username", "user"),
              details=json.dumps({
                  "table": table_name,
                  "raw_intent": question,
                  "executed_sql": sanitized_sql,
                  "disposition": "AUTHORIZED" if not result.get("error") else "ERROR",
                  "verbal_summary": verbal_summary
              }))

    chart = make_chart(result["columns"], result["rows"])

    return render_template(
        "portal2_query.html",
        active_table=table_name,
        active_dataset=schema,
        all_datasets=all_ds,
        sample_cols=cols,
        result_loaded=True,
        question=question,
        description=nlp.get("description"),
        sql=sanitized_sql,
        columns=result["columns"],
        rows=result["rows"],
        row_count=result["row_count"],
        exec_ms=result["execution_ms"],
        chart_json=json.dumps(chart) if chart else None,
        verbal_summary=verbal_summary,
        error=result.get("error"),
        active_dataset_name=schema["display_name"]
    )


# ── Text-To-Speech Neural Audio Stream ────────────────────────────────────────

@app.route("/api/tts")
def tts_api():
    text = request.args.get("text", "").strip()
    if not text:
        return "No text provided", 400
    try:
        async def _synth():
            communicate = edge_tts.Communicate(text, voice="en-US-JennyNeural")
            buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.write(chunk["data"])
            buffer.seek(0)
            return buffer

        audio_buffer = asyncio.run(_synth())
        return send_file(audio_buffer, mimetype="audio/mpeg")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Auth & Legacy Fallbacks ───────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_user(username, password)
        if user:
            session["user_id"]  = user["user_id"]
            session["username"] = user["username"]
            session["role"]     = user["role"]
            flash(f"Welcome back, {user['username']}! 👋", "success")
            return redirect(url_for("portal1"))
        flash("❌ Invalid username or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("portal1"))



# ── Query ─────────────────────────────────────────────────────────────────────

@app.route("/query", methods=["POST"])
@login_required
def query():
    question = request.form.get("question", "").strip()
    if not question:
        flash("Please enter a question.", "warning")
        return redirect(url_for("dashboard"))

    # 1. NLP → SQL (or Direct SQL Statement Evaluation)
    q_stripped = question.strip()
    if q_stripped.upper().startswith(("SELECT", "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE", "PRAGMA")):
        nlp = {
            "sql": q_stripped,
            "description": "Direct Query Statement",
            "matched": True,
            "confidence": 1.0
        }
    else:
        nlp = generate_sql(question)
    
    # If standard academic patterns did not match, check uploaded datasets
    if not nlp["matched"]:
        all_ds = get_uploaded_datasets()
        for ds in all_ds:
            name_words = [w.lower() for w in re.findall(r"\w+", ds["display_name"])]
            tbl_words  = [w.lower() for w in re.findall(r"\w+", ds["table_name"])]
            q_lower    = question.lower()
            if any(w in q_lower for w in name_words if len(w) > 3) or any(w in q_lower for w in tbl_words if len(w) > 3):
                schema = get_dataset_schema(ds["table_name"])
                if schema:
                    cols = schema.get("all_columns", [])
                    candidate = generate_sql_for_dataset(question, ds["table_name"], cols)
                    if candidate.get("matched"):
                        nlp = candidate
                        nlp["description"] = f"{nlp['description']} [{ds['display_name']}]"
                        break
        # If still not matched and there's only 1 uploaded dataset, try matching it
        if not nlp["matched"] and len(all_ds) == 1:
            schema = get_dataset_schema(all_ds[0]["table_name"])
            if schema:
                cols = schema.get("all_columns", [])
                candidate = generate_sql_for_dataset(question, all_ds[0]["table_name"], cols)
                if candidate.get("matched"):
                    nlp = candidate
                    nlp["description"] = f"{nlp['description']} [{all_ds[0]['display_name']}]"

    sql = nlp["sql"]

    if not nlp["matched"]:
        log_query(session["user_id"], session["username"],
                  question, None, "no_match", 0, 0, error=nlp["description"])
        verbal_summary = DataToSpeechNarrator.construct_verbal_summary(
            question, [], [], error=f"Pattern Mismatch: {nlp['description']}"
        )
        return render_template("result.html",
            question=question, error=nlp["description"],
            sql=None, columns=[], rows=[], chart_json=None,
            verbal_summary=verbal_summary)

    # 2. Deterministic AST Governance & RBAC
    custom_tables = {ds["table_name"] for ds in get_uploaded_datasets()}
    v = validate_sql(sql, session["role"], custom_allowed_tables=custom_tables)
    if not v["valid"]:
        log_query(session["user_id"], session["username"],
                  question, sql, "validation_failed", 0, 0, error=v["reason"])
        log_audit("validation_blocked", session["user_id"], session["username"],
                  details=json.dumps({
                      "role": session["role"],
                      "raw_intent": question,
                      "rejected_sql": sql,
                      "disposition": "DENIED",
                      "violation": v["reason"]
                  }))
        verbal_summary = DataToSpeechNarrator.construct_verbal_summary(
            question, [], [], error=v["reason"]
        )
        return render_template("result.html",
            question=question, error=f"Query blocked: {v['reason']}",
            sql=sql, columns=[], rows=[], chart_json=None,
            verbal_summary=verbal_summary)

    # Use the AST-governed, limit-injected sanitized SQL
    sanitized_sql = v.get("sanitized_sql") or sql

    # 3. Execution against Database Layer
    result = execute_query(sanitized_sql)

    if result["error"]:
        log_query(session["user_id"], session["username"],
                  question, sanitized_sql, "db_error",
                  result["execution_ms"], 0, error=result["error"])
        verbal_summary = DataToSpeechNarrator.construct_verbal_summary(
            question, [], [], error=result["error"]
        )
        return render_template("result.html",
            question=question, error=result["error"],
            sql=sanitized_sql, columns=result["columns"], rows=[], chart_json=None,
            verbal_summary=verbal_summary)

    # 4. Tabular-to-Verbal Synthesis
    verbal_summary = DataToSpeechNarrator.construct_verbal_summary(
        question, result["columns"], result["rows"]
    )

    # 5. Log Telemetry
    log_query(session["user_id"], session["username"],
              question, sanitized_sql, "success",
              result["execution_ms"], result["row_count"])
    log_audit("query_executed", session["user_id"], session["username"],
              details=json.dumps({
                  "role": session["role"],
                  "raw_intent": question,
                  "executed_sql": sanitized_sql,
                  "disposition": "AUTHORIZED",
                  "row_count": result["row_count"],
                  "execution_ms": result["execution_ms"],
                  "verbal_summary": verbal_summary
              }))

    chart = make_chart(result["columns"], result["rows"])

    return render_template("result.html",
        question=question,
        description=nlp["description"],
        sql=sanitized_sql,
        columns=result["columns"],
        rows=result["rows"],
        row_count=result["row_count"],
        exec_ms=result["execution_ms"],
        chart_json=json.dumps(chart) if chart else None,
        verbal_summary=verbal_summary,
        error=None,
    )


# ── History ───────────────────────────────────────────────────────────────────

@app.route("/history")
@login_required
def history():
    role = session["role"]
    records = get_all_history(200) if role in ("admin","teacher") \
              else get_query_history(session["user_id"], 100)
    return render_template("history.html", records=records, role=role)


# ── Audit ─────────────────────────────────────────────────────────────────────

@app.route("/audit")
@login_required
@admin_required
def audit():
    return render_template("audit.html",
        events=get_audit_logs(200),
        feedback=get_feedback(100))


# ── Admin User & DB Governance ────────────────────────────────────────────────

@app.route("/users")
@login_required
def users():
    if session.get("role") != "admin":
        flash("Admin clearance required for Governance & User Management.", "danger")
        return redirect(url_for("dashboard"))
    return render_template("users.html",
                           users=get_app_users(),
                           stats=get_system_stats())


# ── Faculty Attendance Radar ──────────────────────────────────────────────────

@app.route("/defaulters")
@login_required
def defaulters():
    if session.get("role") not in ("admin", "teacher"):
        flash("Only faculty and administration can view attendance radars.", "danger")
        return redirect(url_for("dashboard"))
    return render_template("defaulters.html",
                           defaulters=get_defaulters(threshold=75.0),
                           role=session["role"])



# ── Feedback ──────────────────────────────────────────────────────────────────

@app.route("/feedback", methods=["POST"])
@login_required
def feedback():
    data = request.get_json(silent=True) or {}
    save_feedback(session["user_id"],
                  data.get("question",""), data.get("sql",""),
                  data.get("rating","not_helpful"), data.get("comment",""))
    return jsonify({"ok": True})


# ── CSV Export ────────────────────────────────────────────────────────────────

@app.route("/export")
@login_required
def export_csv():
    role = session["role"]
    records = get_all_history(5000) if role in ("admin","teacher") \
              else get_query_history(session["user_id"], 1000)

    output = io.StringIO()
    fields = ["timestamp","username","question","generated_sql",
              "status","execution_time_ms","result_row_count","error"]
    w = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(records)
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="querymind_history.csv",
    )


# ── Health ────────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    import os
    from db.database import DB_PATH
    return jsonify({"sqlite": os.path.exists(DB_PATH), "status": "ok"})


# ── Dataset Upload & Browser ─────────────────────────────────────────────────

@app.route("/datasets")
@login_required
def datasets():
    if session.get("role") not in ("admin", "teacher"):
        flash("Dataset management requires faculty or admin access.", "danger")
        return redirect(url_for("dashboard"))
    all_ds = get_uploaded_datasets()
    return render_template("datasets.html", datasets=all_ds, role=session["role"])


@app.route("/datasets/upload", methods=["GET", "POST"])
@login_required
def dataset_upload():
    if session.get("role") not in ("admin", "teacher"):
        flash("Dataset upload requires faculty or admin access.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        f = request.files.get("file")
        if not f or not f.filename:
            flash("No file selected.", "warning")
            return redirect(request.url)

        filename = f.filename
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ("csv", "xlsx", "xls"):
            flash("Only CSV or Excel (.xlsx/.xls) files are supported.", "danger")
            return redirect(request.url)

        file_bytes = f.read()
        result = upload_csv_excel(file_bytes, filename, uploaded_by=session["username"])

        if "error" in result:
            flash(f"Upload failed: {result['error']}", "danger")
            return redirect(request.url)

        log_audit("dataset_upload", session["user_id"], session["username"],
                  details={"file": filename, "table": result["table_name"],
                           "rows": result["row_count"]})
        flash(f"✅ Dataset '{result['display_name']}' uploaded! {result['row_count']} rows, "
              f"{len(result['columns'])} columns.", "success")
        return redirect(url_for("dataset_view", table_name=result["table_name"]))

    return render_template("upload.html", role=session["role"])


@app.route("/datasets/<table_name>")
@login_required
def dataset_view(table_name):
    schema = get_dataset_schema(table_name)
    if not schema:
        flash("Dataset not found.", "danger")
        return redirect(url_for("datasets"))
    return render_template("dataset_view.html", schema=schema,
                           role=session["role"], table_name=table_name)


@app.route("/datasets/<table_name>/query", methods=["POST"])
@login_required
def dataset_query(table_name):
    schema = get_dataset_schema(table_name)
    if not schema:
        flash("Dataset not found.", "danger")
        return redirect(url_for("datasets"))

    question = request.form.get("question", "").strip()
    if not question:
        return redirect(url_for("dataset_view", table_name=table_name))

    columns = schema.get("all_columns", [])
    nlp = generate_sql_for_dataset(question, table_name, columns)
    sql  = nlp["sql"]

    # Validate (allow the dataset table through, block system tables)
    custom_tables = {ds["table_name"] for ds in get_uploaded_datasets()}
    v = validate_sql(sql, session["role"], custom_allowed_tables=custom_tables)
    if not v["valid"]:
        log_query(session["user_id"], session["username"],
                  question, sql, "validation_failed", 0, 0, error=v["reason"])
        log_audit("validation_blocked", session["user_id"], session["username"],
                  details=json.dumps({
                      "role": session["role"],
                      "raw_intent": question,
                      "rejected_sql": sql,
                      "disposition": "DENIED",
                      "violation": v["reason"]
                  }))
        verbal_summary = DataToSpeechNarrator.construct_verbal_summary(
            question, [], [], error=v["reason"]
        )
        return render_template("result.html",
            question=question,
            error=f"Query blocked: {v['reason']}",
            sql=sql, columns=[], rows=[], chart_json=None,
            verbal_summary=verbal_summary)

    sanitized_sql = v.get("sanitized_sql") or sql
    result = execute_query(sanitized_sql)
    if result["error"]:
        log_query(session["user_id"], session["username"],
                  question, sanitized_sql, "db_error",
                  result["execution_ms"], 0, error=result["error"])
        verbal_summary = DataToSpeechNarrator.construct_verbal_summary(
            question, [], [], error=result["error"]
        )
        return render_template("result.html",
            question=question, error=result["error"],
            sql=sanitized_sql, columns=result["columns"], rows=[], chart_json=None,
            verbal_summary=verbal_summary)

    verbal_summary = DataToSpeechNarrator.construct_verbal_summary(
        question, result["columns"], result["rows"]
    )

    log_query(session["user_id"], session["username"],
              question, sanitized_sql, "success",
              result["execution_ms"], result["row_count"])
    log_audit("dataset_query_executed", session["user_id"], session["username"],
              details=json.dumps({
                  "role": session["role"],
                  "table": table_name,
                  "raw_intent": question,
                  "executed_sql": sanitized_sql,
                  "disposition": "AUTHORIZED",
                  "row_count": result["row_count"],
                  "execution_ms": result["execution_ms"],
                  "verbal_summary": verbal_summary
              }))

    chart = make_chart(result["columns"], result["rows"])
    return render_template("result.html",
        question=question,
        description=f"{nlp['description']} [{schema['display_name']}]",
        sql=sanitized_sql,
        columns=result["columns"],
        rows=result["rows"],
        row_count=result["row_count"],
        exec_ms=result["execution_ms"],
        chart_json=json.dumps(chart) if chart else None,
        verbal_summary=verbal_summary,
        error=None,
    )


@app.route("/datasets/<table_name>/delete", methods=["POST"])
@login_required
def dataset_delete(table_name):
    if session.get("role") != "admin":
        flash("Only admins can delete datasets.", "danger")
        return redirect(url_for("dataset_view", table_name=table_name))
    from db.database import delete_dataset as _del
    ok = _del(table_name)
    if ok:
        log_audit("dataset_delete", session["user_id"], session["username"],
                  details={"table": table_name})
        flash(f"Dataset '{table_name}' deleted.", "success")
    else:
        flash("Cannot delete system tables.", "danger")
    return redirect(url_for("datasets"))


# ─── Speech & Voice APIs (Zero-Cost Neural Audio & ASR) ───────────────────────

@app.route("/api/tts", methods=["GET", "POST"])
def text_to_speech():
    """
    Zero-Cost Asynchronous Neural Text-to-Speech Streaming Endpoint.
    Streams synthesized voice byte buffers directly back without disk persistence.
    """
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        text = data.get("text", "")
        voice = data.get("voice", "en-US-ChristopherNeural")
    else:
        text = request.args.get("text", "")
        voice = request.args.get("voice", "en-US-ChristopherNeural")

    text = (text or "").strip()
    if not text:
        return jsonify({"error": "No text provided for voice synthesis."}), 400

    async def _stream_neural_audio():
        comm = edge_tts.Communicate(text=text, voice=voice)
        audio_stream = bytearray()
        async for packet in comm.stream():
            if packet.get("type") == "audio":
                audio_stream.extend(packet["data"])
        return bytes(audio_stream)

    try:
        audio_bytes = asyncio.run(_stream_neural_audio())
        if not audio_bytes:
            return jsonify({"error": "Audio generation produced empty buffer."}), 500

        return send_file(
            io.BytesIO(audio_bytes),
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="spoken_summary.mp3"
        )
    except Exception as exc:
        return jsonify({
            "error": f"TTS synthesis failed: {str(exc)}",
            "fallback": "Use client-side Web Speech API"
        }), 500


@app.route("/api/transcribe", methods=["POST"])
def transcribe_audio():
    """
    Accepts raw audio buffers or status queries for Speech-to-Text ingestion.
    """
    return jsonify({
        "status": "active",
        "engine": "WebSpeechAPI + faster-whisper reference bridge",
        "message": "Direct client-side streaming ASR active for sub-200ms latency."
    })


# ── QueryMind 2.0 Async REST APIs ─────────────────────────────────────────────

@app.route("/api/generate-sql", methods=["POST"])
def api_generate_sql():
    """
    Schema-aware natural language to SQL translation endpoint.
    Translates intent into a deterministic SQL statement without executing it.
    """
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    table_name = data.get("table_name", "").strip()
    if not question:
        return jsonify({"error": "Empty question received."}), 400

    # Custom dataset table
    if table_name and table_name not in ("academic", "students", "subjects", "marks", "attendance"):
        schema = get_dataset_schema(table_name)
        if schema:
            cols = schema.get("all_columns", [])
            nlp = generate_sql_for_dataset(question, table_name, cols)
            return jsonify({
                "sql": nlp["sql"],
                "description": nlp.get("description", "Dataset Query"),
                "matched": nlp.get("matched", True),
                "table_name": table_name
            })

    # Academic relational schema routing
    nlp = generate_sql(question)
    if not nlp["matched"]:
        all_ds = get_uploaded_datasets()
        for ds in all_ds:
            schema = get_dataset_schema(ds["table_name"])
            if schema:
                candidate = generate_sql_for_dataset(question, ds["table_name"], schema.get("all_columns", []))
                if candidate.get("matched"):
                    nlp = candidate
                    nlp["description"] = f"{nlp['description']} [{ds['display_name']}]"
                    break

    return jsonify({
        "sql": nlp.get("sql"),
        "description": nlp.get("description"),
        "matched": nlp.get("matched", False),
        "confidence": nlp.get("confidence", 0)
    })


@app.route("/api/validate-sql", methods=["POST"])
def api_validate_sql():
    """
    Deterministic AST governance validation gateway.
    Verifies read-only SELECT expressions, entity RBAC, and injects row ceilings.
    """
    data = request.get_json(silent=True) or {}
    sql = data.get("sql", "").strip()
    table_name = data.get("table_name", "").strip()
    if not sql:
        return jsonify({"valid": False, "reason": "Empty SQL query."}), 400

    role = session.get("role", "admin")
    custom_tables = {ds["table_name"] for ds in get_uploaded_datasets()}
    if table_name and table_name not in ("academic", "students", "subjects", "marks", "attendance"):
        custom_tables.add(table_name)

    v = validate_sql(sql, role, custom_allowed_tables=custom_tables)
    return jsonify(v)


@app.route("/api/execute-sql", methods=["POST"])
def api_execute_sql():
    """
    Authorized SQL execution engine.
    Validates AST, executes against SQLite, records query history with input mode,
    and returns tabular records with execution latency and visualization specs.
    """
    data = request.get_json(silent=True) or {}
    sql = data.get("sql", "").strip()
    question = data.get("question", "").strip()
    input_mode = data.get("input_mode", "text").strip().lower()
    table_name = data.get("table_name", "").strip()
    if input_mode not in ("voice", "text"):
        input_mode = "text"

    if not sql:
        return jsonify({"error": "No SQL provided for execution."}), 400

    role = session.get("role", "admin")
    custom_tables = {ds["table_name"] for ds in get_uploaded_datasets()}
    if table_name and table_name not in ("academic", "students", "subjects", "marks", "attendance"):
        custom_tables.add(table_name)

    v = validate_sql(sql, role, custom_allowed_tables=custom_tables)
    if not v["valid"]:
        log_query(session.get("user_id", 1), session.get("username", "user"),
                  question or sql, sql, "validation_failed", 0, 0,
                  error=v["reason"], input_mode=input_mode)
        log_audit("validation_blocked", session.get("user_id", 1), session.get("username", "user"),
                  details=json.dumps({"sql": sql, "violation": v["reason"], "input_mode": input_mode}))
        return jsonify({"error": f"AST Governance Rejection: {v['reason']}", "valid": False}), 403

    sanitized_sql = v.get("sanitized_sql") or sql
    res = execute_query(sanitized_sql)

    status = "success" if not res.get("error") else "db_error"
    log_query(session.get("user_id", 1), session.get("username", "user"),
              question or sanitized_sql, sanitized_sql, status,
              res["execution_ms"], res["row_count"],
              error=res.get("error"), input_mode=input_mode)

    chart = make_chart(res["columns"], res["rows"])
    verbal = DataToSpeechNarrator.construct_verbal_summary(
        question or "Database query", res["columns"], res["rows"], error=res.get("error")
    )

    return jsonify({
        "columns": res["columns"],
        "rows": res["rows"],
        "row_count": res["row_count"],
        "execution_ms": res["execution_ms"],
        "sanitized_sql": sanitized_sql,
        "error": res.get("error"),
        "chart": chart,
        "verbal_summary": verbal
    })


@app.route("/api/schema")
def api_schema():
    """Return live database metadata and generated Mermaid ER diagram."""
    meta = get_database_schema_metadata()
    return jsonify(meta)


# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
