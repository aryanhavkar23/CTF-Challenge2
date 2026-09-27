def test_authenticated_dashboard_works(auth_client):
    """Authenticated dashboard displays initial required metrics and empty state text."""
    response = auth_client.get('/dashboard')
    assert response.status_code == 200
    
    html = response.data.decode('utf-8')
    
    # Required metric displays
    assert "Revenue: ---" in html or ("Revenue" in html and "---" in html)
    assert "Users: ---" in html or ("Users" in html and "---" in html)
    assert "Reports: 0" in html or ("Reports" in html and "0" in html)
    
    # Required empty state text
    assert "No data available." in html

def test_api_dashboard_endpoint_authenticated(auth_client):
    """GET /api/dashboard returns the expected JSON telemetry schema."""
    response = auth_client.get('/api/dashboard')
    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert data["revenue"] == "---"
    assert data["users"] == "---"
    assert data["reports"] == 0
    assert data["status"] == "No data available."

def test_api_dashboard_endpoint_unauthenticated(client):
    """Unauthenticated call to /api/dashboard yields 401 Unauthorized JSON."""
    response = client.get('/api/dashboard')
    assert response.status_code == 401
    assert response.is_json
    data = response.get_json()
    assert "error" in data
