from functools import wraps
from flask import session, redirect, url_for, flash, request, g
from app.models import User

def login_required(f):
    """Decorator to enforce authenticated session and active user verification."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            if request.path.startswith('/api/') or request.is_json or 'application/json' in request.headers.get('Accept', ''):
                return {"error": "Authentication required"}, 401
            return redirect(url_for('auth.login'))

        user = User.get_by_id(user_id)
        if not user:
            session.clear()
            if request.path.startswith('/api/') or request.is_json or 'application/json' in request.headers.get('Accept', ''):
                return {"error": "Invalid session"}, 401
            return redirect(url_for('auth.login'))

        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function
