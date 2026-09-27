def test_state_dependent_api_dashboard_metadata(auth_client):
    """2. /api/dashboard exposes different non-secret metadata depending on server-side state."""
    # 1. Normal state metadata check
    normal_resp = auth_client.get('/api/dashboard')
    assert normal_resp.status_code == 200
    normal_data = normal_resp.get_json()
    assert normal_data["telemetry_ref"] == "DB-19"
    assert normal_data["stream_partition"] == "partition_04_default"
    assert normal_data["access_tier"] == "standard_tier"
    assert normal_data["pipeline_state"] == "idle"

    # Transition to audit state via HPP
    auth_client.get('/dashboard?view=summary&view=archive')

    # 2. Special audit state metadata check
    audit_resp = auth_client.get('/api/dashboard')
    assert audit_resp.status_code == 200
    audit_data = audit_resp.get_json()
    assert audit_data["telemetry_ref"] == "DB-17"
    assert audit_data["stream_partition"] == "partition_02_archive"
    assert audit_data["access_tier"] == "extended_partition"
    assert audit_data["pipeline_state"] == "standby_reconciliation"

def test_misleading_authorization_error_on_report_5(auth_client):
    """3. Endpoint responds with misleading 'Expected role: auditor' error when context != audit."""
    # Standard state check on HTML view
    resp_html = auth_client.get('/reports/5')
    assert resp_html.status_code == 403
    assert "Invalid authorization context. Expected role: auditor." in resp_html.data.decode('utf-8')

    # Standard state check on JSON API
    resp_api = auth_client.get('/api/reports/5')
    assert resp_api.status_code == 403
    assert resp_api.is_json
    api_data = resp_api.get_json()
    assert api_data.get("message") == "Invalid authorization context. Expected role: auditor."

def test_role_auditor_does_not_bypass_actual_condition(client):
    """Verify that tampering with role='auditor' does NOT grant access without dashboard_context='audit'."""
    client.post('/login', data={'username': 'analyst', 'password': 'analyst2026'})

    # Manually tamper with session to simulate an attacker setting role to 'auditor'
    with client.session_transaction() as sess:
        sess['role'] = 'auditor'
        sess['dashboard_context'] = 'default'  # Ensure dashboard_context is NOT audit

    # Requesting report 5 must still fail because the real requirement is dashboard_context=='audit'
    resp = client.get('/reports/5')
    assert resp.status_code == 403
    assert "Invalid authorization context. Expected role: auditor." in resp.data.decode('utf-8')

    resp_api = client.get('/api/reports/5')
    assert resp_api.status_code == 403

def test_decoy_idor_report_access(auth_client):
    """4. Decoy IDOR: Reports 1-4 are accessible normally, while Report 5 requires audit context."""
    # Standard reports 1-4 accessible in normal state
    for rep_id in [1, 2, 3, 4]:
        resp = auth_client.get(f'/reports/{rep_id}')
        assert resp.status_code == 200
        resp_api = auth_client.get(f'/api/reports/{rep_id}')
        assert resp_api.status_code == 200

    # Report 5 is blocked in normal state
    assert auth_client.get('/reports/5').status_code == 403

    # Activate audit state via correct HPP parameter ordering
    auth_client.get('/dashboard?view=summary&view=archive')

    # Report 5 is now unlocked
    unlocked_resp = auth_client.get('/reports/5')
    assert unlocked_resp.status_code == 200
    assert "Audit Ledger Telemetry" in unlocked_resp.data.decode('utf-8')

    unlocked_api = auth_client.get('/api/reports/5')
    assert unlocked_api.status_code == 200
    assert unlocked_api.get_json()["title"] == "Internal Security & Audit Ledger Telemetry"

def test_state_dependent_reports_list_filtering(auth_client):
    """Reports list hides report 5 in default state and exposes it in audit state."""
    # In default state: 4 reports visible
    norm_list = auth_client.get('/api/reports').get_json()
    assert norm_list["count"] == 4
    assert not any(r["id"] == 5 for r in norm_list["reports"])

    # Transition to audit state
    auth_client.get('/dashboard?view=summary&view=archive')

    # In audit state: 5 reports visible
    audit_list = auth_client.get('/api/reports').get_json()
    assert audit_list["count"] == 5
    assert any(r["id"] == 5 for r in audit_list["reports"])

def test_all_state_transitions_deterministic(auth_client):
    """6. Parameter order dependency: Deterministic state transitions between default and audit."""
    # 1. Fresh state -> DB-19
    r1 = auth_client.get('/dashboard')
    assert "DB-19" in r1.data.decode('utf-8')
    assert auth_client.get('/reports/5').status_code == 403

    # 2. view=archive&view=summary (Wrong order) -> Remains DB-19
    r2 = auth_client.get('/dashboard?view=archive&view=summary')
    assert "DB-19" in r2.data.decode('utf-8')
    assert auth_client.get('/reports/5').status_code == 403

    # 3. view=summary&view=archive (Correct order) -> Transitions to DB-17
    r3 = auth_client.get('/dashboard?view=summary&view=archive')
    assert "DB-17" in r3.data.decode('utf-8')
    assert auth_client.get('/reports/5').status_code == 200

    # 4. Subsequent request with no parameters -> Persists in DB-17
    r4 = auth_client.get('/dashboard')
    assert "DB-17" in r4.data.decode('utf-8')
    assert auth_client.get('/reports/5').status_code == 200

    # 5. view=summary (Reset) -> Transitions back to DB-19
    r5 = auth_client.get('/dashboard?view=summary')
    assert "DB-19" in r5.data.decode('utf-8')
    assert auth_client.get('/reports/5').status_code == 403

def test_session_isolation_and_copying_resistance(client, auth_client):
    """5. Session dependency: Special state is tied to session; copying parameters to fresh session fails."""
    # Session A achieves audit state
    auth_client.get('/dashboard?view=summary&view=archive')
    assert auth_client.get('/reports/5').status_code == 200

    # Session B (fresh session) logs in
    client.post('/login', data={'username': 'analyst', 'password': 'analyst2026'})
    
    # Session B cannot access report 5
    assert client.get('/reports/5').status_code == 403

    # Session B cannot reproduce audit state by passing references as query params
    client.get('/dashboard?ref=DB-17&telemetry_ref=DB-17')
    assert client.get('/reports/5').status_code == 403
