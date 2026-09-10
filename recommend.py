import json


def build_prompt(ticket_description: str, articles: list[dict]) -> str:
    articles_block = "\n\n".join(
        f"KB Article {a['kb_number']} - {a['title']}\n{a['body']}" for a in articles
    )

    return f"""You are a support-ticket triage assistant for a university IT help desk.
You are given a ticket description and a set of retrieved Knowledge Base (KB) articles.
Use ONLY the retrieved KB articles below as your source of truth - do not use outside knowledge.

Ticket description:
{ticket_description}

Retrieved KB articles:
{articles_block}

Respond with ONLY a JSON object (no other text, no markdown fences) matching this exact shape:
{{
  "issue_summary": "string - inferred issue/cause",
  "resolution_steps": [
    {{
      "step": "string - one concrete action",
      "grounding": "SUPPORTED | INFERRED | UNCERTAIN",
      "cited_kb": ["KB0012345"] or null
    }}
  ],
  "cited_kb_articles": ["KB0012345"]
}}

Grounding rules:
- SUPPORTED: this step is directly stated in a retrieved KB article.
- INFERRED: this step is a reasonable extrapolation beyond what the retrieved articles literally say.
- UNCERTAIN: this step is not well backed by the retrieved articles.
Never label a claim SUPPORTED unless it is directly backed by the retrieved text.
"""

VALID_GROUNDING = {"SUPPORTED", "INFERRED", "UNCERTAIN"}


class SchemaValidationError(Exception):
    pass


def _strip_markdown_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


def parse_response(raw_text: str) -> dict:
    cleaned = _strip_markdown_fences(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise SchemaValidationError(f"response is not valid JSON: {e}") from e

    if not isinstance(data, dict):
        raise SchemaValidationError("response JSON is not an object")

    for key in ("issue_summary", "resolution_steps", "cited_kb_articles"):
        if key not in data:
            raise SchemaValidationError(f"missing required field: {key}")

    if not isinstance(data["resolution_steps"], list):
        raise SchemaValidationError("resolution_steps must be a list")

    for step in data["resolution_steps"]:
        if not isinstance(step, dict) or "step" not in step or "grounding" not in step:
            raise SchemaValidationError("resolution_steps entry missing 'step' or 'grounding'")
        if step["grounding"] not in VALID_GROUNDING:
            raise SchemaValidationError(f"invalid grounding value: {step['grounding']!r}")

    if not isinstance(data["cited_kb_articles"], list):
        raise SchemaValidationError("cited_kb_articles must be a list")

    return data
