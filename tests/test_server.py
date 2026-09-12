from fastapi.testclient import TestClient
from starlette.middleware.cors import CORSMiddleware

import server


def test_cors_is_not_configured_with_wildcard_origin():
    cors_entries = [m for m in server.app.user_middleware if m.cls is CORSMiddleware]

    assert len(cors_entries) == 1
    assert cors_entries[0].kwargs["allow_origins"] != ["*"]


def test_recommend_endpoint_wires_ticket_through_retrieve_and_recommend(monkeypatch):
    captured = {}

    def fake_retrieve(ticket_description, corpus, index):
        captured["ticket"] = ticket_description
        return [
            {"kb_number": "KB0000001", "title": "T", "body": "B", "category": "C", "score": 0.9}
        ]

    def fake_recommend(ticket_description, articles, call_llm):
        captured["articles"] = articles
        return {
            "issue_summary": "ok",
            "resolution_steps": [],
            "cited_kb_articles": [],
            "retrieval": [],
        }

    monkeypatch.setattr(server, "retrieve", fake_retrieve)
    monkeypatch.setattr(server, "recommend", fake_recommend)

    client = TestClient(server.app)
    response = client.post("/recommend", json={"ticket_description": "wifi not working"})

    assert response.status_code == 200
    assert response.json()["issue_summary"] == "ok"
    assert captured["ticket"] == "wifi not working"
    assert captured["articles"][0]["kb_number"] == "KB0000001"


def test_recommend_endpoint_rejects_missing_ticket_description():
    client = TestClient(server.app)
    response = client.post("/recommend", json={})

    assert response.status_code == 422


def test_recommend_endpoint_rejects_missing_api_key_when_key_configured(monkeypatch):
    monkeypatch.setenv("BACKEND_API_KEY", "secret123")

    client = TestClient(server.app)
    response = client.post("/recommend", json={"ticket_description": "test"})

    assert response.status_code == 401


def test_recommend_endpoint_rejects_wrong_api_key_when_key_configured(monkeypatch):
    monkeypatch.setenv("BACKEND_API_KEY", "secret123")

    client = TestClient(server.app)
    response = client.post(
        "/recommend",
        json={"ticket_description": "test"},
        headers={"X-API-Key": "wrong"},
    )

    assert response.status_code == 401


def test_recommend_endpoint_accepts_correct_api_key_when_key_configured(monkeypatch):
    monkeypatch.setenv("BACKEND_API_KEY", "secret123")
    monkeypatch.setattr(server, "retrieve", lambda *a, **k: [])
    monkeypatch.setattr(
        server,
        "recommend",
        lambda *a, **k: {
            "issue_summary": "ok",
            "resolution_steps": [],
            "cited_kb_articles": [],
            "retrieval": [],
        },
    )

    client = TestClient(server.app)
    response = client.post(
        "/recommend",
        json={"ticket_description": "test"},
        headers={"X-API-Key": "secret123"},
    )

    assert response.status_code == 200
