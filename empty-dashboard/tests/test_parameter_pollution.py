from flask import session

def test_normal_request(auth_client):
    """1. Normal single view parameter produces default reference (DB-19) and not audit state."""
    response = auth_client.get('/dashboard?view=summary')
    assert response.status_code == 200
    html = response.data.decode('utf-8')

    with auth_client.session_transaction() as sess:
        assert sess.get('dashboard_context') != 'audit'
    
    assert "DB-19" in html
    assert "DB-17" not in html
    # The internal keyword "audit" must never be displayed to the participant
    assert "audit" not in html.lower() or "System Diagnostics" in html

def test_duplicate_parameters_wrong_order(auth_client):
    """2. Duplicate parameters in wrong order (view=archive&view=summary) must NOT produce special state."""
    response = auth_client.get('/dashboard?view=archive&view=summary')
    assert response.status_code == 200
    html = response.data.decode('utf-8')

    with auth_client.session_transaction() as sess:
        assert sess.get('dashboard_context') != 'audit'

    assert "DB-19" in html
    assert "DB-17" not in html

def test_duplicate_parameters_correct_order(auth_client):
    """3. Duplicate parameters in correct order (view=summary&view=archive) creates special session state and DB-17."""
    response = auth_client.get('/dashboard?view=summary&view=archive')
    assert response.status_code == 200
    html = response.data.decode('utf-8')

    # Internal session state must be "audit"
    with auth_client.session_transaction() as sess:
        assert sess.get('dashboard_context') == 'audit'

    # Participant sees subtle diagnostic reference DB-17, NOT DB-19
    assert "DB-17" in html
    assert "DB-19" not in html

    # The internal state name "audit" must NOT be displayed to the participant
    assert "context: audit" not in html.lower()
    assert "session['dashboard_context']" not in html
    assert "audit_events" not in html

def test_repeated_identical_parameters(auth_client):
    """4. Repeated identical parameters (archive/archive or summary/summary) must not produce special state."""
    # Test view=archive&view=archive
    resp_archive = auth_client.get('/dashboard?view=archive&view=archive')
    assert resp_archive.status_code == 200
    html_archive = resp_archive.data.decode('utf-8')
    with auth_client.session_transaction() as sess:
        assert sess.get('dashboard_context') != 'audit'
    assert "DB-19" in html_archive
    assert "DB-17" not in html_archive

    # Test view=summary&view=summary
    resp_summary = auth_client.get('/dashboard?view=summary&view=summary')
    assert resp_summary.status_code == 200
    html_summary = resp_summary.data.decode('utf-8')
    with auth_client.session_transaction() as sess:
        assert sess.get('dashboard_context') != 'audit'
    assert "DB-19" in html_summary
    assert "DB-17" not in html_summary

def test_fresh_session(client):
    """5. A fresh authenticated session defaults to standard state and DB-19."""
    # Login as analyst in fresh session
    client.post('/login', data={'username': 'analyst', 'password': 'analyst2026'})
    response = client.get('/dashboard')
    assert response.status_code == 200
    html = response.data.decode('utf-8')

    with client.session_transaction() as sess:
        assert sess.get('dashboard_context') != 'audit'

    assert "DB-19" in html
    assert "DB-17" not in html

def test_special_session_persistence(auth_client):
    """6. Special session state (audit / DB-17) persists across subsequent requests."""
    # Trigger special state with parameter pollution
    pollute_resp = auth_client.get('/dashboard?view=summary&view=archive')
    assert pollute_resp.status_code == 200
    assert "DB-17" in pollute_resp.data.decode('utf-8')

    with auth_client.session_transaction() as sess:
        assert sess.get('dashboard_context') == 'audit'

    # Subsequent request with NO parameters should maintain DB-17
    followup_resp = auth_client.get('/dashboard')
    assert followup_resp.status_code == 200
    followup_html = followup_resp.data.decode('utf-8')
    assert "DB-17" in followup_html
    assert "DB-19" not in followup_html

    with auth_client.session_transaction() as sess:
        assert sess.get('dashboard_context') == 'audit'

    # Subsequent request with debug=true should also maintain DB-17
    debug_resp = auth_client.get('/dashboard?debug=true')
    assert debug_resp.status_code == 200
    debug_html = debug_resp.data.decode('utf-8')
    assert "DB-17" in debug_html
    assert "DB-19" not in debug_html

    # Subsequent request to /api/dashboard should return DB-17
    api_resp = auth_client.get('/api/dashboard')
    assert api_resp.status_code == 200
    api_data = api_resp.get_json()
    assert api_data.get('telemetry_ref') == 'DB-17'

def test_copying_diagnostic_reference_into_fresh_session_fails(client):
    """Attempting to set special state by passing DB-17 as a parameter in a fresh session does not work."""
    client.post('/login', data={'username': 'analyst', 'password': 'analyst2026'})

    spoofed_params = [
        'ref=DB-17',
        'telemetry_ref=DB-17',
        'diagnostic_ref=DB-17',
        'view=DB-17'
    ]

    for param in spoofed_params:
        resp = client.get(f'/dashboard?{param}')
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')

        with client.session_transaction() as sess:
            assert sess.get('dashboard_context') != 'audit', f"Parameter {param} falsely set audit context"

        assert "DB-19" in html, f"Parameter {param} did not return normal DB-19"
        assert "DB-17" not in html, f"Parameter {param} falsely displayed DB-17"
