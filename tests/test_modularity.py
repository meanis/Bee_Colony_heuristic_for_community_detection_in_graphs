import random
from fractions import Fraction
from functools import partial

import networkx as nx
import pytest
from networkx.algorithms.community.quality import NotAPartition

from functions import modularity

# Only floating-point rounding noise is tolerated.
approx = partial(pytest.approx, rel=1e-12)


def reference_modularity(g, partition):
    """Exact Q = 1/(2m) * sum_ij [A_ij - k_i k_j / 2m] * delta(c_i, c_j).

    Deliberately written from the textbook definition, independently of the code under test.
    A self-loop counts twice in A_ii, consistent with its contribution to the degree.
    """
    two_m = 2 * g.number_of_edges()
    community = {node: i for i, c in enumerate(partition) for node in c}
    numerator = 0
    for i in g:
        for j in g:
            if community[i] != community[j]:
                continue
            a_ij = 2 if i == j and g.has_edge(i, i) else int(g.has_edge(i, j))
            numerator += a_ij * two_m - g.degree(i) * g.degree(j)
    return Fraction(numerator, two_m * two_m)


def unweighted_karate():
    # networkx's karate club graph carries edge weights; the app's graphs never do.
    return nx.Graph(nx.karate_club_graph().edges())


def karate_club_split():
    clubs = {}
    for node, club in nx.karate_club_graph().nodes(data='club'):
        clubs.setdefault(club, set()).add(node)
    return list(clubs.values())


def random_partition(g, k, rng):
    communities = [set() for _ in range(k)]
    for node in g:
        communities[rng.randrange(k)].add(node)
    return [c for c in communities if c]


def two_bridged_triangles():
    return nx.Graph([(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3), (2, 3)])


# Two triangles joined by one edge: m = 7; each triangle has 3 internal edges and
# degree sum 7, so Q = 2 * (3/7 - (7/14)^2) = 5/14.
TRIANGLES_Q = Fraction(5, 14)
# Karate club split into its two real-world factions (17 + 17 members), computed exactly.
KARATE_SPLIT_Q = Fraction(1453, 4056)


def test_reference_reproduces_known_values():
    assert reference_modularity(two_bridged_triangles(), [{0, 1, 2}, {3, 4, 5}]) == TRIANGLES_Q
    assert reference_modularity(unweighted_karate(), karate_club_split()) == KARATE_SPLIT_Q


def test_two_bridged_triangles():
    assert modularity(two_bridged_triangles(), [{0, 1, 2}, {3, 4, 5}]) == approx(TRIANGLES_Q)


def test_karate_club_split():
    assert modularity(unweighted_karate(), karate_club_split()) == approx(KARATE_SPLIT_Q)


def test_single_community_is_zero():
    g = unweighted_karate()
    assert modularity(g, [set(g)]) == approx(0)


@pytest.mark.parametrize('k', [1, 2, 4, 8, 34])
def test_random_partitions_match_reference(k):
    g = unweighted_karate()
    rng = random.Random(k)
    for _ in range(50):
        partition = random_partition(g, k, rng)
        assert modularity(g, partition) == approx(reference_modularity(g, partition))


def test_singletons_match_reference():
    g = unweighted_karate()
    partition = [{n} for n in g]
    assert modularity(g, partition) == approx(reference_modularity(g, partition))


def test_self_loop_matches_reference():
    g = two_bridged_triangles()
    g.add_edge(0, 0)
    partition = [{0, 1, 2}, {3, 4, 5}]
    assert modularity(g, partition) == approx(reference_modularity(g, partition))


def test_isolated_node_matches_reference():
    g = nx.Graph([(0, 1), (1, 2)])
    g.add_node(3)
    partition = [{0, 1, 2}, {3}]
    assert modularity(g, partition) == approx(reference_modularity(g, partition))


def test_graph_without_edges():
    g = nx.empty_graph(3)
    assert modularity(g, [{0}, {1}, {2}]) == 0


def test_edge_weights_are_ignored():
    g = two_bridged_triangles()
    nx.set_edge_attributes(g, 5, 'weight')
    g[2][3]['weight'] = 100
    assert modularity(g, [{0, 1, 2}, {3, 4, 5}]) == approx(TRIANGLES_Q)


@pytest.mark.parametrize('partition', [
    [{0, 1, 2}, {2, 3, 4, 5}],  # node 2 in two communities
    [{0, 1, 2}, {3, 4}],        # node 5 missing
])
def test_invalid_partition_raises(partition):
    with pytest.raises(NotAPartition):
        modularity(two_bridged_triangles(), partition)
