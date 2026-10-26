"""
QueryMind MongoDB Client
Handles query history, audit events, and feedback storage.
"""

import datetime
from flask import current_app
from pymongo import MongoClient, DESCENDING
from pymongo.errors import PyMongoError


def _db():
    """Return the MongoDB database object using app config."""
    cfg = current_app.config
    client = MongoClient(cfg["MONGO_URI"], serverSelectionTimeoutMS=3000)
    return client[cfg["MONGO_DB"]]


# ─── Query Logs ───────────────────────────────────────────────────────────────

def log_query(user_id, username, question, sql, status, execution_ms, row_count, error=None):
    """Insert a query-log document into MongoDB."""
    try:
        doc = {
            "user_id":       user_id,
            "username":      username,
            "question":      question,
            "generated_sql": sql,
            "status":        status,          # "success" | "validation_failed" | "db_error" | "no_match"
            "execution_time_ms": execution_ms,
            "result_row_count":  row_count,
            "error":         error,
            "timestamp":     datetime.datetime.utcnow(),
        }
        _db()["query_logs"].insert_one(doc)
    except PyMongoError:
        pass   # Logging failure must not crash the main request


def get_query_history(user_id=None, limit=50):
    """Retrieve query history, optionally filtered by user."""
    try:
        col = _db()["query_logs"]
        flt = {"user_id": user_id} if user_id else {}
        cursor = col.find(flt, {"_id": 0}).sort("timestamp", DESCENDING).limit(limit)
        return list(cursor)
    except PyMongoError:
        return []


def get_all_history(limit=200):
    """Admin view: all users' query history."""
    try:
        col = _db()["query_logs"]
        cursor = col.find({}, {"_id": 0}).sort("timestamp", DESCENDING).limit(limit)
        return list(cursor)
    except PyMongoError:
        return []


# ─── Audit Logs ───────────────────────────────────────────────────────────────

def log_audit(event_type, user_id=None, username=None, details=None):
    """Record a security or administrative event."""
    try:
        doc = {
            "event_type": event_type,   # e.g. "login", "logout", "validation_blocked"
            "user_id":    user_id,
            "username":   username,
            "details":    details,
            "timestamp":  datetime.datetime.utcnow(),
        }
        _db()["audit_logs"].insert_one(doc)
    except PyMongoError:
        pass


def get_audit_logs(limit=200):
    """Retrieve recent audit events (admin only)."""
    try:
        col = _db()["audit_logs"]
        cursor = col.find({}, {"_id": 0}).sort("timestamp", DESCENDING).limit(limit)
        return list(cursor)
    except PyMongoError:
        return []


# ─── Feedback ─────────────────────────────────────────────────────────────────

def save_feedback(user_id, question, sql, rating, comment=""):
    """Store user feedback about a query result."""
    try:
        doc = {
            "user_id":   user_id,
            "question":  question,
            "sql":       sql,
            "rating":    rating,        # "helpful" | "not_helpful"
            "comment":   comment,
            "timestamp": datetime.datetime.utcnow(),
        }
        _db()["query_feedback"].insert_one(doc)
        return True
    except PyMongoError:
        return False


def get_feedback(limit=100):
    """Admin: retrieve all feedback entries."""
    try:
        col = _db()["query_feedback"]
        cursor = col.find({}, {"_id": 0}).sort("timestamp", DESCENDING).limit(limit)
        return list(cursor)
    except PyMongoError:
        return []


# ─── Health Check ─────────────────────────────────────────────────────────────

def test_connection():
    """Return True if MongoDB is reachable."""
    try:
        _db().command("ping")
        return True
    except Exception:
        return False
