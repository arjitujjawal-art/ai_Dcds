"""
QueryMind 2.0 — Production Gunicorn Configuration
Optimized for concurrency, memory efficiency, and thread-safe SQLite operations.
"""

import os
import multiprocessing

# Port and Network Binding
port = os.environ.get("PORT", "5000")
bind = f"0.0.0.0:{port}"

# Worker & Thread Concurrency
# SQLite WAL mode is multi-reader thread safe; 2 workers with 4 threads per worker is optimal
workers = int(os.environ.get("WEB_CONCURRENCY", 2))
threads = int(os.environ.get("PYTHON_MAX_THREADS", 4))
worker_class = "gthread"

# Request Timeout (120s for neural text-to-speech generation & big joins)
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")

# Graceful restarts
graceful_timeout = 30
max_requests = 1000
max_requests_jitter = 50

# Preload app: False for SQLite connection isolation per worker
preload_app = False
