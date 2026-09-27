from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import User, AuditEvent

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    """Root entry point: redirects to dashboard if authenticated, else to login."""
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard_view'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Authentication gateway."""
    # Redirect already logged-in users to dashboard
    if 'user_id' in session and request.method == 'GET':
        return redirect(url_for('dashboard.dashboard_view'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            error = "Username and password are required."
            return render_template('login.html', error=error), 401

        user = User.get_by_username(username)

        if user and User.verify_password(user, password):
            # Establish session securely
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session.permanent = True

            AuditEvent.log(
                user_id=user['id'],
                action="LOGIN_SUCCESS",
                ip_address=request.remote_addr,
                details=f"User {user['username']} logged in successfully"
            )

            return redirect(url_for('dashboard.dashboard_view'))
        else:
            AuditEvent.log(
                user_id=None,
                action="LOGIN_FAILED",
                ip_address=request.remote_addr,
                details=f"Failed login attempt for username: {username}"
            )
            error = "Invalid credentials. Please verify your username and password."
            return render_template('login.html', error=error), 401

    return render_template('login.html')

@auth_bp.route('/logout', methods=['GET'])
def logout():
    """Terminates the user session."""
    user_id = session.get('user_id')
    username = session.get('username')

    if user_id:
        AuditEvent.log(
            user_id=user_id,
            action="LOGOUT",
            ip_address=request.remote_addr,
            details=f"User {username} logged out"
        )

    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for('auth.login'))
