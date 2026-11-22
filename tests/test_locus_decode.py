import random

import networkx as nx
import pytest

from bcsa_dcd.functions import locus_decode
from helpers import random_solution, reference_communities, unweighted_karate


def as_set(communities):
    # Compare partitions regardless of the order of communities.
    return {frozenset(c) for c in communities}


@pytest.mark.parametrize('solution, expected', [
    ([1, 0, 3, 2], [{0, 1}, {2, 3}]),        # two pairs pointing at each other
    ([1, 2, 3, 3], [{0, 1, 2, 3}]),          # a chain
    ([1, 1, 1, 1], [{0, 1, 2, 3}]),          # a star around node 1
    ([0, 1, 2], [{0}, {1}, {2}]),            # self-pointing genes are singletons
    ([1, 0, 2], [{0, 1}, {2}]),              # one singleton among a pair
    ([0], [{0}]),
    ([], []),
])
def test_hand_examples(solution, expected):
    assert as_set(locus_decode(solution)) == as_set(expected)


def test_matches_reference():
    g = unweighted_karate()
    rng = random.Random(0)
    for _ in range(200):
        solution = random_solution(g, rng)
        assert as_set(locus_decode(solution)) == reference_communities(solution)


def test_communities_are_connected_in_the_graph():
    # The point of the locus encoding: genes are neighbours, so every community is connected.
    g = unweighted_karate()
    rng = random.Random(1)
    for _ in range(200):
        for community in locus_decode(random_solution(g, rng)):
            assert nx.is_connected(g.subgraph(community))


def test_communities_form_a_partition():
    g = unweighted_karate()
    rng = random.Random(2)
    for _ in range(200):
        communities = locus_decode(random_solution(g, rng))
        members = [n for c in communities for n in c]
        assert sorted(members) == sorted(g)
