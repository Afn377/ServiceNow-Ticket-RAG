import numpy as np

from retrieve import rank_articles


def test_rank_articles_orders_by_semantic_score_when_no_boost():
    ticket_vec = np.array([1.0, 0.0])
    article_vecs = np.array([
        [1.0, 0.0],   # KB_HIGH_SEM: semantic_score = 1.0
        [0.0, 1.0],   # KB_LOW_SEM: semantic_score = 0.0
    ])
    kb_numbers = ["KB_HIGH_SEM", "KB_LOW_SEM"]
    categories = ["catB", "catA"]
    category_labels = ["catA", "catB"]
    category_vecs = np.array([
        [1.0, 0.0],  # catA
        [0.0, 1.0],  # catB
    ])

    results = rank_articles(
        ticket_vec, article_vecs, kb_numbers, categories,
        category_vecs, category_labels, top_k=2, boost_weight=0.0,
    )

    assert [kb for kb, _ in results] == ["KB_HIGH_SEM", "KB_LOW_SEM"]
    assert results[0][1] == 1.0
    assert results[1][1] == 0.0


def test_rank_articles_boost_can_flip_ranking_order():
    ticket_vec = np.array([1.0, 0.0])
    article_vecs = np.array([
        [1.0, 0.0],   # KB_HIGH_SEM: semantic_score = 1.0, category catB (no match)
        [0.0, 1.0],   # KB_LOW_SEM: semantic_score = 0.0, category catA (matches ticket)
    ])
    kb_numbers = ["KB_HIGH_SEM", "KB_LOW_SEM"]
    categories = ["catB", "catA"]
    category_labels = ["catA", "catB"]
    category_vecs = np.array([
        [1.0, 0.0],  # catA - matches ticket_vec exactly
        [0.0, 1.0],  # catB - orthogonal to ticket_vec
    ])

    results = rank_articles(
        ticket_vec, article_vecs, kb_numbers, categories,
        category_vecs, category_labels, top_k=2, boost_weight=2.0,
    )

    assert [kb for kb, _ in results] == ["KB_LOW_SEM", "KB_HIGH_SEM"]
    assert results[0][1] == 2.0   # 0.0 + 2.0 * 1.0
    assert results[1][1] == 1.0   # 1.0 + 2.0 * 0.0


def test_rank_articles_respects_top_k():
    ticket_vec = np.array([1.0, 0.0])
    article_vecs = np.array([[1.0, 0.0], [0.9, 0.1], [0.0, 1.0]])
    kb_numbers = ["A", "B", "C"]
    categories = ["catA", "catA", "catA"]
    category_labels = ["catA"]
    category_vecs = np.array([[1.0, 0.0]])

    results = rank_articles(
        ticket_vec, article_vecs, kb_numbers, categories,
        category_vecs, category_labels, top_k=2, boost_weight=0.0,
    )

    assert len(results) == 2
    assert [kb for kb, _ in results] == ["A", "B"]
