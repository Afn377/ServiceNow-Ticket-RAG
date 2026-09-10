from recommend import recommend

GOOD_JSON = '{"issue_summary": "x", "resolution_steps": [], "cited_kb_articles": []}'
BAD_JSON = "not json at all"


def _articles(score=0.8):
    return [
        {"kb_number": "KB0000001", "title": "T", "body": "B", "category": "C", "score": score}
    ]


def test_recommend_returns_insufficient_evidence_when_top_score_below_min():
    result = recommend("some ticket", _articles(score=0.1), call_llm=lambda p: GOOD_JSON)

    assert result["insufficient_evidence"] is True
    assert result["resolution_steps"] == []


def test_recommend_returns_insufficient_evidence_when_no_articles():
    result = recommend("some ticket", [], call_llm=lambda p: GOOD_JSON)

    assert result["insufficient_evidence"] is True


def test_recommend_parses_good_first_response():
    result = recommend("some ticket", _articles(), call_llm=lambda p: GOOD_JSON)

    assert result["issue_summary"] == "x"
    assert result["retrieval"][0]["kb_number"] == "KB0000001"
    assert "insufficient_evidence" not in result


def test_recommend_retries_once_on_bad_json_then_succeeds():
    calls = []

    def fake_call_llm(prompt):
        calls.append(prompt)
        return BAD_JSON if len(calls) == 1 else GOOD_JSON

    result = recommend("some ticket", _articles(), call_llm=fake_call_llm)

    assert len(calls) == 2
    assert result["issue_summary"] == "x"


def test_recommend_flags_schema_error_after_two_bad_responses():
    result = recommend("some ticket", _articles(), call_llm=lambda p: BAD_JSON)

    assert result["schema_error"] is True
    assert result["raw_response"] == BAD_JSON
