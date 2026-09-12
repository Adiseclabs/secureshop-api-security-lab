"""
tests/test_api.py
--------------------
Minimal functional tests: health check, registration, login, and basic
authorization behavior. Run with:  pytest
These are NOT the security testing exercise itself - they just confirm
the app's basic plumbing works.
"""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["DATABASE_PATH"] = os.path.join(tempfile.gettempdir(), "secureshop_test.db")
os.environ["TRAINING_MODE"] = "false"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"

from app import create_app          # noqa: E402
from database.db import db          # noqa: E402


@pytest.fixture()
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.drop_all()
        db.create_all()
    with app.test_client() as c:
        yield c
    with app.app_context():
        db.drop_all()


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == 200


def test_register_and_login(client):
    resp = client.post("/api/register", json={
        "name": "Test User",
        "email": "test.user@secureshop.local",
        "password": "TestPass123",
    })
    assert resp.status_code == 201

    resp = client.post("/api/login", json={
        "email": "test.user@secureshop.local",
        "password": "TestPass123",
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert "token" in body["data"]


def test_register_rejects_weak_password(client):
    resp = client.post("/api/register", json={
        "name": "Weak Pw",
        "email": "weak.pw@secureshop.local",
        "password": "abc",
    })
    assert resp.status_code == 400


def test_profile_requires_auth(client):
    resp = client.get("/api/profile")
    assert resp.status_code == 401


def test_admin_route_requires_admin_role(client):
    client.post("/api/register", json={
        "name": "Regular User",
        "email": "regular.user@secureshop.local",
        "password": "TestPass123",
    })
    login = client.post("/api/login", json={
        "email": "regular.user@secureshop.local",
        "password": "TestPass123",
    })
    token = login.get_json()["data"]["token"]

    resp = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_login_invalid_credentials(client):
    resp = client.post("/api/login", json={
        "email": "nobody@secureshop.local",
        "password": "WrongPass123",
    })
    assert resp.status_code == 401
