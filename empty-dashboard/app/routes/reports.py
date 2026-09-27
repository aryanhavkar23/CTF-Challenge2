import hashlib
from flask import Blueprint, render_template, abort, session, current_app
from app.routes import login_required
from app.models import Report

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports', methods=['GET'])
@login_required
def list_reports():
    """Lists enterprise intelligence and compliance reports based on session context."""
    all_reports = Report.get_all(published_only=True)
    is_audit = session.get('dashboard_context') == 'audit'

    # Standard analysts only see standard reports; audit context reveals the audit ledger
    if is_audit:
        reports = all_reports
    else:
        reports = [r for r in all_reports if r['id'] != 5]

    return render_template(
        'reports.html',
        reports=reports,
        reports_count=len(reports),
        username=session.get('username', 'analyst')
    )

@reports_bp.route('/reports/<int:report_id>', methods=['GET'])
@login_required
def view_report(report_id: int):
    """Displays detailed contents for a specific report."""
    report = Report.get_by_id(report_id)
    if not report:
        abort(404, description=f"Report #{report_id} could not be located in the archive.")

    continuation_token = None

    # Access control for restricted audit ledger report #5
    if report_id == 5:
        if session.get('dashboard_context') != 'audit':
            return render_template(
                'error.html',
                code=403,
                title="Authorization Failure",
                message="Invalid authorization context. Expected role: auditor."
            ), 403

        # Generate and bind deterministic continuation token for this authenticated session
        user_id = session.get('user_id', 1)
        secret_key = current_app.config['SECRET_KEY']
        token_hash = hashlib.sha256(f"continuation:{user_id}:{secret_key}".encode()).hexdigest()[:16]
        continuation_token = f"TKN-{token_hash}"
        session['continuation_token'] = continuation_token

    return render_template(
        'report.html',
        report=report,
        continuation_token=continuation_token,
        username=session.get('username', 'analyst')
    )
