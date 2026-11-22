import random

import pytest

from bcsa_dcd.functions import node_labeling
from helpers import random_solution, reference_communities, unweighted_karate


def assert_labels_match(labels, communities):
    """Nodes share a label exactly when they share a community."""
    assert len(labels) == sum(len(c) for c in communities)
    for community in communities:
        assert len({labels[n] for n in community}) == 1
    # One distinct label per community, so no two communities share a label.
    assert len(set(labels)) == len(communities)


@pytest.mark.parametrize('solution', [
    [1, 0, 3, 2],          # two pairs
    [1, 0, 3, 2, 5, 4],    # three pairs: a third community must not reuse a label
    [1, 2, 3, 3],          # one community
    [0, 1, 2],             # self-pointing genes: three singletons
    [1, 0, 2, 4, 3],       # a pair, a singleton, a pair
    [0],
])
def test_hand_examples(solution):
    assert_labels_match(node_labeling(solution), reference_communities(solution))


def test_empty():
    assert node_labeling([]) == []


def test_labels_are_consecutive_from_zero():
    # Current behaviour, not required by NMI (which ignores label values); keeps
    # labels usable as indices, e.g. for plot colours.
    assert sorted(set(node_labeling([1, 0, 2, 4, 3]))) == [0, 1, 2]


def test_random_solutions_match_reference():
    g = unweighted_karate()
    rng = random.Random(3)
    for _ in range(200):
        solution = random_solution(g, rng)
        labels = node_labeling(solution)
        assert_labels_match(labels, reference_communities(solution))
        assert sorted(set(labels)) == list(range(len(set(labels))))
