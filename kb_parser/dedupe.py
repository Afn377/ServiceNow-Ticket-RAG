def dedupe_records(records: list[dict]) -> list[dict]:
    by_kb_number: dict[str, dict] = {}
    order: list[str] = []

    for record in records:
        kb_number = record["kb_number"]
        tier = record["audience_tier"]

        if kb_number not in by_kb_number:
            merged = dict(record)
            merged["audience_tier"] = [tier]
            by_kb_number[kb_number] = merged
            order.append(kb_number)
            continue

        existing = by_kb_number[kb_number]
        existing["audience_tier"].append(tier)
        if len(record["body"]) > len(existing["body"]):
            richest_tiers = existing["audience_tier"]
            existing.clear()
            existing.update(record)
            existing["audience_tier"] = richest_tiers

    return [by_kb_number[kb_number] for kb_number in order]
