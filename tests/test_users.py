def test_login_success(client):
    response = client.post(
        "/user/token",
        data={"username": "normal_test", "password": "testpass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client):
    response = client.post(
        "/user/token",
        data={"username": "normal_test", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

def test_login_nonexistent_user(client):
    response = client.post(
        "/user/token",
        data={"username": "not_exists", "password": "testpass"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

def test_signup_success(client):
    login_response = client.post(
        "/user/token",
        data={"username": "admin_test", "password": "testpass"}
    )
    token = login_response.json()["access_token"]
    
    response = client.post(
        "/user/signup",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "new_user", "password": "newpassword", "admin": False}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "new_user"
    assert "id" in data

def test_signup_duplicate_username(client):
    login_response = client.post(
        "/user/token",
        data={"username": "admin_test", "password": "testpass"}
    )
    token = login_response.json()["access_token"]
    
    response = client.post(
        "/user/signup",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "normal_test", "password": "anypassword"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already registered"}

def test_signup_unauthorized(client):
    login_response = client.post(
        "/user/token",
        data={"username": "normal_test", "password": "testpass"}
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/user/signup",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "unauthorized_user", "password": "unauthorized_password"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "UNAUTHORIZED"}    

def test_get_me_success(client):
    login_response = client.post(
        "/user/token",
        data={"username": "normal_test", "password": "testpass"}
    )
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/user/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "normal_test"

def test_get_me_invalid_token(client):
    response = client.get(
        "/user/me",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "UNAUTHORIZED"}

def test_signup_no_token(client):
    response = client.post(
        "/user/signup",
        json={"username": "hacker", "password": "123"}
    )
    assert response.status_code == 401
