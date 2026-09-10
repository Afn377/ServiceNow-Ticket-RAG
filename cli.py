import json
import sys

from deepseek_client import call_deepseek
from recommend import recommend
from retrieve import load_corpus, load_index, retrieve


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        ticket_description = " ".join(argv[1:])
    else:
        ticket_description = sys.stdin.read().strip()

    corpus = load_corpus()
    index = load_index()

    articles = retrieve(ticket_description, corpus, index)
    result = recommend(ticket_description, articles, call_llm=call_deepseek)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(sys.argv)
