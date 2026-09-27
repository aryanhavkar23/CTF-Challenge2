def test_index_unauthenticated_redirects(client):
    """GET / redirects unauthenticated visitor to /login."""
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers.get('Location', '')

def test_login_works(client):
    """Logging in with valid analyst credentials succeeds and redirects to /dashboard."""
    response = client.post('/login', data={
        'username': 'analyst',
        'password': 'analyst2026'
    }, follow_redirects=False)
    
    assert response.status_code == 302
    assert '/dashboard' in response.headers.get('Location', '')
    
    # Follow redirect to dashboard and verify authenticated session
    dashboard_resp = client.get('/dashboard')
    assert dashboard_resp.status_code == 200
    assert b"analyst" in dashboard_resp.data

def test_invalid_login_fails(client):
    """Invalid credentials return 401 Unauthorized with an error message."""
    response = client.post('/login', data={
        'username': 'analyst',
        'password': 'wrongpassword'
    }, follow_redirects=False)
    
    assert response.status_code == 401
    assert b"Invalid credentials" in response.data

def test_empty_login_fails(client):
    """Empty credentials return 401 Unauthorized."""
    response = client.post('/login', data={
        'username': '',
        'password': ''
    }, follow_redirects=False)
    
    assert response.status_code == 401

def test_unauthenticated_dashboard_redirects_to_login(client):
    """Unauthenticated access to /dashboard must redirect to /login."""
    response = client.get('/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers.get('Location', '')

def test_logout_works(auth_client):
    """GET /logout clears user session and redirects to /login."""
    response = auth_client.get('/logout', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers.get('Location', '')

    # Verifying subsequent /dashboard access is rejected
    subsequent = auth_client.get('/dashboard', follow_redirects=False)
    assert subsequent.status_code == 302
    assert '/login' in subsequent.headers.get('Location', '')
