"""Integration tests for workspaces, documents, users, dashboard."""

import io


def _create_workspace(client, auth_headers, name="My Workspace"):
    return client.post(
        "/api/v1/workspaces", headers=auth_headers, json={"name": name, "description": "d"}
    )


def test_create_and_list_workspace(client, auth_headers):
    r = _create_workspace(client, auth_headers)
    assert r.status_code == 201
    wid = r.json()["workspace_id"]

    lst = client.get("/api/v1/workspaces", headers=auth_headers)
    assert lst.status_code == 200
    assert any(w["id"] == wid for w in lst.json())


def test_workspaces_require_auth(client):
    r = client.post("/api/v1/workspaces", json={"name": "x"})
    assert r.status_code == 401


def test_dashboard_summary(client, auth_headers):
    _create_workspace(client, auth_headers)
    r = client.get("/api/v1/dashboard", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["workspace_count"] >= 1
    assert "documents" in r.json()


def test_update_profile(client, auth_headers):
    r = client.put("/api/v1/users/profile", headers=auth_headers, json={"name": "Renamed"})
    assert r.status_code == 200
    me = client.get("/api/v1/auth/me", headers=auth_headers)
    assert me.json()["name"] == "Renamed"


def test_documents_upload_invalid_type(client, auth_headers):
    wid = _create_workspace(client, auth_headers).json()["workspace_id"]
    files = {"file": ("evil.exe", io.BytesIO(b"MZ"), "application/octet-stream")}
    r = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        data={"workspace_id": wid},
        files=files,
    )
    assert r.status_code == 415


def test_documents_list_requires_workspace_param(client, auth_headers):
    r = client.get("/api/v1/documents", headers=auth_headers)
    assert r.status_code == 404


def test_document_access_forbidden_for_other_user(client, auth_headers):
    wid = _create_workspace(client, auth_headers).json()["workspace_id"]

    other = client.post(
        "/api/v1/auth/register",
        json={"name": "Other", "email": "other@testmail.dev", "password": "Testpass1!"},
    )
    other_token = other.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    assert client.get(
        f"/api/v1/documents?workspace_id={wid}", headers=other_headers
    ).status_code == 404
    assert (
        client.post(
            "/api/v1/chat",
            headers=other_headers,
            json={"workspace_id": wid, "message": "hi"},
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/search",
            headers=other_headers,
            json={"workspace_id": wid, "query": "hi"},
        ).status_code
        == 404
    )


def test_delete_missing_document(client, auth_headers):
    r = client.delete(
        "/api/v1/documents/00000000-0000-0000-0000-000000000000", headers=auth_headers
    )
    assert r.status_code == 404


def test_chat_requires_auth(client):
    r = client.post("/api/v1/chat", json={"workspace_id": "x", "message": "hi"})
    assert r.status_code == 401


def test_search_requires_auth(client):
    r = client.post("/api/v1/search", json={"workspace_id": "x", "query": "hi"})
    assert r.status_code == 401
