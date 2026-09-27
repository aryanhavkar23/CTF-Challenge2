"""
Adversarial CTF security regression test suite for 'The Empty Dashboard: False Positive'.
Ensures that all unintended paths, bypasses, parameter tampering, and session forgeries fail,
while the intended multi-step exploit chain remains deterministic and functional.
"""
import hashlib
import json
import pytest

def test_direct_sensitive_endpoints_not_found_or_forbidden(client, auth_client):
    """Attempt direct access to flag, admin, and debug endpoints without chain."""
    for endpoint in ['/flag', '/admin', '/debug', '/api/flag', '/api/admin', '/api/v1/flag']:
        # Unauthenticated
        assert client.get(endpoint).status_code == 404
        assert client.post(endpoint).status_code == 404
        assert client.put(endpoint).status_code == 404
        assert client.delete(endpoint).status_code == 404

        # Authenticated
        assert auth_client.get(endpoint).status_code == 404
        assert auth_client.post(endpoint).status_code == 404

def test_internal_debug_isolated_and_resists_header_spoofing(client, auth_client):
    """Internal debug endpoint must unconditionally return 403 and never expose the flag."""
    spoofed_headers = [
        {'X-Forwarded-For': '127.0.0.1'},
        {'X-Originating-IP': '127.0.0.1'},
        {'X-Remote-IP': '127.0.0.1'},
        {'X-Real-IP': '127.0.0.1'},
        {'Client-IP': '127.0.0.1'},
        {'Host': 'localhost'},
    ]

    for headers in spoofed_headers:
        resp = client.get('/internal/debug', headers=headers)
        assert resp.status_code == 403
        assert b"Diagnostic interface unavailable." in resp.data
        assert b"CTF{" not in resp.data

        auth_resp = auth_client.get('/internal/debug', headers=headers)
        assert auth_resp.status_code == 403
        assert b"CTF{" not in auth_resp.data

def test_robots_txt_does_not_leak_flag(client):
    """robots.txt provides standard crawler directives without leaking sensitive secrets."""
    resp = client.get('/robots.txt')
    assert resp.status_code == 200
    assert resp.mimetype == "text/plain"
    assert b"CTF{" not in resp.data
    assert b"Disallow: /api/" in resp.data
    assert b"Disallow: /export" in resp.data

def test_static_assets_contain_no_secrets_or_flags(client):
    """Static CSS and JavaScript must not contain leaked flags, secrets, or internal keywords."""
    for asset_path in ['/static/css/style.css', '/static/js/app.js']:
        resp = client.get(asset_path)
        assert resp.status_code == 200
        assert b"CTF{" not in resp.data
        assert b"SECRET_KEY" not in resp.data
        assert b"continuation_token" not in resp.data
        assert b"export_reference" not in resp.data

def test_static_path_traversal_blocked(client):
    """Attempt directory traversal on static assets."""
    traversal_paths = [
        '/static/../config.py',
        '/static/..%2fconfig.py',
        '/static/../.env',
        '/static/..%2f.env',
        '/static/%2e%2e%2f.env',
    ]
    for p in traversal_paths:
        resp = client.get(p)
        assert resp.status_code in [404, 400]
        assert b"CTF{" not in resp.data

def test_login_resists_sqli_bypass(client):
    """Authentication gateway must use parameterized queries and reject SQL injection payloads."""
    sqli_payloads = [
        ("' OR '1'='1", "password"),
        ("admin' --", "password"),
        ("analyst' OR 1=1 --", "password"),
        ("' UNION SELECT 1, 'admin', 'hash', 'admin' --", "password"),
    ]
    for username, password in sqli_payloads:
        resp = client.post('/login', data={'username': username, 'password': password})
        assert resp.status_code == 401
        assert b"Invalid credentials" in resp.data

def test_hpp_extra_junk_parameters_do_not_trigger_audit(auth_client):
    """Supplying more than the exact 2 parameters or injecting intermediate junk must fail."""
    invalid_hpp_queries = [
        "view=summary&view=foo&view=archive",
        "view=summary&view=archive&view=extra",
        "view=summary&view=archive&view=archive",
        "view=summary&view=summary&view=archive",
        "view=SUMMARY&view=ARCHIVE",
        "view[]=summary&view[]=archive",
    ]
    for q in invalid_hpp_queries:
        # Reset session context
        with auth_client.session_transaction() as sess:
            sess['dashboard_context'] = 'default'

        resp = auth_client.get(f'/dashboard?{q}')
        assert "DB-19" in resp.data.decode('utf-8')
        with auth_client.session_transaction() as sess:
            assert sess.get('dashboard_context') != 'audit'

def test_session_forgery_of_dummy_tokens_blocked(client, app):
    """
    Session tampering regression:
    Injecting arbitrary dummy continuation_token and export_reference must be rejected
    by cryptographic derivation verification in /export and /export/confirm.
    """
    client.post('/login', data={'username': 'analyst', 'password': 'analyst2026'})

    # Manually inject forged dummy state into session
    with client.session_transaction() as sess:
        sess['dashboard_context'] = 'audit'
        sess['continuation_token'] = 'TKN-FORGED-DUMMY-VALUE'
        sess['export_reference'] = 'EXP-FORGED-DUMMY-VALUE'

    # 1. /export with forged dummy token must be rejected
    exp_resp = client.get('/export?token=TKN-FORGED-DUMMY-VALUE')
    assert exp_resp.status_code == 403
    assert "Export validation failed." in exp_resp.data.decode('utf-8')

    # 2. /export/confirm with forged dummy export reference must be rejected
    confirm_resp = client.get('/export/confirm?ref=EXP-FORGED-DUMMY-VALUE')
    assert confirm_resp.status_code == 403
    assert "Export validation failed." in confirm_resp.data.decode('utf-8')
    assert app.config.get('CTF_FLAG', 'CTF{').encode() not in confirm_resp.data

def test_user_session_validation_in_login_required(client):
    """Tampering session user_id to a nonexistent user must terminate session."""
    with client.session_transaction() as sess:
        sess['user_id'] = 999999
        sess['username'] = 'ghost'

    # Attempt to access dashboard
    resp = client.get('/dashboard')
    # Must redirect to login and clear invalid session
    assert resp.status_code == 302
    assert '/login' in resp.headers.get('Location', '')

    # Subsequent check should confirm session is clean
    with client.session_transaction() as sess:
        assert 'user_id' not in sess

def test_method_tampering_on_confirmation(auth_client):
    """Unsupported HTTP methods on /export/confirm return 405 Method Not Allowed."""
    # Achieve valid state
    auth_client.get('/dashboard?view=summary&view=archive')
    rep = auth_client.get('/api/reports/5').get_json()
    tkn = rep['continuation_token']
    exp = auth_client.get(f'/export?token={tkn}', headers={'Accept': 'application/json'}).get_json()['export_reference']

    for method in ['put', 'delete', 'patch']:
        func = getattr(auth_client, method)
        resp = func(f'/export/confirm?ref={exp}')
        assert resp.status_code == 405

def test_json_post_body_support_on_confirmation(auth_client, app):
    """API clients submitting valid export reference via JSON POST receive the flag."""
    expected_flag = app.config.get('CTF_FLAG', 'CTF{')

    # Complete valid chain prerequisites
    auth_client.get('/dashboard?view=summary&view=archive')
    rep = auth_client.get('/api/reports/5').get_json()
    tkn = rep['continuation_token']
    exp_res = auth_client.post('/export', json={'token': tkn}, headers={'Accept': 'application/json'})
    assert exp_res.status_code == 200
    exp = exp_res.get_json()['export_reference']

    # Confirm via JSON POST
    confirm_resp = auth_client.post('/export/confirm', json={'ref': exp}, headers={'Accept': 'application/json'})
    assert confirm_resp.status_code == 200
    confirm_data = confirm_resp.get_json()
    assert confirm_data['status'] == 'confirmed'
    assert confirm_data['flag'] == expected_flag
