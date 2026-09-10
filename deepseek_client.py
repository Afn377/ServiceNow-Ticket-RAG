import os

from openai import OpenAI

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"


def _client(api_key: str | None = None) -> OpenAI:
    key = api_key or os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY environment variable is not set")
    return OpenAI(api_key=key, base_url=DEEPSEEK_BASE_URL)


def call_deepseek(prompt: str, api_key: str | None = None) -> str:
    client = _client(api_key)
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content
