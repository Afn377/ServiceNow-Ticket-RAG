import json

import numpy as np

from embeddings import embed_query

TOP_K = 5
BOOST_WEIGHT = 0.10
RRF_K = 60


def _rank_positions(scores: np.ndarray) -> np.ndarray:
    """Return 1-indexed ranks per element, where rank 1 is the highest score."""
    order = np.argsort(-scores)
    ranks = np.empty(len(scores), dtype=int)
    ranks[order] = np.arange(1, len(scores) + 1)
    return ranks


def reciprocal_rank_fusion(
    rank_lists: list[np.ndarray], k: int = 60
) -> np.ndarray:
    """Sum 1/(k + rank) element-wise across all provided rank lists."""
    fused = np.zeros(len(rank_lists[0]), dtype=float)
    for ranks in rank_lists:
        fused += 1.0 / (k + ranks)
    return fused


def rank_articles(
    ticket_vec: np.ndarray,
    article_vecs: np.ndarray,
    kb_numbers: list[str],
    categories: list[str],
    category_vecs: np.ndarray,
    category_labels: list[str],
    bm25_index,
    query_tokens: list[str],
    top_k: int = TOP_K,
    boost_weight: float = BOOST_WEIGHT,
) -> list[tuple[str, float]]:
    semantic_scores = article_vecs @ ticket_vec
    semantic_ranks = _rank_positions(semantic_scores)

    bm25_scores = np.array(bm25_index.get_scores(query_tokens))
    bm25_ranks = _rank_positions(bm25_scores)

    fused_scores = reciprocal_rank_fusion([semantic_ranks, bm25_ranks], k=RRF_K)

    label_to_index = {label: i for i, label in enumerate(category_labels)}
    article_category_indices = np.array([label_to_index[c] for c in categories])
    article_category_vecs = category_vecs[article_category_indices]
    category_scores = article_category_vecs @ ticket_vec

    final_scores = fused_scores + boost_weight * category_scores

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


_bm25_index_cache = {}


def _get_bm25_index(corpus: dict[str, dict], kb_numbers: list[str]):
    """Build (and cache) a BM25 index keyed by corpus object identity.

    Keyed by ``id(corpus)`` so distinct corpus dicts (e.g. separate fixtures
    within one pytest process) never reuse a stale index.
    """
    from rank_bm25 import BM25Okapi

    cache_key = id(corpus)
    if cache_key not in _bm25_index_cache:
        texts = [f"{corpus[kb]['title']}\n{corpus[kb]['body']}" for kb in kb_numbers]
        tokenized = [text.lower().split() for text in texts]
        _bm25_index_cache[cache_key] = BM25Okapi(tokenized)
    return _bm25_index_cache[cache_key]


def retrieve(
    ticket_description: str,
    corpus: dict[str, dict],
    index: dict,
    embed_query_fn=embed_query,
    top_k: int = TOP_K,
    boost_weight: float = BOOST_WEIGHT,
) -> list[dict]:
    ticket_vec = embed_query_fn(ticket_description)
    kb_numbers = list(index["kb_numbers"])
    bm25_index = _get_bm25_index(corpus, kb_numbers)
    query_tokens = ticket_description.lower().split()
    ranked = rank_articles(
        ticket_vec,
        index["article_vecs"],
        kb_numbers,
        list(index["categories"]),
        index["category_vecs"],
        list(index["category_labels"]),
        bm25_index,
        query_tokens,
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
