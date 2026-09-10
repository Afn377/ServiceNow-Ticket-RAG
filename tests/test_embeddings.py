import numpy as np

from embeddings import embed_passages, embed_query


def test_embed_passages_returns_normalized_384_dim_vectors():
    vectors = embed_passages(["hello world", "another sentence"])

    assert vectors.shape == (2, 384)
    norms = np.linalg.norm(vectors, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-4)


def test_embed_query_prepends_bge_prefix_and_returns_384_dim_vector():
    vector = embed_query("wifi not connecting")

    assert vector.shape == (384,)
    assert abs(np.linalg.norm(vector) - 1.0) < 1e-4


def test_embed_query_and_embed_passages_of_same_text_differ_due_to_prefix():
    query_vec = embed_query("printer setup")
    passage_vec = embed_passages(["printer setup"])[0]

    assert not np.allclose(query_vec, passage_vec)
