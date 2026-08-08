import pytest
from ai.retrieval.retriever import _cosine


def test_cosine_identical_is_one():
    assert _cosine([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)


def test_cosine_orthogonal_is_zero():
    assert _cosine([1, 0], [0, 1]) == pytest.approx(0.0)


def test_cosine_opposite_is_negative():
    assert _cosine([1, 0], [-1, 0]) == pytest.approx(-1.0)


def test_cosine_zero_vector_no_div_zero():
    assert _cosine([0, 0, 0], [1, 2, 3]) == 0.0


def test_cosine_ranks_similar_higher():
    q = [1, 1, 1, 1]
    similar = [1, 1, 1, 1]
    unrelated = [1, -1, 1, -1]
    assert _cosine(q, similar) > _cosine(q, unrelated)
