from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

BGE_MODEL_NAME = "BAAI/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(BGE_MODEL_NAME)


def embed_passages(texts: list[str]) -> np.ndarray:
    return _model().encode(texts, normalize_embeddings=True, convert_to_numpy=True)


def embed_query(text: str) -> np.ndarray:
    return _model().encode(
        QUERY_PREFIX + text, normalize_embeddings=True, convert_to_numpy=True
    )
