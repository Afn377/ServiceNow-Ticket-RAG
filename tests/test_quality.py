from kb_parser.quality import analyze_quality


def test_analyze_quality_flags_empty_and_short_bodies():
    records = [
        {"kb_number": "KB0000001", "body": "", "category": "Network", "source_file": "main.txt"},
        {"kb_number": "KB0000002", "body": "too short", "category": "Network", "source_file": "main.txt"},
        {
            "kb_number": "KB0000003",
            "body": "this body has plenty of words to be considered a real article",
            "category": "Network",
            "source_file": "main.txt",
        },
    ]

    report = analyze_quality(records)

    assert report["empty_bodies"] == ["KB0000001"]
    assert report["short_bodies"] == ["KB0000002"]
    assert "KB0000003" not in report["short_bodies"]


def test_analyze_quality_builds_category_breakdown_per_source_file():
    records = [
        {"kb_number": "KB0000001", "body": "x " * 10, "category": "Network", "source_file": "main.txt"},
        {"kb_number": "KB0000002", "body": "x " * 10, "category": "Network", "source_file": "main.txt"},
        {"kb_number": "KB0000003", "body": "x " * 10, "category": "Printing", "source_file": "public.txt"},
    ]

    report = analyze_quality(records)

    assert report["category_breakdown"]["main.txt"]["Network"] == 2
    assert report["category_breakdown"]["public.txt"]["Printing"] == 1
