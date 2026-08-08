"""Shared fixtures for unit + integration tests.

Integration tests hit a real Postgres (test DB `ai_knowledge_test`), which
requires Docker: `docker compose up -d db` first. Set TEST_DATABASE_URL to
override the default.
"""
import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from database.session import Base, get_db
from models import entities  # noqa: F401  (registers models)

TEST_URL = os.environ.get("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/ai_knowledge_test")


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_URL, pool_pre_ping=True)
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db(test_engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = Session()
    yield session
    session.close()
    # fresh tables per test
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)


@pytest.fixture()
def client(test_engine):
    from fastapi.testclient import TestClient

    Session = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    from backend.main import app

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def test_db():
    return TEST_URL


def _register(client, email="a@a.com", password="secret123", name="Test"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "name": name},
    )


@pytest.fixture()
def auth_headers(client):
    _register(client)
    r = client.post(
        "/api/v1/auth/login", json={"email": "a@a.com", "password": "secret123"}
    )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
