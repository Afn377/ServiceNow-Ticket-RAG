SHORT_BODY_WORD_THRESHOLD = 5


def analyze_quality(records: list[dict]) -> dict:
    empty_bodies = []
    short_bodies = []
    category_breakdown: dict[str, dict[str, int]] = {}

    for record in records:
        body = record["body"]
        word_count = len(body.split())

        if word_count == 0:
            empty_bodies.append(record["kb_number"])
        elif word_count < SHORT_BODY_WORD_THRESHOLD:
            short_bodies.append(record["kb_number"])

        file_counts = category_breakdown.setdefault(record["source_file"], {})
        file_counts[record["category"]] = file_counts.get(record["category"], 0) + 1

    return {
        "empty_bodies": empty_bodies,
        "short_bodies": short_bodies,
        "category_breakdown": category_breakdown,
    }
