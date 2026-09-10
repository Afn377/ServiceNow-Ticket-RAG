import json

import cli


def test_main_wires_ticket_through_retrieve_and_recommend_and_prints_json(monkeypatch, capsys):
    monkeypatch.setattr(cli, "load_corpus", lambda: {"corpus": True})
    monkeypatch.setattr(cli, "load_index", lambda: {"index": True})

    captured_args = {}

    def fake_retrieve(ticket_description, corpus, index):
        captured_args["ticket"] = ticket_description
        captured_args["corpus"] = corpus
        captured_args["index"] = index
        return [
            {"kb_number": "KB0000001", "title": "T", "body": "B", "category": "C", "score": 0.9}
        ]

    def fake_recommend(ticket_description, articles, call_llm):
        return {
            "issue_summary": "ok",
            "resolution_steps": [],
            "cited_kb_articles": [],
            "retrieval": [],
        }

    monkeypatch.setattr(cli, "retrieve", fake_retrieve)
    monkeypatch.setattr(cli, "recommend", fake_recommend)

    cli.main(["cli.py", "wifi", "not", "working"])

    assert captured_args["ticket"] == "wifi not working"
    assert captured_args["corpus"] == {"corpus": True}
    assert captured_args["index"] == {"index": True}

    printed = capsys.readouterr().out
    result = json.loads(printed)
    assert result["issue_summary"] == "ok"
