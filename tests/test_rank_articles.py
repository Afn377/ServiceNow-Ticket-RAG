import numpy as np
import pytest
from rank_bm25 import BM25Okapi

from retrieve import _rank_positions, rank_articles, reciprocal_rank_fusion


def test_rank_positions_ranks_highest_score_as_1():
    scores = np.array([0.5, 0.9, 0.1])

    ranks = _rank_positions(scores)

    assert list(ranks) == [2, 1, 3]


def test_reciprocal_rank_fusion_sums_reciprocal_ranks_across_lists():
    ranks_a = np.array([1, 2, 3])
    ranks_b = np.array([3, 1, 2])

    fused = reciprocal_rank_fusion([ranks_a, ranks_b], k=60)

    expected = [1 / 61 + 1 / 63, 1 / 62 + 1 / 61, 1 / 63 + 1 / 62]
    assert fused == pytest.approx(expected)


def test_rank_articles_bm25_signal_can_outrank_top_semantic_match():
    # Article A: best semantic match (rank 1), but zero keyword overlap with
    # the query (bm25 rank 3, the worst).
    # Article B: middling semantic match (rank 2), but the strongest keyword
    # match (bm25 rank 1) - RRF fusion should let it win overall.
    # Article C: worst semantic match (rank 3), middling keyword match (bm25 rank 2).
    ticket_vec = np.array([1.0, 0.0])
    article_vecs = np.array([
        [1.0, 0.0],  # A
        [0.5, 0.0],  # B
        [0.1, 0.0],  # C
    ])
    kb_numbers = ["A", "B", "C"]
    categories = ["cat", "cat", "cat"]
    category_labels = ["cat"]
    category_vecs = np.array([[0.0, 0.0]])  # no category signal (boost_weight=0 anyway)

    corpus_texts = [
        "zzz yyy xxx unrelated content here",  # A: no overlap with query
        "alpha beta gamma alpha beta gamma",  # B: strong overlap
        "alpha beta random filler text",  # C: partial overlap
    ]
    bm25_index = BM25Okapi([text.lower().split() for text in corpus_texts])
    query_tokens = "alpha beta gamma".split()

    results = rank_articles(
        ticket_vec, article_vecs, kb_numbers, categories,
        category_vecs, category_labels, bm25_index, query_tokens,
        top_k=3, boost_weight=0.0,
    )

    assert [kb for kb, _ in results] == ["B", "A", "C"]


def test_rank_articles_respects_top_k():
    ticket_vec = np.array([1.0, 0.0])
    article_vecs = np.array([[1.0, 0.0], [0.9, 0.1], [0.0, 1.0]])
    kb_numbers = ["A", "B", "C"]
    categories = ["cat", "cat", "cat"]
    category_labels = ["cat"]
    category_vecs = np.array([[0.0, 0.0]])

    corpus_texts = ["same text", "same text", "same text"]
    bm25_index = BM25Okapi([text.lower().split() for text in corpus_texts])
    query_tokens = "same text".split()

    results = rank_articles(
        ticket_vec, article_vecs, kb_numbers, categories,
        category_vecs, category_labels, bm25_index, query_tokens,
        top_k=2, boost_weight=0.0,
    )

    assert len(results) == 2
    assert [kb for kb, _ in results] == ["A", "B"]


def test_rank_articles_category_boost_still_applies_on_top_of_fusion():
    ticket_vec = np.array([1.0, 0.0])
    article_vecs = np.array([
        [1.0, 0.0],  # KB_HIGH_SEM: best on both semantic and bm25, no category match
        [0.0, 1.0],  # KB_LOW_SEM: worst on both, but category matches ticket
    ])
    kb_numbers = ["KB_HIGH_SEM", "KB_LOW_SEM"]
    categories = ["catB", "catA"]
    category_labels = ["catA", "catB"]
    category_vecs = np.array([
        [1.0, 0.0],  # catA - matches ticket_vec exactly
        [0.0, 1.0],  # catB - orthogonal to ticket_vec
    ])

    corpus_texts = ["alpha beta gamma", "zzz yyy xxx"]
    bm25_index = BM25Okapi([text.lower().split() for text in corpus_texts])
    query_tokens = "alpha beta gamma".split()

    results_no_boost = rank_articles(
        ticket_vec, article_vecs, kb_numbers, categories,
        category_vecs, category_labels, bm25_index, query_tokens,
        top_k=2, boost_weight=0.0,
    )
    assert [kb for kb, _ in results_no_boost] == ["KB_HIGH_SEM", "KB_LOW_SEM"]

    results_with_boost = rank_articles(
        ticket_vec, article_vecs, kb_numbers, categories,
        category_vecs, category_labels, bm25_index, query_tokens,
        top_k=2, boost_weight=10.0,
    )
    assert [kb for kb, _ in results_with_boost] == ["KB_LOW_SEM", "KB_HIGH_SEM"]
