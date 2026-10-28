"""
QueryMind 2.0 — Production WSGI Entrypoint
Compatible with Gunicorn, Waitress, uWSGI, and cloud platforms (Render, Railway, Heroku, AWS).
"""

import os
from app import app

# Production application callable
application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
