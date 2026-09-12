import json

import numpy as np

from retrieve import load_corpus, load_index, retrieve


def test_load_corpus_indexes_by_kb_number(tmp_path):
    corpus = [
        {"kb_number": "KB0000001", "category": "Network", "title": "VPN", "body": "VPN body"},
    ]
    path = tmp_path / "kb_corpus.json"
    path.write_text(json.dumps(corpus))

    result = load_corpus(str(path))

    assert result == {"KB0000001": corpus[0]}


def test_load_index_returns_expected_keys(tmp_path):
    path = tmp_path / "kb_index.npz"
    np.savez(
        path,
        article_vecs=np.array([[1.0, 0.0]]),
        kb_numbers=np.array(["KB0000001"]),
        categories=np.array(["Network"]),
        category_labels=np.array(["Network"]),
        category_vecs=np.array([[1.0, 0.0]]),
    )

    result = load_index(str(path))

    assert list(result["kb_numbers"]) == ["KB0000001"]
    assert result["article_vecs"].shape == (1, 2)


def test_retrieve_joins_ranked_results_with_corpus_fields():
    corpus = {
        "KB0000001": {"kb_number": "KB0000001", "category": "Network", "title": "VPN Setup", "body": "How to VPN."},
        "KB0000002": {"kb_number": "KB0000002", "category": "Printing", "title": "Printer Setup", "body": "How to print."},
    }
    index = {
        "article_vecs": np.array([[1.0, 0.0], [0.0, 1.0]]),
        "kb_numbers": np.array(["KB0000001", "KB0000002"]),
        "categories": np.array(["Network", "Printing"]),
        "category_labels": np.array(["Network", "Printing"]),
        "category_vecs": np.array([[1.0, 0.0], [0.0, 1.0]]),
    }

    def fake_embed_query(text):
        return np.array([1.0, 0.0])

    results = retrieve(
        "vpn issue", corpus, index, embed_query_fn=fake_embed_query, top_k=2, boost_weight=0.0
    )

    assert results[0]["kb_number"] == "KB0000001"
    assert results[0]["title"] == "VPN Setup"
    assert results[0]["body"] == "How to VPN."
    assert results[0]["score"] == 1.0
    assert results[1]["kb_number"] == "KB0000002"
