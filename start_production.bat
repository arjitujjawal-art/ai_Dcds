@echo off
echo ==========================================================
echo  Starting QueryMind 2.0 DBMS Production Server
echo ==========================================================

python check_deployment.py
if %errorlevel% neq 0 (
    echo [ERROR] Pre-flight deployment audit failed!
    exit /b %errorlevel%
)

echo [OK] Launching QueryMind 2.0 on http://127.0.0.1:5000
python wsgi.py
