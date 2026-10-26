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

# ── Local imports ─────────────────────────────────────────────────────────────
from nlp.sql_generator import generate_sql, generate_sql_for_dataset
from nlp.sql_validator  import validate_sql
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
    execute_query,
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
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def root():
    return redirect(url_for("dashboard") if "user_id" in session else url_for("login"))


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = get_user(username, password)
        if user:
            session["user_id"]  = user["user_id"]
            session["username"] = user["username"]
            session["role"]     = user["role"]
            log_audit("login", user["user_id"], user["username"])
            flash(f"Welcome back, {user['username']}! 👋", "success")
            return redirect(url_for("dashboard"))

        flash("❌ Invalid username or password.", "danger")
        log_audit("login_failed", details={"username": username})

    return render_template("login.html")


@app.route("/logout")
def logout():
    log_audit("logout", session.get("user_id"), session.get("username"))
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    role = session["role"]
    recent = get_query_history(session["user_id"], limit=5)
    
    stats = None
    app_users = None
    div_stats = None
    defaulters = None
    profile = None
    uploaded_datasets = None

    if role in ("admin", "teacher"):
        uploaded_datasets = get_uploaded_datasets()

    if role == "admin":
        stats = get_system_stats()
        app_users = get_app_users()
        recent = get_all_history(limit=6)
    elif role == "teacher":
        div_stats = get_division_stats()
        defaulters = get_defaulters(threshold=75.0)
    else:
        profile = get_student_profile(session.get("username", "student1"))

    return render_template(
        "dashboard.html",
        username=session["username"],
        role=role,
        recent=recent,
        stats=stats,
        app_users=app_users,
        div_stats=div_stats,
        defaulters=defaulters,
        profile=profile,
        uploaded_datasets=uploaded_datasets,
    )



# ── Query ─────────────────────────────────────────────────────────────────────

@app.route("/query", methods=["POST"])
@login_required
def query():
    question = request.form.get("question", "").strip()
    if not question:
        flash("Please enter a question.", "warning")
        return redirect(url_for("dashboard"))

    # 1. NLP → SQL
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
        return render_template("result.html",
            question=question, error=nlp["description"],
            sql=None, columns=[], rows=[], chart_json=None)

    # 2. Validate
    v = validate_sql(sql, session["role"])
    if not v["valid"]:
        log_query(session["user_id"], session["username"],
                  question, sql, "validation_failed", 0, 0, error=v["reason"])
        return render_template("result.html",
            question=question, error=f"Query blocked: {v['reason']}",
            sql=sql, columns=[], rows=[], chart_json=None)

    # 3. Execute
    result = execute_query(sql)

    if result["error"]:
        log_query(session["user_id"], session["username"],
                  question, sql, "db_error",
                  result["execution_ms"], 0, error=result["error"])
        return render_template("result.html",
            question=question, error=result["error"],
            sql=sql, columns=result["columns"], rows=[], chart_json=None)

    # 4. Log success
    log_query(session["user_id"], session["username"],
              question, sql, "success",
              result["execution_ms"], result["row_count"])

    chart = make_chart(result["columns"], result["rows"])

    return render_template("result.html",
        question=question,
        description=nlp["description"],
        sql=sql,
        columns=result["columns"],
        rows=result["rows"],
        row_count=result["row_count"],
        exec_ms=result["execution_ms"],
        chart_json=json.dumps(chart) if chart else None,
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
    v = validate_sql(sql, session["role"])
    if not v["valid"]:
        log_query(session["user_id"], session["username"],
                  question, sql, "validation_failed", 0, 0, error=v["reason"])
        return render_template("result.html",
            question=question,
            error=f"Query blocked: {v['reason']}",
            sql=sql, columns=[], rows=[], chart_json=None)

    result = execute_query(sql)
    if result["error"]:
        log_query(session["user_id"], session["username"],
                  question, sql, "db_error",
                  result["execution_ms"], 0, error=result["error"])
        return render_template("result.html",
            question=question, error=result["error"],
            sql=sql, columns=result["columns"], rows=[], chart_json=None)

    log_query(session["user_id"], session["username"],
              question, sql, "success",
              result["execution_ms"], result["row_count"])

    chart = make_chart(result["columns"], result["rows"])
    return render_template("result.html",
        question=question,
        description=f"{nlp['description']} [{schema['display_name']}]",
        sql=sql,
        columns=result["columns"],
        rows=result["rows"],
        row_count=result["row_count"],
        exec_ms=result["execution_ms"],
        chart_json=json.dumps(chart) if chart else None,
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


# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
