#!/usr/bin/env bash
set -e

echo "=========================================================="
echo " Starting QueryMind 2.0 DBMS Production Server"
echo "=========================================================="

# 1. Run automated pre-flight audit
python check_deployment.py

# 2. Launch production WSGI server
PORT=${PORT:-5000}
echo "Launching Gunicorn multi-worker WSGI server on port $PORT..."
exec gunicorn --config gunicorn_config.py wsgi:app
