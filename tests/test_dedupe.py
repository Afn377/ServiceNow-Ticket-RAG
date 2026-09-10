from kb_parser.dedupe import dedupe_records


def test_dedupe_keeps_unique_records_unchanged():
    records = [
        {"kb_number": "KB0000001", "body": "short", "audience_tier": "main_hd"},
        {"kb_number": "KB0000002", "body": "other", "audience_tier": "public"},
    ]

    result = dedupe_records(records)

    assert len(result) == 2
    assert result[0]["audience_tier"] == ["main_hd"]
    assert result[1]["audience_tier"] == ["public"]


def test_dedupe_merges_duplicate_kb_number_keeping_richest_body():
    records = [
        {"kb_number": "KB0000001", "body": "short body", "audience_tier": "main_hd"},
        {
            "kb_number": "KB0000001",
            "body": "a much longer and richer body with more detail",
            "audience_tier": "public",
        },
    ]

    result = dedupe_records(records)

    assert len(result) == 1
    merged = result[0]
    assert merged["body"] == "a much longer and richer body with more detail"
    assert merged["audience_tier"] == ["main_hd", "public"]
