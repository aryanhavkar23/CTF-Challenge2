from flask import Blueprint, render_template, session, request
from app.routes import login_required

dashboard_bp = Blueprint('dashboard', __name__)

def resolve_dashboard_context():
    """
    Evaluates requested telemetry projection view against session context.
    Uses primary view parameter check alongside chained pipeline resolution.
    """
    primary_view = request.args.get('view')
    pipeline_views = request.args.getlist('view')

    if primary_view is not None:
        # Check primary view permission against secondary pipeline target
        # Strictly enforce the exact duplicate parameter pair: view=summary&view=archive
        if primary_view == 'summary' and pipeline_views == ['summary', 'archive']:
            session['dashboard_context'] = 'audit'
        else:
            session['dashboard_context'] = 'default'

    context = session.get('dashboard_context', 'default')
    return 'DB-17' if context == 'audit' else 'DB-19'

@dashboard_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard_view():
    """Renders the executive internal metrics and telemetry dashboard."""
    is_debug = request.args.get('debug') == 'true'
    telemetry_ref = resolve_dashboard_context()

    # Baseline live telemetry metrics
    metrics = {
        "revenue": "---",
        "users": "---",
        "reports": 0,
        "status_message": "No data available."
    }

    debug_info = None
    if is_debug:
        debug_info = {
            "gateway_node": "telemetry-worker-node-04b",
            "cluster_environment": "production-internal",
            "session_scope": "analyst_standard_read",
            "pipeline_status": "standby_idle",
            "diagnostics_subsystem": "isolated_control_plane",
            "trace_id": "tr-20260927-08412",
            "memory_buffer": "38.2 MB / 1024 MB",
            "active_filters": "dept=analytics, stream=idle",
            "diagnostic_ref": telemetry_ref
        }

    return render_template(
        'dashboard.html',
        metrics=metrics,
        telemetry_ref=telemetry_ref,
        debug_mode=is_debug,
        debug_info=debug_info,
        username=session.get('username', 'analyst'),
        role=session.get('role', 'analyst')
    )
