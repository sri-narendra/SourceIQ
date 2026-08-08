"""Integration tests for the auth API endpoints."""
from tests.conftest import _register


def test_register_success(client):
    r = _register(client)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["access_token"]
    assert body["user"]["email"] == "a@a.com"


def test_register_duplicate_email(client):
    _register(client)
    r = _register(client, email="a@a.com")
    assert r.status_code == 409


def test_register_missing_fields(client):
    r = client.post("/api/v1/auth/register", json={"email": "x@y.com"})
    assert r.status_code == 422


def test_login_success(client):
    _register(client)
    r = client.post("/api/v1/auth/login", json={"email": "a@a.com", "password": "secret123"})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_login_wrong_password(client):
    _register(client)
    r = client.post("/api/v1/auth/login", json={"email": "a@a.com", "password": "nope"})
    assert r.status_code == 401


def test_login_unknown_user(client):
    r = client.post("/api/v1/auth/login", json={"email": "ghost@x.com", "password": "x"})
    assert r.status_code == 401


def test_me_with_token(client, auth_headers):
    r = client.get("/api/v1/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["email"] == "a@a.com"


def test_me_without_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_invalid_token(client):
    r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer bogus"})
    assert r.status_code == 401
