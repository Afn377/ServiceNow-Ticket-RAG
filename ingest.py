import json
from pathlib import Path

from kb_parser.dedupe import dedupe_records
from kb_parser.loader import read_kb_file
from kb_parser.quality import analyze_quality
from kb_parser.records import parse_record, split_records

RAW_DIR = Path("raw")
OUT_DIR = Path("out")

FILES_TO_TIER = {
    "Public Knowledge txt - updated 07-23-2026.txt": "public",
    "Help Desk and Labs Knowledge txt - updated 07-23-2026.txt": "main_hd",
    "Help Desk and Labs Knowledge txt - Level 2 Specialists and AH - updated 07-23-26.txt": "l2_ah",
    "Help Desk and Labs Knowledge txt - FT - updated 07-23-26.txt": "ft",
    "Help Desk and Labs Knowledge txt - Supervisors - updated 07-23-26.txt": "supervisors",
}


def ingest() -> None:
    all_records = []
    parse_failures = []
    files_seen = set()

    for filename, tier in FILES_TO_TIER.items():
        path = RAW_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"expected KB export not found: {path}")
        files_seen.add(filename)

        text = read_kb_file(path)
        for raw_record in split_records(text):
            try:
                record = parse_record(raw_record)
            except Exception as exc:  # noqa: BLE001 - captured for the quality report
                parse_failures.append({"source_file": filename, "error": str(exc), "raw": raw_record[:120]})
                continue
            record["source_file"] = filename
            record["audience_tier"] = tier
            all_records.append(record)

    deduped = dedupe_records(all_records)
    quality = analyze_quality(all_records)

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "kb_corpus.json").write_text(json.dumps(deduped, indent=2, ensure_ascii=False))

    report_lines = [
        "# KB Corpus Data Quality Report",
        "",
        f"- Files processed: {len(files_seen)}",
        f"- Raw records parsed: {len(all_records)}",
        f"- Unique KB articles after dedup: {len(deduped)}",
        f"- Parse failures: {len(parse_failures)}",
        f"- Empty bodies: {len(quality['empty_bodies'])}",
        f"- Suspiciously short bodies (<{5} words): {len(quality['short_bodies'])}",
        "",
        "## Records per source file",
    ]
    counts_by_file: dict[str, int] = {}
    for record in all_records:
        counts_by_file[record["source_file"]] = counts_by_file.get(record["source_file"], 0) + 1
    for filename, tier in FILES_TO_TIER.items():
        report_lines.append(f"- {filename} ({tier}): {counts_by_file.get(filename, 0)}")

    if parse_failures:
        report_lines.append("")
        report_lines.append("## Parse failures")
        for failure in parse_failures:
            report_lines.append(f"- {failure['source_file']}: {failure['error']} -- {failure['raw']!r}")

    if quality["empty_bodies"]:
        report_lines.append("")
        report_lines.append("## Empty-body articles")
        for kb in quality["empty_bodies"]:
            report_lines.append(f"- {kb}")

    if quality["short_bodies"]:
        report_lines.append("")
        report_lines.append("## Suspiciously short articles")
        for kb in quality["short_bodies"]:
            report_lines.append(f"- {kb}")

    report_lines.append("")
    report_lines.append("## Category breakdown per source file")
    for filename, categories in quality["category_breakdown"].items():
        report_lines.append(f"### {filename}")
        for category, count in sorted(categories.items(), key=lambda kv: -kv[1]):
            report_lines.append(f"- {category}: {count}")

    (OUT_DIR / "data_quality_report.md").write_text("\n".join(report_lines))

    print(f"Parsed {len(all_records)} records from {len(files_seen)} files -> {len(deduped)} unique articles")
    print(f"Parse failures: {len(parse_failures)}")


if __name__ == "__main__":
    ingest()
