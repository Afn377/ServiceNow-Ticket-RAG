from evaluate import score_retrieval


def test_score_retrieval_hit_at_rank_1():
    hit, reciprocal_rank = score_retrieval(
        expected_kb=["KB0000001"],
        retrieved_kb=["KB0000001", "KB0000002", "KB0000003"],
    )

    assert hit is True
    assert reciprocal_rank == 1.0


def test_score_retrieval_hit_at_rank_5():
    hit, reciprocal_rank = score_retrieval(
        expected_kb=["KB0000005"],
        retrieved_kb=["KB0000001", "KB0000002", "KB0000003", "KB0000004", "KB0000005"],
    )

    assert hit is True
    assert reciprocal_rank == 0.2


def test_score_retrieval_miss():
    hit, reciprocal_rank = score_retrieval(
        expected_kb=["KB0009999"],
        retrieved_kb=["KB0000001", "KB0000002", "KB0000003"],
    )

    assert hit is False
    assert reciprocal_rank == 0.0


def test_score_retrieval_multiple_expected_uses_best_rank():
    hit, reciprocal_rank = score_retrieval(
        expected_kb=["KB0000003", "KB0000001"],
        retrieved_kb=["KB0000002", "KB0000001", "KB0000003"],
    )

    assert hit is True
    assert reciprocal_rank == 0.5
