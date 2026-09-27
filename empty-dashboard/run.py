import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Debug mode is explicitly disabled by default as per security requirements
    debug_mode = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
