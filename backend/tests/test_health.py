"""Smoke tests for Module 1 core endpoints."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint() -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["project"] == "VTU AI Study Portal"
    assert "version" in body


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_versioned_root_endpoint() -> None:
    response = client.get("/api/v1")
    assert response.status_code == 200


def test_versioned_version_endpoint() -> None:
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    assert "environment" in response.json()
