import json

import numpy as np

from embeddings import embed_passages


def build_index(
    corpus_path: str = "out/kb_corpus.json", index_path: str = "out/kb_index.npz"
) -> None:
    with open(corpus_path, encoding="utf-8") as f:
        records = json.load(f)

    kb_numbers = [r["kb_number"] for r in records]
    categories = [r["category"] for r in records]
    texts = [f"{r['title']}\n{r['body']}" for r in records]

    article_vecs = embed_passages(texts)

    category_labels = sorted(set(categories))
    category_vecs = embed_passages(category_labels)

    np.savez(
        index_path,
        article_vecs=article_vecs,
        kb_numbers=np.array(kb_numbers),
        categories=np.array(categories),
        category_labels=np.array(category_labels),
        category_vecs=category_vecs,
    )


if __name__ == "__main__":
    build_index()
    print("Index written to out/kb_index.npz")
