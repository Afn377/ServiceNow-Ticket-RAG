from recommend import build_prompt


def test_build_prompt_includes_ticket_and_articles():
    ticket = "wifi not connecting in the library"
    articles = [
        {
            "kb_number": "KB0000001",
            "title": "RUWireless Setup",
            "body": "Connect to RUWireless-Secure using your NetID.",
            "category": "Network",
            "score": 0.8,
        },
        {
            "kb_number": "KB0000002",
            "title": "VPN Setup",
            "body": "Install the VPN client.",
            "category": "Network",
            "score": 0.5,
        },
    ]

    prompt = build_prompt(ticket, articles)

    assert ticket in prompt
    assert "KB0000001" in prompt
    assert "RUWireless Setup" in prompt
    assert "Connect to RUWireless-Secure using your NetID." in prompt
    assert "KB0000002" in prompt
    assert "SUPPORTED" in prompt
    assert "INFERRED" in prompt
    assert "UNCERTAIN" in prompt
    assert "JSON" in prompt


def test_build_prompt_with_no_articles_still_includes_ticket():
    prompt = build_prompt("some ticket", [])

    assert "some ticket" in prompt
