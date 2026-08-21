from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_login_success_sets_cookie():
    response = client.post("/api/login", json={"username": "user", "password": "password"})
    assert response.status_code == 200
    assert response.json() == {"username": "user"}
    assert "session" in response.cookies


def test_login_failure_wrong_password():
    response = client.post("/api/login", json={"username": "user", "password": "wrong"})
    assert response.status_code == 401


def test_login_failure_unknown_user():
    response = client.post("/api/login", json={"username": "nobody", "password": "password"})
    assert response.status_code == 401


def test_me_requires_authentication():
    response = client.get("/api/me")
    assert response.status_code == 401


def test_me_with_valid_session():
    login_response = client.post("/api/login", json={"username": "user", "password": "password"})
    token = login_response.cookies["session"]

    response = client.get("/api/me", cookies={"session": token})
    assert response.status_code == 200
    assert response.json() == {"username": "user"}


def test_logout_invalidates_session():
    login_response = client.post("/api/login", json={"username": "user", "password": "password"})
    token = login_response.cookies["session"]

    logout_response = client.post("/api/logout", cookies={"session": token})
    assert logout_response.status_code == 204

    me_response = client.get("/api/me", cookies={"session": token})
    assert me_response.status_code == 401
