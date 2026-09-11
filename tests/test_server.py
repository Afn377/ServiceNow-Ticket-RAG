from fastapi.testclient import TestClient

import server


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
