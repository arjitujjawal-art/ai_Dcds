"""
QueryMind 2.0 – Dual-Engine Database Adapter (Supabase PostgreSQL + SQLite Fallback)
Enables seamless execution against Supabase cloud instances while preserving
local SQLite zero-config development and continuous integration testing.
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("querymind.db.adapter")

class DatabaseAdapter:
    """
    Unified Database Adapter supporting both Supabase (PostgreSQL) and SQLite.
    Automatically detects environment variables and routes queries safely.
    """
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "").strip()
        self.supabase_key = os.getenv("SUPABASE_KEY", "").strip()
        self.postgres_dsn = os.getenv("DATABASE_URL", "").strip()
        self.use_supabase = bool(self.supabase_url and self.supabase_key) or bool(self.postgres_dsn)
        self._supabase_client = None
        self._pg_conn = None
        
        if self.use_supabase:
            self._init_supabase()
        else:
            logger.info("Supabase credentials not detected; running on SQLite unified engine.")

    def _init_supabase(self):
        """Initialize Supabase client or Postgres connection pool if available."""
        try:
            from supabase import create_client
            self._supabase_client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Successfully initialized Supabase Client.")
        except Exception as e:
            logger.warning(f"Could not initialize supabase-py client ({e}). Checking psycopg2...")
            try:
                import psycopg2
                if self.postgres_dsn:
                    self._pg_conn = psycopg2.connect(self.postgres_dsn)
                    logger.info("Successfully connected to Postgres directly via psycopg2.")
            except Exception as pe:
                logger.warning(f"Direct Postgres connection unavailable ({pe}). Falling back to SQLite.")
                self.use_supabase = False

    @property
    def backend_name(self) -> str:
        """Return the active database engine name."""
        if self.use_supabase:
            return "Supabase PostgreSQL (Cloud)"
        return "SQLite (Local Unified)"

    def is_cloud_enabled(self) -> bool:
        """Check if cloud Supabase instance is active."""
        return self.use_supabase

    def execute_query(self, sql: str, params: Optional[Tuple] = None, input_mode: str = "text") -> Dict[str, Any]:
        """
        Execute a SELECT SQL query against the active database engine.
        Returns a dict with 'columns', 'rows', 'row_count', 'exec_time_ms', and 'engine'.
        """
        start_time = time.perf_counter()
        
        # 1. Cloud Supabase Postgres Execution
        if self.use_supabase and self._pg_conn:
            try:
                with self._pg_conn.cursor() as cur:
                    cur.execute(sql, params or ())
                    columns = [desc[0] for desc in cur.description] if cur.description else []
                    rows = cur.fetchall()
                    rows_as_dicts = [dict(zip(columns, r)) for r in rows]
                    
                exec_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return {
                    "columns": columns,
                    "rows": rows_as_dicts,
                    "row_count": len(rows_as_dicts),
                    "exec_time_ms": exec_time_ms,
                    "engine": self.backend_name,
                    "input_mode": input_mode,
                    "status": "success"
                }
            except Exception as e:
                logger.error(f"Postgres execution failed: {e}. Falling back to SQLite.")

        # 2. Local SQLite Engine Execution
        import db.database as db
        conn = db._conn()
        try:
            cur = conn.cursor()
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            
            columns = [desc[0] for desc in cur.description] if cur.description else []
            rows = cur.fetchall()
            rows_as_dicts = [dict(r) for r in rows]
            
            exec_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            
            return {
                "columns": columns,
                "rows": rows_as_dicts,
                "row_count": len(rows_as_dicts),
                "exec_time_ms": exec_time_ms,
                "engine": self.backend_name,
                "input_mode": input_mode,
                "status": "success"
            }
        finally:
            conn.close()

    def get_catalog_metadata(self) -> Dict[str, Any]:
        """Retrieve live table schema catalog and dynamic ER diagram."""
        import db.database as db
        meta = db.get_database_schema_metadata()
        return {
            "engine": self.backend_name,
            "tables": meta.get("tables", {}),
            "relationships": meta.get("relationships", []),
            "mermaid": meta.get("er_mermaid", "")
        }

# Global singleton adapter instance
db_adapter = DatabaseAdapter()
