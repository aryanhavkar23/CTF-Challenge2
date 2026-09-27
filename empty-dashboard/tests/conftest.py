import os
import sys
import tempfile
import pytest

# Ensure app package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import init_db

@pytest.fixture
def app():
    """Create and configure a clean Flask application instance for testing."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    test_config = {
        'TESTING': True,
        'DEBUG': False,
        'SECRET_KEY': 'test-session-secret-key-12345',
        'DATABASE_PATH': db_path,
        'CTF_FLAG': 'CTF{development_flag_replace_me}',
        'SESSION_COOKIE_SECURE': False
    }

    app = create_app(test_config=test_config)

    yield app

    # Cleanup temp db
    os.close(db_fd)
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass

@pytest.fixture
def client(app):
    """Test client for performing HTTP requests."""
    return app.test_client()

@pytest.fixture
def auth_client(client):
    """Test client with an active authenticated session for user 'analyst'."""
    client.post('/login', data={
        'username': 'analyst',
        'password': 'analyst2026'
    })
    return client
