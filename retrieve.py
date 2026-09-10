import numpy as np

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
