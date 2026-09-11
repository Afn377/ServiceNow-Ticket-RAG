"""Manual evaluation harness for the ServiceNow KB retrieval tool.

Given a hand-written set of eval tickets (``eval/eval_tickets.json``), this
module measures retrieval quality with two standard IR metrics:

* Hit rate -- fraction of tickets where at least one expected KB article
  appears anywhere in the retrieved results.
* MRR -- mean reciprocal rank, where each ticket contributes
  ``1 / rank`` of the best-ranked expected KB article (0.0 on a miss).

Usage:
    python3 evaluate.py
"""

import json
import os

from retrieve import load_corpus, load_index, retrieve

EVAL_TICKETS_PATH = "eval/eval_tickets.json"
EVAL_REPORT_PATH = "eval/eval_report.json"
TOP_K = 5


def score_retrieval(
    expected_kb: list[str], retrieved_kb: list[str]
) -> tuple[bool, float]:
    """Score a single ticket's retrieved results against the expected KBs.

    ``retrieved_kb`` is in rank order (index 0 == rank 1). Returns
    ``(hit, reciprocal_rank)`` where ``hit`` is True if any expected KB number
    appears anywhere in ``retrieved_kb``, and ``reciprocal_rank`` is
    ``1 / rank`` of the best-ranked (earliest) expected KB found, or ``0.0``
    when no expected KB is found.
    """
    expected = set(expected_kb)
    for index, kb_number in enumerate(retrieved_kb):
        if kb_number in expected:
            return True, 1.0 / (index + 1)
    return False, 0.0


def load_eval_tickets(path: str = EVAL_TICKETS_PATH) -> list[dict]:
    """Load the hand-written eval ticket set, failing clearly if absent."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Eval ticket set not found at '{path}'.\n"
            "Create it first as a JSON list of objects shaped like:\n"
            '  [{"id": "T1", "ticket": "<ticket text>", "expected_kb": ["KB0000001"]}]\n'
            "Each expected_kb entry must be a kb_number present in out/kb_corpus.json."
        )
    with open(path, encoding="utf-8") as f:
        tickets = json.load(f)
    if not isinstance(tickets, list):
        raise ValueError(
            f"Expected '{path}' to contain a JSON list of eval tickets, "
            f"got {type(tickets).__name__}."
        )
    return tickets


def evaluate_tickets(
    tickets: list[dict], corpus: dict, index: dict, top_k: int = TOP_K
) -> tuple[list[dict], dict]:
    """Run every eval ticket through retrieval and score it.

    Returns ``(per_ticket_results, summary)``.
    """
    results = []
    for ticket in tickets:
        retrieved = retrieve(ticket["ticket"], corpus, index, top_k=top_k)
        retrieved_kb = [str(r["kb_number"]) for r in retrieved]
        hit, reciprocal_rank = score_retrieval(ticket["expected_kb"], retrieved_kb)
        results.append(
            {
                "id": ticket["id"],
                "ticket": ticket["ticket"],
                "expected_kb": ticket["expected_kb"],
                "retrieved_kb": retrieved_kb,
                "hit": hit,
                "reciprocal_rank": reciprocal_rank,
            }
        )

    total = len(results)
    hit_rate = sum(r["hit"] for r in results) / total if total else 0.0
    mrr = sum(r["reciprocal_rank"] for r in results) / total if total else 0.0
    summary = {
        "total_tickets": total,
        "hit_rate": hit_rate,
        "mrr": mrr,
    }
    return results, summary


def write_report(
    results: list[dict],
    summary: dict,
    path: str = EVAL_REPORT_PATH,
) -> None:
    """Write per-ticket results plus the summary to a JSON report."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)
        f.write("\n")


def print_summary(results: list[dict], summary: dict) -> None:
    """Print a human-readable summary, including every missed ticket."""
    total = summary["total_tickets"]
    print(f"Eval tickets: {total}")
    print(f"Hit rate: {summary['hit_rate'] * 100:.1f}%")
    print(f"MRR: {summary['mrr']:.3f}")

    misses = [r for r in results if not r["hit"]]
    if misses:
        print(f"\nMissed tickets ({len(misses)}):")
        for r in misses:
            print(f"  - [{r['id']}] {r['ticket']}")
            print(f"      expected: {r['expected_kb']}  retrieved: {r['retrieved_kb']}")
    else:
        print("\nNo missed tickets.")


def main() -> None:
    tickets = load_eval_tickets()
    corpus = load_corpus()
    index = load_index()

    results, summary = evaluate_tickets(tickets, corpus, index)
    write_report(results, summary)
    print_summary(results, summary)
    print(f"\nReport written to {EVAL_REPORT_PATH}")


if __name__ == "__main__":
    main()
