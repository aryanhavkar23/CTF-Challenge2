import hashlib
from flask import Blueprint, jsonify, request, abort, session, current_app
from app.routes import login_required
from app.models import Report
from app.routes.dashboard import resolve_dashboard_context

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/dashboard', methods=['GET'])
@login_required
def api_dashboard():
    """Returns application overview and telemetry metrics with state-dependent metadata in JSON format."""
    is_debug = request.args.get('debug') == 'true'
    telemetry_ref = resolve_dashboard_context()
    is_audit = telemetry_ref == 'DB-17'

    response_data = {
        "view": "analyst_overview",
        "mode": "read_only",
        "reports": 0,
        "revenue": "---",
        "users": "---",
        "status": "No data available.",
        "telemetry_ref": telemetry_ref,
        "reference": telemetry_ref
    }

    # State-dependent non-secret metadata
    if is_audit:
        response_data.update({
            "stream_partition": "partition_02_archive",
            "access_tier": "extended_partition",
            "pipeline_state": "standby_reconciliation",
            "reconciliation_channel": "ch-reconcile-02"
        })
    else:
        response_data.update({
            "stream_partition": "partition_04_default",
            "access_tier": "standard_tier",
            "pipeline_state": "idle",
            "reconciliation_channel": "ch-default-04"
        })

    if is_debug:
        response_data["debug"] = {
            "enabled": True,
            "gateway_node": "telemetry-worker-node-04b",
            "cluster_environment": "production-internal",
            "session_scope": "analyst_standard_read",
            "pipeline_status": "standby_idle",
            "diagnostics_subsystem": "isolated_control_plane",
            "trace_id": "tr-20260927-08412",
            "diagnostic_ref": telemetry_ref
        }

    return jsonify(response_data)

@api_bp.route('/reports', methods=['GET'])
@login_required
def api_reports():
    """Returns accessible report summaries and realistic metadata in JSON format."""
    all_reports = Report.get_all(published_only=True)
    is_audit = session.get('dashboard_context') == 'audit'

    # Filter reports according to current session context
    if is_audit:
        reports = all_reports
    else:
        reports = [r for r in all_reports if r['id'] != 5]

    report_list = [
        {
            "id": r["id"],
            "title": r["title"],
            "category": r["category"],
            "summary": r["summary"],
            "created_at": str(r["created_at"]),
            "author": r["author_username"] or "system_auditor",
            "classification": "Internal-Confidential"
        }
        for r in reports
    ]
    return jsonify({
        "count": len(report_list),
        "classification": "internal_confidential",
        "reports": report_list
    })

@api_bp.route('/reports/<int:report_id>', methods=['GET'])
@login_required
def api_report_detail(report_id: int):
    """Enables report enumeration with decoy IDOR protection requiring audit state."""
    report = Report.get_by_id(report_id)
    if not report:
        abort(404, description=f"Report #{report_id} could not be located in the archive.")

    # Access control for restricted audit ledger report #5
    continuation_token = None
    if report_id == 5:
        if session.get('dashboard_context') != 'audit':
            return jsonify({
                "code": 403,
                "error": "Forbidden",
                "message": "Invalid authorization context. Expected role: auditor."
            }), 403

        # Generate and bind deterministic continuation token for this authenticated session
        user_id = session.get('user_id', 1)
        secret_key = current_app.config['SECRET_KEY']
        token_hash = hashlib.sha256(f"continuation:{user_id}:{secret_key}".encode()).hexdigest()[:16]
        continuation_token = f"TKN-{token_hash}"
        session['continuation_token'] = continuation_token

    response_payload = {
        "id": report["id"],
        "title": report["title"],
        "category": report["category"],
        "summary": report["summary"],
        "content": report["content"],
        "created_at": str(report["created_at"]),
        "author": report["author_username"] or "system_auditor",
        "classification": "Internal-Confidential",
        "status": "archived"
    }

    if continuation_token:
        response_payload["continuation_token"] = continuation_token

    return jsonify(response_payload)
