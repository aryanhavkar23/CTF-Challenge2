import os
import sys

# Ensure empty-dashboard is in Python path when executed from repository root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'empty-dashboard')))

from app import create_app

app = create_app()

if __name__ == '__main__':
    debug_mode = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Nexus Enterprise Analytics on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
