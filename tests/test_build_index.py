import json

import numpy as np

from build_index import build_index


def test_build_index_writes_expected_arrays(tmp_path):
    corpus = [
        {"kb_number": "KB0000001", "category": "Network", "title": "VPN Setup", "body": "How to set up VPN."},
        {"kb_number": "KB0000002", "category": "Printing", "title": "Printer Setup", "body": "How to add a printer."},
        {"kb_number": "KB0000003", "category": "Network", "title": "WiFi Setup", "body": "How to connect to WiFi."},
    ]
    corpus_path = tmp_path / "kb_corpus.json"
    corpus_path.write_text(json.dumps(corpus))
    index_path = tmp_path / "kb_index.npz"

    build_index(str(corpus_path), str(index_path))

    data = np.load(index_path, allow_pickle=False)
    assert data["article_vecs"].shape == (3, 384)
    assert list(data["kb_numbers"]) == ["KB0000001", "KB0000002", "KB0000003"]
    assert list(data["categories"]) == ["Network", "Printing", "Network"]
    assert sorted(data["category_labels"].tolist()) == ["Network", "Printing"]
    assert data["category_vecs"].shape == (2, 384)
