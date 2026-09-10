import pytest

from recommend import SchemaValidationError, parse_response

VALID_RESPONSE = """{
  "issue_summary": "WiFi connection issue",
  "resolution_steps": [
    {"step": "Connect to RUWireless-Secure", "grounding": "SUPPORTED", "cited_kb": ["KB0000001"]}
  ],
  "cited_kb_articles": ["KB0000001"]
}"""


def test_parse_response_accepts_valid_json():
    result = parse_response(VALID_RESPONSE)

    assert result["issue_summary"] == "WiFi connection issue"
    assert result["resolution_steps"][0]["grounding"] == "SUPPORTED"
    assert result["cited_kb_articles"] == ["KB0000001"]


def test_parse_response_strips_markdown_code_fences():
    wrapped = "```json\n" + VALID_RESPONSE + "\n```"

    result = parse_response(wrapped)

    assert result["issue_summary"] == "WiFi connection issue"


def test_parse_response_rejects_non_json_text():
    with pytest.raises(SchemaValidationError):
        parse_response("Sorry, I can't help with that.")


def test_parse_response_rejects_missing_issue_summary():
    bad = '{"resolution_steps": [], "cited_kb_articles": []}'

    with pytest.raises(SchemaValidationError):
        parse_response(bad)


def test_parse_response_rejects_missing_resolution_steps():
    bad = '{"issue_summary": "x", "cited_kb_articles": []}'

    with pytest.raises(SchemaValidationError):
        parse_response(bad)


def test_parse_response_rejects_invalid_grounding_value():
    bad = """{
      "issue_summary": "x",
      "resolution_steps": [{"step": "do thing", "grounding": "MAYBE", "cited_kb": null}],
      "cited_kb_articles": []
    }"""

    with pytest.raises(SchemaValidationError):
        parse_response(bad)


def test_parse_response_rejects_missing_cited_kb_articles():
    bad = '{"issue_summary": "x", "resolution_steps": []}'

    with pytest.raises(SchemaValidationError):
        parse_response(bad)
