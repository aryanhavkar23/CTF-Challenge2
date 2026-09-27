def test_export_view_authenticated(auth_client):
    """GET /export renders the export workbench."""
    response = auth_client.get('/export')
    assert response.status_code == 200
    assert b"Data Export" in response.data

def test_export_json_format(auth_client):
    """GET /export?format=json downloads JSON formatted file."""
    response = auth_client.get('/export?format=json')
    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert "analytics_export.json" in response.headers.get("Content-Disposition", "")

def test_export_csv_format(auth_client):
    """GET /export?format=csv downloads CSV formatted file."""
    response = auth_client.get('/export?format=csv')
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert "analytics_export.csv" in response.headers.get("Content-Disposition", "")

def test_robots_txt(client):
    """GET /robots.txt returns plain text directives."""
    response = client.get('/robots.txt')
    assert response.status_code == 200
    assert response.mimetype == "text/plain"
    assert b"User-agent" in response.data
    assert b"Disallow: /api/" in response.data

def test_no_flag_route_exists(client, auth_client):
    """Verify that /flag route does not exist."""
    assert client.get('/flag').status_code == 404
    assert auth_client.get('/flag').status_code == 404

def test_no_admin_route_exists(client, auth_client):
    """Verify that /admin route does not exist."""
    assert client.get('/admin').status_code == 404
    assert auth_client.get('/admin').status_code == 404

def test_no_flag_leakage(auth_client, app):
    """Ensure CTF flag string is never leaked into standard page bodies or responses."""
    flag = app.config.get('CTF_FLAG', 'CTF{')
    
    for route in ['/', '/login', '/dashboard', '/reports', '/export', '/api/dashboard', '/api/reports']:
        resp = auth_client.get(route)
        assert flag.encode() not in resp.data, f"Flag found in route response: {route}"

def test_error_handlers_do_not_leak_stack_traces(client):
    """Error responses should never expose python tracebacks or exception internals."""
    response = client.get('/nonexistent-path-that-triggers-404')
    assert response.status_code == 404
    assert b"Traceback (most recent call last)" not in response.data
    assert b"Werkzeug Debugger" not in response.data
