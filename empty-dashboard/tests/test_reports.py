def test_reports_work_authenticated(auth_client):
    """GET /reports displays reports archive with seeded intelligence reports."""
    response = auth_client.get('/reports')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert "Departmental Intelligence Reports" in html
    assert "Telemetry Ingestion Pipeline" in html

def test_unauthenticated_reports_redirects(client):
    """GET /reports requires login and redirects to /login."""
    response = client.get('/reports', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers.get('Location', '')

def test_nonexistent_report_gives_404(auth_client):
    """GET /reports/<report_id> returns 404 for nonexistent report."""
    response = auth_client.get('/reports/999')
    assert response.status_code == 404
    html = response.data.decode('utf-8')
    assert "404" in html
    assert "Page Not Found" in html or "could not be located" in html

def test_api_reports_authenticated(auth_client):
    """GET /api/reports returns JSON summary with realistic metadata."""
    response = auth_client.get('/api/reports')
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert "count" in data
    assert data["count"] > 0
    assert "reports" in data
    assert isinstance(data["reports"], list)

    # Check realistic metadata fields
    first_report = data["reports"][0]
    assert "id" in first_report
    assert "title" in first_report
    assert "category" in first_report
    assert "summary" in first_report
    assert "created_at" in first_report
    assert "author" in first_report
    assert "classification" in first_report

def test_api_reports_unauthenticated(client):
    """Unauthenticated call to /api/reports returns 401 JSON."""
    response = client.get('/api/reports')
    assert response.status_code == 401
    assert response.is_json

def test_api_report_detail_enumeration(auth_client):
    """GET /api/reports/<id> returns specific report details for enumeration."""
    response = auth_client.get('/api/reports/1')
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert data["id"] == 1
    assert "content" in data
    assert "summary" in data

def test_api_report_detail_nonexistent(auth_client):
    """GET /api/reports/<id> returns 404 for nonexistent report ID."""
    response = auth_client.get('/api/reports/9999')
    assert response.status_code == 404
