import os
from flask import Flask, Response, render_template, request, jsonify
from app.config import Config
from app.database import close_db, init_db

def create_app(test_config=None):
    """Application factory for the Enterprise Analytics Portal."""
    app = Flask(__name__, instance_relative_config=False)
    
    # Load configuration
    app.config.from_object(Config)
    if test_config is not None:
        app.config.update(test_config)

    # Register database teardown hook
    app.teardown_appcontext(close_db)

    # Initialize database tables and default seed data
    init_db(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.reports import reports_bp
    from app.routes.api import api_bp
    from app.routes.export import export_bp
    from app.routes.internal import internal_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(internal_bp)

    # Standalone routes
    @app.route('/robots.txt')
    def robots_txt():
        content = "User-agent: *\nDisallow: /api/\nDisallow: /export\n"
        return Response(content, mimetype="text/plain")

    # Custom error handlers to prevent information leakage and stack traces
    @app.errorhandler(400)
    def bad_request(error):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Bad Request", "message": str(error.description if hasattr(error, 'description') else "Invalid request parameters")}), 400
        return render_template('error.html', code=400, title="Bad Request", message="The request could not be processed due to invalid syntax or parameters."), 400

    @app.errorhandler(401)
    def unauthorized(error):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Unauthorized", "message": "Authentication required to access this resource"}), 401
        return render_template('error.html', code=401, title="Authentication Required", message="Your session has expired or you do not have permission to view this resource."), 401

    @app.errorhandler(403)
    def forbidden(error):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Forbidden", "message": "Access denied"}), 403
        return render_template('error.html', code=403, title="Forbidden", message="You do not possess the required authorization level for this resource."), 403

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Not Found", "message": "Requested endpoint or resource not found"}), 404
        return render_template('error.html', code=404, title="Page Not Found", message="The requested report, dashboard view, or resource does not exist."), 404

    @app.errorhandler(500)
    def internal_error(error):
        # Stack traces are never exposed to clients
        if request.path.startswith('/api/'):
            return jsonify({"error": "Internal Server Error", "message": "An internal operational error occurred."}), 500
        return render_template('error.html', code=500, title="Internal Server Error", message="An unexpected error occurred while processing the telemetry data. Our system engineering team has been notified."), 500

    return app
