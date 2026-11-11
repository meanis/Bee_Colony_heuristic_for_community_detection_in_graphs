import random

import networkx as nx
import pytest

from functions import locus_decode


def reference_communities(solution):
    """Union-find over the edges (i, solution[i]); independent of networkx."""
    parent = list(range(len(solution)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, j in enumerate(solution):
        parent[find(i)] = find(j)
    groups = {}
    for i in range(len(solution)):
        groups.setdefault(find(i), set()).add(i)
    return {frozenset(g) for g in groups.values()}


def as_set(communities):
    # Compare partitions regardless of the order of communities.
    return {frozenset(c) for c in communities}


def unweighted_karate():
    return nx.Graph(nx.karate_club_graph().edges())


def random_solution(g, rng):
    # Same construction as the app: each gene is a random neighbour of its node.
    return [rng.choice(list(g[i])) for i in range(g.number_of_nodes())]


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
