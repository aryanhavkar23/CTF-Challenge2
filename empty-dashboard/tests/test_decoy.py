def test_internal_debug_returns_403_and_restricted_message(client, auth_client):
    """GET /internal/debug returns 403 and believable diagnostic restricted response."""
    for test_client in [client, auth_client]:
        response = test_client.get('/internal/debug', headers={'Accept': 'application/json'})
        assert response.status_code == 403
        assert response.is_json
        data = response.get_json()
        assert data["code"] == 403
        assert "Diagnostic interface unavailable." in data["message"]
        assert data["status"] == "restricted"

def test_internal_debug_html_response(client, auth_client):
    """GET /internal/debug in browser returns 403 error page with restricted message."""
    response = auth_client.get('/internal/debug')
    assert response.status_code == 403
    html = response.data.decode('utf-8')
    assert "403" in html
    assert "Diagnostic interface unavailable." in html

def test_internal_debug_does_not_reveal_flag_or_solution(client, auth_client, app):
    """Verify /internal/debug does not leak CTF_FLAG or hint at secret session values."""
    flag = app.config.get('CTF_FLAG', 'CTF{')
    
    for test_client in [client, auth_client]:
        json_resp = test_client.get('/internal/debug', headers={'Accept': 'application/json'})
        assert flag.encode() not in json_resp.data
        json_data = json_resp.get_json()
        # Verify no mention of session keys or challenge solution
        assert "session" not in str(json_data).lower()
        assert "flag" not in str(json_data).lower()

        html_resp = test_client.get('/internal/debug')
        assert flag.encode() not in html_resp.data
        assert "flag" not in html_resp.data.decode('utf-8').lower()

def test_api_dashboard_fields(auth_client):
    """Verify /api/dashboard exposes view, reports, mode, and status fields."""
    response = auth_client.get('/api/dashboard')
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()

    # Required fields from Phase 2 specification
    assert "view" in data
    assert "reports" in data
    assert "mode" in data
    assert "status" in data

    # Verify initial empty state values
    assert data["reports"] == 0
    assert data["status"] == "No data available."

def test_api_dashboard_debug_true_difference(auth_client):
    """Verify /api/dashboard?debug=true produces a believable difference without secrets."""
    # Standard request
    standard_resp = auth_client.get('/api/dashboard')
    standard_data = standard_resp.get_json()
    assert "debug" not in standard_data

    # Debug true request
    debug_resp = auth_client.get('/api/dashboard?debug=true')
    assert debug_resp.status_code == 200
    debug_data = debug_resp.get_json()
    assert "debug" in debug_data
    assert debug_data["debug"]["enabled"] is True
    assert "gateway_node" in debug_data["debug"]
    assert "cluster_environment" in debug_data["debug"]

def test_dashboard_debug_true_renders_diagnostics(auth_client):
    """GET /dashboard?debug=true renders the believable diagnostic console."""
    # Standard view: no debug console
    normal_resp = auth_client.get('/dashboard')
    assert b"System Diagnostics Console" not in normal_resp.data

    # Debug view: renders diagnostic console
    debug_resp = auth_client.get('/dashboard?debug=true')
    assert debug_resp.status_code == 200
    html = debug_resp.data.decode('utf-8')
    assert "System Diagnostics Console" in html
    assert "Telemetry Debug Active" in html
    assert "telemetry-worker-node-04b" in html

def test_dashboard_invalid_debug_variations_do_not_enable_debug(auth_client):
    """Only debug=true is accepted; other variations or obvious exploit params must not enable debug."""
    invalid_params = [
        'debug=1',
        'debug=yes',
        'debug=True',
        'admin=true',
        'role=admin',
        'get_flag=true',
        'secret=true'
    ]
    for param in invalid_params:
        resp = auth_client.get(f'/dashboard?{param}')
        assert resp.status_code == 200
        assert b"System Diagnostics Console" not in resp.data, f"Param {param} unexpectedly enabled debug"

def test_report_enumeration_does_not_reveal_flag(auth_client, app):
    """Enumerating all reports via API or UI must never reveal CTF_FLAG."""
    flag = app.config.get('CTF_FLAG', 'CTF{')

    # Enumerate via /api/reports
    list_resp = auth_client.get('/api/reports')
    assert list_resp.status_code == 200
    reports = list_resp.get_json()["reports"]
    assert len(reports) > 0

    for rep in reports:
        rep_id = rep["id"]
        # Query individual report via API
        api_detail = auth_client.get(f'/api/reports/{rep_id}')
        assert api_detail.status_code == 200
        assert flag.encode() not in api_detail.data, f"Flag found in /api/reports/{rep_id}"

        # Query individual report via HTML UI
        ui_detail = auth_client.get(f'/reports/{rep_id}')
        assert ui_detail.status_code == 200
        assert flag.encode() not in ui_detail.data, f"Flag found in /reports/{rep_id}"

def test_all_decoy_endpoints_cannot_directly_retrieve_flag(client, auth_client, app):
    """Comprehensive test proving decoy attack surface cannot directly retrieve CTF_FLAG."""
    flag = app.config.get('CTF_FLAG', 'CTF{')
    decoy_urls = [
        '/internal/debug',
        '/dashboard?debug=true',
        '/api/dashboard',
        '/api/dashboard?debug=true',
        '/api/reports',
        '/api/reports/1',
        '/api/reports/2',
        '/api/reports/3',
        '/api/reports/4',
        '/reports',
        '/reports/1',
        '/reports/2'
    ]

    for url in decoy_urls:
        # Test as unauthenticated if allowed/applicable
        unauth_resp = client.get(url)
        assert flag.encode() not in unauth_resp.data, f"Unauthenticated flag leak at {url}"

        # Test as authenticated analyst
        auth_resp = auth_client.get(url)
        assert flag.encode() not in auth_resp.data, f"Authenticated flag leak at {url}"
