from flask import Blueprint, request, jsonify, render_template

internal_bp = Blueprint('internal', __name__, url_prefix='/internal')

@internal_bp.route('/debug', methods=['GET', 'POST'])
def internal_debug():
    """Restricted internal diagnostic probe endpoint."""
    message = "Diagnostic interface unavailable."
    
    # Return JSON response for API or JSON clients
    if request.is_json or request.path.endswith('.json') or 'application/json' in request.headers.get('Accept', ''):
        return jsonify({
            "code": 403,
            "error": "Forbidden",
            "status": "restricted",
            "message": message,
            "detail": f"{message} Subsystem telemetry instrumentation is restricted to management control plane nodes.",
            "node": "telemetry-diag-gw01",
            "policy": "SEC-MGMT-ISOLATION"
        }), 403

    # Return standard restricted error view for browser clients
    return render_template(
        'error.html',
        code=403,
        title="Diagnostic Interface Unavailable",
        message=f"{message} Subsystem telemetry instrumentation is restricted to management control plane nodes."
    ), 403
