import math
import random
from collections import Counter
from functools import partial

import pytest

from bcsa_dcd.functions import NMI
from helpers import random_solution, reference_labels, unweighted_karate

# Only floating-point rounding noise is tolerated.
approx = partial(pytest.approx, rel=1e-12)


def reference_nmi(a, b):
    """NMI = 2 * I(A; B) / (H(A) + H(B)), from the textbook definition.

    This is scikit-learn's default (average_method='arithmetic').

    Zero entropy: a labeling with a single community has H = 0. If only one side is
    constant, the formula is fine: I(A; B) = 0, so NMI = 0. If both are, H(A) + H(B) = 0
    and the formula is 0/0. Like scikit-learn, we call that a perfect match (1.0): neither
    labeling splits the nodes, so they agree.
    """
    n = len(a)
    count_a, count_b, joint = Counter(a), Counter(b), Counter(zip(a, b))
    h_a = -sum(c / n * math.log(c / n) for c in count_a.values())
    h_b = -sum(c / n * math.log(c / n) for c in count_b.values())
    if h_a + h_b == 0:  # exact: a constant labeling's entropy is -1 * log(1) = 0.0
        return 1.0
    mi = sum(c / n * math.log(c * n / (count_a[x] * count_b[y])) for (x, y), c in joint.items())
    return 2 * mi / (h_a + h_b)


PAIRS = [1, 0, 3, 2]       # {0, 1} {2, 3}
CROSSED = [2, 3, 0, 1]     # {0, 2} {1, 3}: independent of PAIRS
ONE_COMMUNITY = [1, 2, 3, 0]


def test_identical_solutions():
    assert NMI(PAIRS, PAIRS) == approx(1)


def test_same_partition_different_encoding():
    # A triangle encoded two ways is the same community.
    assert NMI([1, 2, 0], [2, 0, 1]) == approx(1)


def test_independent_partitions():
    assert NMI(PAIRS, CROSSED) == approx(0)


@pytest.mark.parametrize(
    "a, b, expected",
    [
        # Both constant: H(A) + H(B) = 0, the 0/0 case. Defined as a perfect match.
        ([0], [0], 1),                                  # a single node
        (ONE_COMMUNITY, [3, 0, 1, 2], 1),
        # Only one side constant: I(A; B) = 0, H(A) + H(B) > 0, so NMI = 0.
        (ONE_COMMUNITY, PAIRS, 0),
        (PAIRS, ONE_COMMUNITY, 0),
        ([0, 1, 2], [1, 2, 0], 0),                      # all singletons vs one triangle
        # B is not constant, but becomes constant once cut to A's length:
        # B = {0, 1} {2}, compared on nodes 0-1 only, which are both in one community.
        ([1, 0], [1, 0, 2], 1),
    ],
)
def test_zero_entropy(a, b, expected):
    la, lb = reference_labels(a), reference_labels(b)[:len(a)]
    assert reference_nmi(la, lb) == approx(expected)
    assert NMI(a, b) == approx(expected)  # approx also rejects NaN


def test_symmetric():
    g = unweighted_karate()
    rng = random.Random(0)
    for _ in range(50):
        a, b = random_solution(g, rng), random_solution(g, rng)
        assert NMI(a, b) == approx(NMI(b, a))


def test_random_solutions_match_reference():
    g = unweighted_karate()
    rng = random.Random(1)
    for _ in range(200):
        a, b = random_solution(g, rng), random_solution(g, rng)
        assert NMI(a, b) == approx(reference_nmi(reference_labels(a), reference_labels(b)))


# --- Growing graphs: A is the previous snapshot's solution, B the current one. ---

def test_longer_second_solution_is_compared_on_the_shared_nodes():
    # Previous snapshot: karate's first 20 nodes; current snapshot: all 34.
    g = unweighted_karate()
    rng = random.Random(2)
    for _ in range(50):
        a = [rng.choice([v for v in g[i] if v < 20] or [i]) for i in range(20)]
        b = random_solution(g, rng)
        expected = reference_nmi(reference_labels(a), reference_labels(b)[:20])
        assert NMI(a, b) == approx(expected)


def test_new_nodes_do_not_change_the_shared_partition():
    # Before: {0, 1} {2, 3}. After: same communities on nodes 0-3, new node 4 joins {2, 3}
    # and new node 5 is alone. Only nodes 0-3 are compared, and they are unchanged.
    # (Keeping the last four nodes instead would give about 0.34.)
    assert NMI(PAIRS, [1, 0, 3, 2, 2, 5]) == approx(1)


def test_new_node_can_merge_old_communities():
    # Before: {0}, {1}. After, both point at new node 2: {0, 1, 2}.
    # On the shared nodes that is {0}, {1} vs {0, 1}: a split vs a single community.
    assert NMI([0, 1], [2, 2, 2]) == approx(0)


def test_longer_first_solution_raises():
    # Never happens in the app: nodes are never removed, so later solutions are never shorter.
    with pytest.raises(ValueError):
        NMI(PAIRS + [4], PAIRS)
