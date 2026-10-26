"""
QueryMind Dataset Auto-Analyzer Engine
Inspects, parses, and automatically analyzes any uploaded tabular dataset (CSV / Excel).
Computes column schemas, missing value profiles, descriptive statistics,
distribution metrics, and auto-generates visual chart configurations.
"""

import sqlite3
import json
import os
import re
import pandas as pd
import numpy as np

DB_PATH = os.path.join(os.path.dirname(__file__), "querymind.db")


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def auto_analyze_dataset(table_name: str) -> dict | None:
    """
    Performs comprehensive automated statistical and structural analysis
    on any dataset table in SQLite.
    """
    conn = _conn()
    reg = conn.execute(
        "SELECT * FROM dataset_registry WHERE table_name = ?", (table_name,)
    ).fetchone()
    
    if not reg:
        # Check if table exists in sqlite_master anyway
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (table_name,)
        ).fetchone()
        if not exists:
            conn.close()
            return None
        display_name = table_name.replace("_", " ").title()
    else:
        display_name = reg["display_name"]

    try:
        raw_conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', raw_conn)
        raw_conn.close()
    except Exception as exc:
        conn.close()
        return {"error": f"Failed to read table: {str(exc)}"}

    total_rows = len(df)
    total_cols = len(df.columns)
    missing_cells = int(df.isna().sum().sum())
    missing_pct = round((missing_cells / (total_rows * total_cols) * 100), 2) if total_rows * total_cols > 0 else 0
    duplicate_rows = int(df.duplicated().sum())

    columns_analysis = []
    numeric_columns = []
    categorical_columns = []

    for col in df.columns:
        series = df[col]
        non_null_count = int(series.count())
        col_missing = int(series.isna().sum())
        col_missing_pct = round((col_missing / total_rows * 100), 1) if total_rows > 0 else 0
        unique_vals = int(series.nunique())

        is_numeric = pd.api.types.is_numeric_dtype(series)

        col_stat = {
            "name": col,
            "display_name": col.replace("_", " ").title(),
            "dtype": "Numeric" if is_numeric else "Text / Categorical",
            "is_numeric": is_numeric,
            "non_null_count": non_null_count,
            "missing_count": col_missing,
            "missing_pct": col_missing_pct,
            "unique_count": unique_vals,
        }

        if is_numeric and non_null_count > 0:
            numeric_columns.append(col)
            valid_nums = series.dropna()
            col_stat["min"] = round(float(valid_nums.min()), 2)
            col_stat["max"] = round(float(valid_nums.max()), 2)
            col_stat["mean"] = round(float(valid_nums.mean()), 2)
            col_stat["median"] = round(float(valid_nums.median()), 2)
            col_stat["sum"] = round(float(valid_nums.sum()), 2)
        else:
            categorical_columns.append(col)
            # Top categories
            top_counts = series.value_counts().head(5).to_dict()
            col_stat["top_values"] = [{"val": str(k), "count": int(v)} for k, v in top_counts.items()]

        columns_analysis.append(col_stat)

    # ── Automated Chart Recommendation ───────────────────────────────────────
    chart_recommendation = None
    if categorical_columns and numeric_columns:
        # Prefer meaningful category over high-cardinality unique names
        cat = None
        for c in categorical_columns:
            if df[c].nunique() < total_rows:
                cat = c
                break
        cat = cat or categorical_columns[0]

        # Prefer non-ID numeric columns
        num_candidates = [c for c in numeric_columns if not c.lower().endswith("id")]
        num = num_candidates[0] if num_candidates else numeric_columns[0]

        grouped = df.groupby(cat)[num].mean().sort_values(ascending=False).head(10)
        chart_recommendation = {
            "title": f"Average {num.replace('_', ' ').title()} by {cat.replace('_', ' ').title()}",
            "type": "bar",
            "labels": [str(x) for x in grouped.index.tolist()],
            "data": [round(float(x), 2) for x in grouped.values.tolist()],
            "x_label": cat.replace('_', ' ').title(),
            "y_label": f"Average {num.replace('_', ' ').title()}"
        }
    elif numeric_columns:
        num = numeric_columns[0]
        sample_s = df[num].dropna().head(15)
        chart_recommendation = {
            "title": f"{num.replace('_', ' ').title()} Distribution (Sample)",
            "type": "line",
            "labels": [f"Row {i+1}" for i in range(len(sample_s))],
            "data": [round(float(x), 2) for x in sample_s.tolist()],
            "x_label": "Records",
            "y_label": num.replace('_', ' ').title()
        }
    elif categorical_columns:
        cat = categorical_columns[0]
        counts = df[cat].value_counts().head(8)
        chart_recommendation = {
            "title": f"Count Distribution by {cat.replace('_', ' ').title()}",
            "type": "doughnut",
            "labels": [str(x) for x in counts.index.tolist()],
            "data": [int(x) for x in counts.values.tolist()],
            "x_label": cat.replace('_', ' ').title(),
            "y_label": "Frequency"
        }

    # First 25 preview records
    preview_df = df.head(25).fillna("—")
    preview_rows = preview_df.to_dict(orient="records")

    conn.close()

    return {
        "table_name": table_name,
        "display_name": display_name,
        "total_rows": total_rows,
        "total_cols": total_cols,
        "missing_cells": missing_cells,
        "missing_pct": missing_pct,
        "duplicate_rows": duplicate_rows,
        "columns": list(df.columns),
        "columns_analysis": columns_analysis,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "chart": chart_recommendation,
        "preview_rows": preview_rows,
    }
