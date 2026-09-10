import json

import numpy as np

from embeddings import embed_query

TOP_K = 5
BOOST_WEIGHT = 0.15


def rank_articles(
    ticket_vec: np.ndarray,
    article_vecs: np.ndarray,
    kb_numbers: list[str],
    categories: list[str],
    category_vecs: np.ndarray,
    category_labels: list[str],
    top_k: int = TOP_K,
    boost_weight: float = BOOST_WEIGHT,
) -> list[tuple[str, float]]:
    semantic_scores = article_vecs @ ticket_vec

    label_to_index = {label: i for i, label in enumerate(category_labels)}
    article_category_indices = np.array([label_to_index[c] for c in categories])
    article_category_vecs = category_vecs[article_category_indices]
    category_scores = article_category_vecs @ ticket_vec

    final_scores = semantic_scores + boost_weight * category_scores

    order = np.argsort(-final_scores)[:top_k]
    return [(kb_numbers[i], float(final_scores[i])) for i in order]


def load_corpus(path: str = "out/kb_corpus.json") -> dict[str, dict]:
    with open(path, encoding="utf-8") as f:
        records = json.load(f)
    return {r["kb_number"]: r for r in records}


def load_index(path: str = "out/kb_index.npz") -> dict:
    data = np.load(path, allow_pickle=False)
    return {
        "article_vecs": data["article_vecs"],
        "kb_numbers": data["kb_numbers"],
        "categories": data["categories"],
        "category_vecs": data["category_vecs"],
        "category_labels": data["category_labels"],
    }


def retrieve(
    ticket_description: str,
    corpus: dict[str, dict],
    index: dict,
    embed_query_fn=embed_query,
    top_k: int = TOP_K,
    boost_weight: float = BOOST_WEIGHT,
) -> list[dict]:
    ticket_vec = embed_query_fn(ticket_description)
    ranked = rank_articles(
        ticket_vec,
        index["article_vecs"],
        list(index["kb_numbers"]),
        list(index["categories"]),
        index["category_vecs"],
        list(index["category_labels"]),
        top_k=top_k,
        boost_weight=boost_weight,
    )

    results = []
    for kb_number, score in ranked:
        record = corpus[kb_number]
        results.append(
            {
                "kb_number": kb_number,
                "title": record["title"],
                "body": record["body"],
                "category": record["category"],
                "score": score,
            }
        )
    return results
