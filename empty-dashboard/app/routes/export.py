import hashlib
import json
import csv
import io
from flask import Blueprint, render_template, request, Response, session, jsonify, current_app
from app.routes import login_required
from app.models import Report

export_bp = Blueprint('export', __name__)

def _export_failure():
    """Returns a generic error response without disclosing which check failed."""
    message = "Export validation failed."
    if request.is_json or 'application/json' in request.headers.get('Accept', ''):
        return jsonify({
            "code": 403,
            "error": "Forbidden",
            "message": message
        }), 403
    return render_template(
        'error.html',
        code=403,
        title="Validation Failed",
        message=message
    ), 403

@export_bp.route('/export', methods=['GET', 'POST'])
@login_required
def export_view():
    """Renders the data export workbench and validates report continuation tokens."""
    json_data = request.get_json(silent=True) or {}
    token = request.values.get('token') or json_data.get('token')
    export_ref = session.get('export_reference')

    # If continuation token is provided, validate it against session context
    if token is not None:
        user_id = session.get('user_id')
        session_token = session.get('continuation_token')
        is_audit = session.get('dashboard_context') == 'audit'
        secret_key = current_app.config['SECRET_KEY']
        expected_token = f"TKN-{hashlib.sha256(f'continuation:{user_id}:{secret_key}'.encode()).hexdigest()[:16]}"

        # Token validation: user must be authenticated, in audit context, with matching authentic session token
        if not user_id or not is_audit or not session_token or session_token != expected_token or token != expected_token:
            return _export_failure()

        # Generate deterministic export reference bound to token and session user
        ref_hash = hashlib.sha256(f"export_ref:{token}:{user_id}:{secret_key}".encode()).hexdigest()[:12].upper()
        export_ref = f"EXP-{ref_hash}"
        session['export_reference'] = export_ref

        if request.is_json or 'application/json' in request.headers.get('Accept', ''):
            return jsonify({
                "status": "success",
                "export_reference": export_ref,
                "message": "Export reference generated successfully. Proceed to /export/confirm."
            }), 200

    download_format = request.args.get('format')
    
    # Handle CSV / JSON data downloads
    if download_format:
        all_reports = Report.get_all(published_only=True)
        reports = all_reports if session.get('dashboard_context') == 'audit' else [r for r in all_reports if r['id'] != 5]
        
        if download_format == 'json':
            data = [
                {
                    "id": r["id"],
                    "title": r["title"],
                    "category": r["category"],
                    "summary": r["summary"],
                    "created_at": str(r["created_at"])
                }
                for r in reports
            ]
            response = Response(
                json.dumps(data, indent=2),
                mimetype="application/json"
            )
            response.headers["Content-Disposition"] = "attachment; filename=analytics_export.json"
            return response

        elif download_format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["ID", "Title", "Category", "Summary", "Created At"])
            for r in reports:
                writer.writerow([r["id"], r["title"], r["category"], r["summary"], str(r["created_at"])])
            
            response = Response(output.getvalue(), mimetype="text/csv")
            response.headers["Content-Disposition"] = "attachment; filename=analytics_export.csv"
            return response

    return render_template(
        'export.html',
        export_reference=export_ref,
        continuation_token=session.get('continuation_token'),
        username=session.get('username', 'analyst')
    )

@export_bp.route('/export/confirm', methods=['GET', 'POST'])
@login_required
def confirm_export():
    """
    Final confirmation endpoint.
    Requires:
    1. Authenticated user
    2. Correct dashboard context (audit)
    3. Correct report continuation token
    4. Correct export reference
    """
    # 1. Authenticated user check
    user_id = session.get('user_id')
    if not user_id:
        return _export_failure()

    # 2. Correct dashboard context check
    if session.get('dashboard_context') != 'audit':
        return _export_failure()

    secret_key = current_app.config['SECRET_KEY']
    expected_token = f"TKN-{hashlib.sha256(f'continuation:{user_id}:{secret_key}'.encode()).hexdigest()[:16]}"

    # 3. Correct report continuation token check (must match authentic derived token)
    session_token = session.get('continuation_token')
    if not session_token or session_token != expected_token:
        return _export_failure()

    json_data = request.get_json(silent=True) or {}
    submitted_token = request.values.get('token') or json_data.get('token')
    if submitted_token and submitted_token != expected_token:
        return _export_failure()

    # 4. Correct export reference check (must match authentic derived export reference)
    expected_ref = f"EXP-{hashlib.sha256(f'export_ref:{expected_token}:{user_id}:{secret_key}'.encode()).hexdigest()[:12].upper()}"
    session_export_ref = session.get('export_reference')
    if not session_export_ref or session_export_ref != expected_ref:
        return _export_failure()

    submitted_ref = request.values.get('ref') or request.values.get('export_ref') or json_data.get('ref') or json_data.get('export_ref')
    if not submitted_ref or submitted_ref != expected_ref:
        return _export_failure()

    # All validations successfully passed -> Return CTF_FLAG
    flag = current_app.config.get('CTF_FLAG', 'CTF{development_flag_replace_me}')

    if request.is_json or 'application/json' in request.headers.get('Accept', ''):
        return jsonify({
            "status": "confirmed",
            "message": "Audited telemetry export confirmed.",
            "export_reference": session_export_ref,
            "flag": flag,
            "telemetry_data": flag
        }), 200

    return render_template(
        'export_confirmed.html',
        flag=flag,
        export_reference=session_export_ref,
        username=session.get('username', 'analyst')
    ), 200
